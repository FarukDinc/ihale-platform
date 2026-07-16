-- ============================================================================
-- migration_uygun_firmalar_v3.sql (17 Tem 2026)
-- KULLANICI KURALI: "809K'lık gıda ihalesine sadece akaryakıt satmış firmayı
-- gösterme. Konusu eşleşen (en azından o konuda iş almış) VE geçmiş kazanımları
-- bu ihalenin bedeline ±%500 bandında (bedel/5 .. bedel*5) kalan firmaları getir.
-- Benzer ihalelerde de aynı bandı ŞART koş."
-- + EK KURAL (aynı gün): "Dayanak (konu çapası) HİÇ yoksa ne benzer ihale ne uygun
-- firma GÖSTERME — ileride otomatik firma-davet bu veriden beslenecek, alakasız
-- eşleşme spam üretir." → konu çapası (kanonik kategori / başlık konu-kelimesi /
-- embedding) bulunamazsa her iki RPC de BOŞ döner; jenerik doldurma yok.
--
-- Kök neden: bazı ilanların kategorisi kanonik 41'den değil ("Mal Alımı", "Diğer"
-- gibi jenerik kova) → kategori-eşleşmesi konu sinyali taşımıyor, listeye Petrol
-- Ofisi/Otokar gibi alakasız devler doluyordu.
--
-- v3 değişiklikleri:
--  1) ihaleye_uygun_firmalar: p_baslik parametresi — kategori kanonik değilse
--     (frontend NULL geçer) KONU eşleşmesi başlık kelimeleriyle yapılır
--     (tr_fold + stopword ayıklama). ÖLÇEK BANDI ŞART: p_bedel verilmişse yalnız
--     [p_bedel/p_bant, p_bedel*p_bant] içindeki kazanımlar sayılır (varsayılan
--     bant=5 → ±%500). Firma istatistikleri (max/ort/adet) bant-içi işlerden
--     hesaplanır → "bandın dışına çıkan" profil gösterilmez.
--     NOT: elimizde katılımcı verisi yok, yalnız KAZANAN var; "o konuda ihaleye
--     girmiş" şartı fiilen "o konuda ihale kazanmış" olarak uygulanır.
--  2) benzer_ihaleler (YENİ RPC): embedding (pgvector, varsa) + başlık trigram
--     benzerliği + kanonik kategori/il bonusu; ölçek bandı ŞART (aday ilanın
--     bedeli biliniyorsa bant dışıysa elenir; bedeli bilinmeyen aday -5 ceza ile
--     en alta iter). idare DÖNDÜRMEZ (anon maskesi delinmesin; üye frontend'te
--     ayrı sorguyla çeker).
--
-- Çalıştırma: docker exec -i supabase-db psql -U postgres -d postgres < backend/migration_uygun_firmalar_v3.sql
-- İdempotent: CREATE OR REPLACE + koşullu DROP.
-- ============================================================================

-- Eski imzaları düşür (overload karışıklığını önle)
DROP FUNCTION IF EXISTS public.ihaleye_uygun_firmalar(text, text, numeric, int);
DROP FUNCTION IF EXISTS public.ihaleye_uygun_firmalar(text, text, numeric, int, numeric);
DROP FUNCTION IF EXISTS public.ihaleye_uygun_firmalar(text, text, numeric, int, text, numeric);

-- Konu-kelimesi ayıklama: tr_fold'lanmış başlıktan anlamlı kelimeler.
-- Stopword listesi ihale-jargonu (fold'lanmış hâlleriyle) — "gida" gibi konu
-- kelimeleri kalır, "kisim/kalem/alimi" gibi dolgu kelimeler elenir.
CREATE OR REPLACE FUNCTION public.ihale_konu_kelimeleri(p_baslik text)
RETURNS TABLE (kelime text)
LANGUAGE sql IMMUTABLE PARALLEL SAFE
AS $$
  SELECT DISTINCT w
  FROM regexp_split_to_table(tr_fold(coalesce(p_baslik, '')), '[^a-z0-9]+') AS w
  WHERE length(w) >= 4
    AND w !~ '^[0-9]+$'
    AND w NOT IN (
      'kisim','kalem','adet','muhtelif','cesitli','cesit','grubu','grup','paket',
      'takim','mali','hizmet','hizmeti','alim','alimi','alimlari','alinmasi',
      'alinacak','alinacaktir','satin','yapim','yapimi','isleri','ihale','ihalesi',
      'madde','maddesi','mamul','temin','temini','ihtiyaci','ihtiyac','yillik',
      'aylik','gunluk','donem','donemi','donemlik','malzeme','malzemesi',
      'malzemeleri','dahil','birlikte','genel','kapsaminda','uzere','kullanilmak'
    );
$$;

GRANT EXECUTE ON FUNCTION public.ihale_konu_kelimeleri(text) TO anon, authenticated, service_role;

-- ── 1) Uygun firmalar v3 ────────────────────────────────────────────────────
CREATE OR REPLACE FUNCTION public.ihaleye_uygun_firmalar(
  p_kategori text,                 -- KANONİK kategori; jenerikse ("Mal Alımı"/"Diğer") frontend NULL geçer
  p_il       text    DEFAULT NULL,
  p_bedel    numeric DEFAULT NULL, -- yaklaşık maliyet; yoksa sözleşme bedeli (frontend fallback'ler)
  p_limit    int     DEFAULT 20,
  p_baslik   text    DEFAULT NULL, -- konu eşleşmesi için ihale başlığı
  p_bant     numeric DEFAULT 5     -- ölçek bandı çarpanı: ±%500 → [bedel/5, bedel*5]
)
RETURNS TABLE (
  kazanan_firma    text,
  yuklenici_id     uuid,
  firma_il         text,
  kategori_kazanim bigint,   -- konu+bant eşleşen kazanım sayısı
  max_kazanim      numeric,  -- bant-içi en büyük kazanım
  ort_kazanim      numeric,  -- bant-içi ortalama kazanım
  ayni_il          boolean,
  kapasite_uygun   boolean,  -- true = ölçek bandı ŞART olarak uygulandı (bedel biliniyor)
  skor             numeric
)
LANGUAGE sql STABLE
AS $$
  WITH ilgili AS (  -- KONU eşleşen ilanlar: kanonik kategori VEYA başlık kelimesi
    -- DAYANAK YOKSA BOŞ DÖNER (kullanıcı kuralı, 17 Tem): kategori jenerik + başlıktan
    -- konu kelimesi çıkmadıysa ALAKASIZ firma göstermek yerine hiç göstermiyoruz —
    -- ileride otomatik firma-davet bu listeden beslenecek, yanlış pozitif = spam.
    SELECT i.id, i.il
    FROM public.ilanlar i
    WHERE (p_kategori IS NOT NULL AND i.kategori = p_kategori)
       OR (p_kategori IS NULL AND EXISTS (
             SELECT 1 FROM public.ihale_konu_kelimeleri(p_baslik) t
             WHERE tr_fold(i.baslik) LIKE '%' || t.kelime || '%'))
  )
  SELECT
    s.kazanan_firma,
    (array_agg(s.yuklenici_id) FILTER (WHERE s.yuklenici_id IS NOT NULL))[1] AS yuklenici_id,
    mode() WITHIN GROUP (ORDER BY i.il)                        AS firma_il,
    count(*)                                                   AS kategori_kazanim,
    max(COALESCE(s.kazanan_teklif, s.sozlesme_bedeli))         AS max_kazanim,
    round(avg(COALESCE(s.kazanan_teklif, s.sozlesme_bedeli)))  AS ort_kazanim,
    bool_or(i.il = p_il)                                       AS ayni_il,
    (p_bedel IS NOT NULL AND p_bedel > 0)                      AS kapasite_uygun,
    (
      LEAST(count(*), 20)::numeric                                   -- deneyim (üst sınır 20)
      + (CASE WHEN bool_or(i.il = p_il) THEN 10 ELSE 0 END)          -- aynı ilde iş almış
      -- ölçek yakınlığı (0-8): ort kazanım bedele log-ölçekte ne kadar yakınsa o kadar puan
      + (CASE WHEN p_bedel IS NULL OR p_bedel <= 0 THEN 0
              ELSE round(8 * (1 - LEAST(
                     abs(ln(GREATEST(avg(COALESCE(s.kazanan_teklif, s.sozlesme_bedeli)), 1) / p_bedel))
                     / ln(p_bant), 1))::numeric, 1) END)
    )                                                          AS skor
  FROM public.ihale_sonuclari s
  JOIN ilgili i ON i.id = s.ilan_id
  WHERE s.kazanan_firma IS NOT NULL
    AND s.kazanan_firma <> ''
    -- ÖLÇEK BANDI ŞART: bedel biliniyorsa yalnız bant-içi kazanımlar sayılır
    -- (tutarı NULL olan sonuç satırları da BETWEEN'de elenir)
    AND (p_bedel IS NULL OR p_bedel <= 0
         OR COALESCE(s.kazanan_teklif, s.sozlesme_bedeli)
            BETWEEN p_bedel / p_bant AND p_bedel * p_bant)
  GROUP BY s.kazanan_firma   -- ünvan bazlı tekilleştirme (aynı firma farklı yuklenici_id ile çiftlenmesin)
  ORDER BY skor DESC, max_kazanim DESC NULLS LAST
  LIMIT p_limit;
$$;

-- DİKKAT (anon maskesi, migration_anon_maske.sql): kazanan_firma anon'a KAPALI,
-- bu RPC anon'dan bilerek REVOKE edilmişti — kilit KORUNUR (fonksiyon PUBLIC
-- EXECUTE ile doğduğundan açık REVOKE şart).
REVOKE EXECUTE ON FUNCTION public.ihaleye_uygun_firmalar(text, text, numeric, int, text, numeric) FROM PUBLIC, anon;
GRANT EXECUTE ON FUNCTION public.ihaleye_uygun_firmalar(text, text, numeric, int, text, numeric) TO authenticated, service_role;

-- ── 2) Benzer ihaleler (yeni RPC) ───────────────────────────────────────────
DROP FUNCTION IF EXISTS public.benzer_ihaleler(uuid, text, numeric, int, numeric);

CREATE OR REPLACE FUNCTION public.benzer_ihaleler(
  p_id       uuid,
  p_kategori text    DEFAULT NULL, -- KANONİK kategori (jenerikse NULL)
  p_bedel    numeric DEFAULT NULL, -- kaynak ihalenin efektif bedeli (yaklaşık maliyet / sözleşme bedeli)
  p_limit    int     DEFAULT 4,
  p_bant     numeric DEFAULT 5
)
RETURNS TABLE (
  id                   uuid,
  baslik               text,
  il                   text,
  yaklasik_maliyet_min numeric,
  yaklasik_maliyet_max numeric,
  tahmini_bedel        numeric,
  son_teklif_tarihi    timestamptz,
  kategori             text,
  benzerlik            numeric
)
LANGUAGE sql STABLE
AS $$
  WITH src AS (
    SELECT i.baslik, i.il, i.embedding
    FROM public.ilanlar i
    WHERE i.id = p_id
  ),
  aday AS (
    SELECT
      i.id            AS a_id,
      i.baslik        AS a_baslik,
      i.il            AS a_il,
      i.yaklasik_maliyet_min::numeric AS a_min,
      i.yaklasik_maliyet_max::numeric AS a_max,
      i.tahmini_bedel::numeric AS a_tahmini,
      i.son_teklif_tarihi::timestamptz AS a_son,
      i.kategori      AS a_kategori,
      i.embedding     AS a_emb,
      COALESCE(NULLIF(i.yaklasik_maliyet_max, 0), NULLIF(i.yaklasik_maliyet_min, 0),
               NULLIF(i.tahmini_bedel, 0))              AS a_bedel,
      s.baslik        AS s_baslik,
      s.il            AS s_il,
      s.embedding     AS s_emb
    FROM public.ilanlar i
    CROSS JOIN src s
    WHERE i.durum = 'aktif'
      AND i.id <> p_id
      -- KONU eşleşmesi ŞART: kanonik kategori VEYA başlık kelimesi VEYA semantik
      -- yakınlık. Üçü de yoksa sonuç BOŞ döner (dayanak yoksa gösterme kuralı) —
      -- jenerik kategori/tür doldurması YOK.
      AND ( (p_kategori IS NOT NULL AND i.kategori = p_kategori)
         OR EXISTS (SELECT 1 FROM public.ihale_konu_kelimeleri(s.baslik) t
                    WHERE tr_fold(i.baslik) LIKE '%' || t.kelime || '%')
         OR (s.embedding IS NOT NULL AND i.embedding IS NOT NULL
             AND (i.embedding <=> s.embedding) < 0.45) )
      -- ÖLÇEK BANDI ŞART: aday bedeli biliniyorsa bant dışıysa ELENİR
      AND (p_bedel IS NULL OR p_bedel <= 0
           OR COALESCE(NULLIF(i.yaklasik_maliyet_max, 0), NULLIF(i.yaklasik_maliyet_min, 0),
                       NULLIF(i.tahmini_bedel, 0)) IS NULL
           OR COALESCE(NULLIF(i.yaklasik_maliyet_max, 0), NULLIF(i.yaklasik_maliyet_min, 0),
                       NULLIF(i.tahmini_bedel, 0))
              BETWEEN p_bedel / p_bant AND p_bedel * p_bant)
  )
  SELECT
    a.a_id, a.a_baslik, a.a_il, a.a_min, a.a_max, a.a_tahmini, a.a_son, a.a_kategori,
    round((
      -- konu benzerliği (0-60): embedding varsa cosine, yoksa başlık trigram
      (CASE WHEN a.s_emb IS NOT NULL AND a.a_emb IS NOT NULL
            THEN (1 - (a.a_emb <=> a.s_emb)) * 60
            ELSE similarity(tr_fold(a.a_baslik), tr_fold(a.s_baslik)) * 60 END)
      + (CASE WHEN p_kategori IS NOT NULL AND a.a_kategori = p_kategori THEN 15 ELSE 0 END)
      + (CASE WHEN a.a_il = a.s_il THEN 8 ELSE 0 END)
      -- ölçek yakınlığı (0-10); bedeli bilinmeyen aday -5 (bant garanti edilemedi)
      + (CASE WHEN p_bedel IS NULL OR p_bedel <= 0 THEN 0
              WHEN a.a_bedel IS NULL THEN -5
              ELSE 10 * (1 - LEAST(abs(ln(GREATEST(a.a_bedel, 1) / p_bedel)) / ln(p_bant), 1)) END)
    )::numeric, 1) AS benzerlik
  FROM aday a
  ORDER BY benzerlik DESC
  LIMIT p_limit;
$$;

-- benzer_ihaleler anon'a AÇIK kalabilir: yalnız anon-izinli kolonlar döner
-- (baslik/il/maliyet/tarih/kategori — idare ve kazanan YOK), invoker-rights
-- olduğundan maskeli kolona dokunsa zaten hata alırdı.
GRANT EXECUTE ON FUNCTION public.benzer_ihaleler(uuid, text, numeric, int, numeric) TO anon, authenticated, service_role;

NOTIFY pgrst, 'reload schema';

-- Doğrulama (elle):
--   SELECT * FROM ihale_konu_kelimeleri('10 KISIM 13 KALEM GIDA MADDESİ');      -- -> 'gida'
--   SELECT kazanan_firma, kategori_kazanim, max_kazanim, ort_kazanim, skor
--     FROM ihaleye_uygun_firmalar(NULL, 'ANKARA', 809000, 8, '10 KISIM 13 KALEM GIDA MADDESİ');
--     -- Petrol Ofisi / Otokar GÖRÜNMEMELİ; gıda konulu, 162K-4M bandında iş almış firmalar gelmeli
--   SELECT baslik, il, benzerlik FROM benzer_ihaleler('5a450f6d-92ff-4d16-ba56-6fcddbb355c3', NULL, 809000, 4);
