-- ============================================================================
-- migration_idf_eslestirme.sql (17 Tem 2026) — Katman 2: IDF-ağırlıklı başlık eşleşmesi
--
-- SORUN: benzer_ihaleler + ihaleye_uygun_firmalar başlık eşleşmesinde her kelime EŞİT
-- ağırlıklı. "malzeme/sistem/bakim" gibi jenerik kelimeyi paylaşmak, "endoskopi/
-- hemodiyaliz/transformatör" gibi ayırt edici kelimeyi paylaşmakla aynı sayılıyor.
-- Dahası benzer_ihaleler'in embeddingsiz dalı KARAKTER-bazlı ham trigram similarity()
-- kullanıyor → "2024", "2 KISIM" gibi ortak karakter dizileriyle yanlış eşleşiyor.
--
-- ÇÖZÜM (klasik IDF / nadirlik ağırlığı): her başlık-kelimesine, tüm ilan başlıklarındaki
-- SEYREKLİĞİNE göre ağırlık ver — idf = ln(N / (1+df)). Nadir kelime yüksek, jenerik düşük.
-- Eşleşme skoru = paylaşılan kelimelerin idf TOPLAMI. Böylece "endoskopi"yi paylaşmak
-- güçlü, "sistem"i paylaşmak zayıf sinyal olur.
--
-- Katman 1 (jenerik→kanonik backfill) kategori sinyalini iyileştirdi; bu katman
-- kategori YOKKEN/jenerikken ve benzer-ihalede konu yakınlığını keskinleştirir.
--
-- Çalıştır: docker exec -i supabase-db psql -U postgres -d postgres < backend/migration_idf_eslestirme.sql
-- Gece tazeleme: run_scraper.sh'a REFRESH eklendi (yeni ilanlarla df değişir).
-- Idempotent: IF NOT EXISTS / CREATE OR REPLACE.
-- İNCELEME NOTU (17 Tem, 4-lens çekişmeli): tüm migration BEGIN/COMMIT içinde —
-- fonksiyon CREATE'i hata verirse ROLLBACK olur, canlı fonksiyon SİLİNMİŞ kalmaz
-- (benzer_ihaleler misafir ihale-detay'da canlı; DROP+başarısız-CREATE riski kapandı,
-- ayrıca DROP tümden kaldırıldı — imza aynı, CREATE OR REPLACE yeterli).
-- ============================================================================

BEGIN;

-- ── 0) ihale_konu_kelimeleri gövdesinde tr_fold → public.tr_fold ────────────
-- KRİTİK: SQL fonksiyonu MATERIALIZED VIEW'e INLINE edilince, gövdesindeki
-- ŞEMASIZ referanslar çözülemez ("function tr_fold(text) does not exist"
-- during inlining — canlıda doğrulandı). Şema-nitelikli public.tr_fold ile MV
-- kurulur. Davranış aynı; RPC çağrıları etkilenmez.
CREATE OR REPLACE FUNCTION public.ihale_konu_kelimeleri(p_baslik text)
RETURNS TABLE (kelime text)
LANGUAGE sql IMMUTABLE PARALLEL SAFE
AS $$
  SELECT DISTINCT w
  FROM regexp_split_to_table(public.tr_fold(coalesce(p_baslik, '')), '[^a-z0-9]+') AS w
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

-- ── 1) Kelime→IDF materialized view (tüm başlıklardan) ──────────────────────
-- ihale_konu_kelimeleri IMMUTABLE PARALLEL SAFE → LATERAL çıkarım paralelleşir.
-- df>=2: tek kez geçen kelime (yazım hatası/tekil) gürültü, atılır.
-- NOT (17 Tem, canlı ölçüm): 34.236 kelime çıktı, dağılım SIKIŞIK (bakim=3.01,
-- gida=3.85, sistem=5.83, endoskopi=8.30). idf>=3.0 eşiği ~%99,98'ini tutar →
-- HARD EŞİK değil, IDF-ağırlıklı TOPLAM asıl mekanizma (nadir kelime skoru domine eder).
CREATE MATERIALIZED VIEW IF NOT EXISTS public.ihale_kelime_idf AS
WITH kelimeler AS (
  SELECT i.id, k.kelime
  FROM public.ilanlar i
  CROSS JOIN LATERAL public.ihale_konu_kelimeleri(i.baslik) k
  WHERE i.baslik IS NOT NULL
),
df AS (
  SELECT kelime, count(DISTINCT id)::bigint AS df
  FROM kelimeler GROUP BY kelime
),
toplam AS (SELECT count(*)::numeric AS n FROM public.ilanlar WHERE baslik IS NOT NULL)
SELECT d.kelime,
       d.df,
       round(ln((SELECT n FROM toplam) / (1 + d.df)), 3) AS idf
FROM df d
WHERE d.df >= 2;

CREATE UNIQUE INDEX IF NOT EXISTS idx_ihale_kelime_idf_kelime
  ON public.ihale_kelime_idf (kelime);
ANALYZE public.ihale_kelime_idf;
GRANT SELECT ON public.ihale_kelime_idf TO anon, authenticated, service_role;

-- ── 2) Başlık → (kelime, idf) — MV'de yoksa nadir varsay (yüksek idf 6.0) ────
CREATE OR REPLACE FUNCTION public.ihale_konu_kelimeleri_idf(p_baslik text)
RETURNS TABLE (kelime text, idf numeric)
LANGUAGE sql STABLE PARALLEL SAFE
AS $$
  SELECT k.kelime, COALESCE(m.idf, 6.0)::numeric
  FROM public.ihale_konu_kelimeleri(p_baslik) k
  LEFT JOIN public.ihale_kelime_idf m ON m.kelime = k.kelime
$$;
GRANT EXECUTE ON FUNCTION public.ihale_konu_kelimeleri_idf(text) TO anon, authenticated, service_role;

-- Ayırt edicilik eşiği: idf >= 3.0 ≈ kelime başlıkların ~%5'inden azında geçiyor.
-- Bu eşiğin üstündeki kelimeler "belirleyici" sayılır; yalnız jenerik kelime paylaşan
-- aday ELENİR (dayanak yoksa gösterme kuralı — konu vaguesa yüksek-hassas kal).

-- ── 3) benzer_ihaleler: konu skoru IDF-ağırlıklı örtüşme (embedding öncelikli) ─
-- İMZA/return DEĞİŞMEDİ → DROP YOK (kaldırıldı: başarısız CREATE'te fonksiyonun
-- silinip kalma riskini komple ortadan kaldırır). CREATE OR REPLACE yeterli.
CREATE OR REPLACE FUNCTION public.benzer_ihaleler(
  p_id       uuid,
  p_kategori text    DEFAULT NULL,
  p_bedel    numeric DEFAULT NULL,
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
    SELECT i.baslik, i.il, i.embedding FROM public.ilanlar i WHERE i.id = p_id
  ),
  -- Kaynak başlığının BELİRLEYİCİ kelimeleri (idf>=3) + toplam idf ağırlığı
  src_kw AS (
    SELECT kelime, idf FROM public.ihale_konu_kelimeleri_idf((SELECT baslik FROM src))
    WHERE idf >= 3.0
  ),
  src_kw_toplam AS (SELECT COALESCE(sum(idf), 0) AS w FROM src_kw),
  aday AS (
    SELECT
      i.id, i.baslik, i.il,
      i.yaklasik_maliyet_min::numeric AS a_min,
      i.yaklasik_maliyet_max::numeric AS a_max,
      i.tahmini_bedel::numeric AS a_tahmini,
      i.son_teklif_tarihi::timestamptz AS a_son,
      i.kategori AS a_kategori,
      i.embedding AS a_emb,
      (SELECT embedding FROM src) AS s_emb,
      (SELECT il FROM src) AS s_il,
      COALESCE(NULLIF(i.yaklasik_maliyet_max,0), NULLIF(i.yaklasik_maliyet_min,0),
               NULLIF(i.tahmini_bedel,0)) AS a_bedel,
      -- Paylaşılan BELİRLEYİCİ kelimelerin idf toplamı (konu örtüşme sinyali).
      -- KELİME-SINIRI eşleşmesi (\m..\M): idf df'i TAM-token'dan hesaplandığından
      -- eşleşme de tam-kelime olmalı — aksi halde kısa nadir token ("kars") sık uzun
      -- kelimenin ("karsilanmasi") içinde alt-dize olarak yakalanıp yüksek idf'i
      -- yanlış adaya bindirir (inceleme bulgusu). LIKE indeks ön-filtresi, ~ kesinleştirir.
      (SELECT COALESCE(sum(sk.idf), 0)
         FROM src_kw sk
        WHERE tr_fold(i.baslik) LIKE '%' || sk.kelime || '%'
          AND tr_fold(i.baslik) ~ ('\m' || sk.kelime || '\M')) AS ortak_idf
    FROM public.ilanlar i
    WHERE i.durum = 'aktif'
      AND i.id <> p_id
      AND i.son_teklif_tarihi >= now()          -- SÜRESİ GEÇMİŞİ GÖSTERME (v3.1 açık tespiti)
      -- KONU ŞART: kanonik kategori EŞİT, VEYA en az bir belirleyici kelime paylaş,
      -- VEYA semantik yakın (embedding). Üçü de yoksa BOŞ (dayanak yoksa gösterme).
      AND ( (p_kategori IS NOT NULL AND i.kategori = p_kategori)
         OR EXISTS (SELECT 1 FROM src_kw sk WHERE tr_fold(i.baslik) LIKE '%' || sk.kelime || '%'
                                              AND tr_fold(i.baslik) ~ ('\m' || sk.kelime || '\M'))
         OR ((SELECT embedding FROM src) IS NOT NULL AND i.embedding IS NOT NULL
             AND (i.embedding <=> (SELECT embedding FROM src)) < 0.45) )
      -- ÖLÇEK BANDI ŞART
      AND (p_bedel IS NULL OR p_bedel <= 0
           OR COALESCE(NULLIF(i.yaklasik_maliyet_max,0), NULLIF(i.yaklasik_maliyet_min,0),
                       NULLIF(i.tahmini_bedel,0)) IS NULL
           OR COALESCE(NULLIF(i.yaklasik_maliyet_max,0), NULLIF(i.yaklasik_maliyet_min,0),
                       NULLIF(i.tahmini_bedel,0)) BETWEEN p_bedel / p_bant AND p_bedel * p_bant)
  )
  SELECT
    a.id, a.baslik, a.il, a.a_min, a.a_max, a.a_tahmini, a.a_son, a.a_kategori,
    round((
      -- KONU (0-60): embedding varsa cosine; yoksa IDF-örtüşme oranı (ham trigram DEĞİL)
      (CASE
         WHEN a.s_emb IS NOT NULL AND a.a_emb IS NOT NULL
           THEN (1 - (a.a_emb <=> a.s_emb)) * 60
         WHEN (SELECT w FROM src_kw_toplam) > 0
           THEN LEAST(a.ortak_idf / (SELECT w FROM src_kw_toplam), 1) * 60
         ELSE 0 END)
      + (CASE WHEN p_kategori IS NOT NULL AND a.a_kategori = p_kategori THEN 15 ELSE 0 END)
      + (CASE WHEN a.il = a.s_il THEN 8 ELSE 0 END)     -- FIX: aday'da kolon 'il' (a_il ölü referanstı)
      + (CASE WHEN p_bedel IS NULL OR p_bedel <= 0 THEN 0
              WHEN a.a_bedel IS NULL THEN -5
              -- ln(p_bant) paydası: p_bant<=1'de ln≤0 → sıfıra bölme; GREATEST ile korunur (inceleme)
              ELSE 10 * (1 - LEAST(abs(ln(GREATEST(a.a_bedel,1) / p_bedel)) / GREATEST(ln(p_bant), 0.0001), 1)) END)
    )::numeric, 1) AS benzerlik
  FROM aday a
  ORDER BY benzerlik DESC
  LIMIT p_limit;
$$;
GRANT EXECUTE ON FUNCTION public.benzer_ihaleler(uuid, text, numeric, int, numeric) TO anon, authenticated, service_role;

-- ── 4) ihaleye_uygun_firmalar: başlık dalını IDF-relevans ile skorla ────────
-- Kategori dalı DEĞİŞMEDİ (kategori zaten güçlü çapa). Başlık dalı: belirleyici
-- kelime paylaşan sonuçları çeker, firmayı paylaşılan idf TOPLAMIYLA öne çıkarır.
CREATE OR REPLACE FUNCTION public.ihaleye_uygun_firmalar(
  p_kategori text,
  p_il       text    DEFAULT NULL,
  p_bedel    numeric DEFAULT NULL,
  p_limit    int     DEFAULT 20,
  p_baslik   text    DEFAULT NULL,
  p_bant     numeric DEFAULT 5
)
RETURNS TABLE (
  kazanan_firma    text,
  yuklenici_id     uuid,
  firma_il         text,
  kategori_kazanim bigint,
  max_kazanim      numeric,
  ort_kazanim      numeric,
  ayni_il          boolean,
  kapasite_uygun   boolean,
  skor             numeric
)
LANGUAGE plpgsql STABLE
AS $fn$
BEGIN
  IF p_kategori IS NULL AND (p_baslik IS NULL OR p_baslik = '') THEN
    RETURN;
  END IF;

  IF p_kategori IS NOT NULL THEN
    -- Kategori dalı (v3.3 ile aynı)
    RETURN QUERY
    SELECT
      s.kazanan_firma,
      (array_agg(s.yuklenici_id) FILTER (WHERE s.yuklenici_id IS NOT NULL))[1],
      mode() WITHIN GROUP (ORDER BY i.il),
      count(*),
      max(COALESCE(s.kazanan_teklif, s.sozlesme_bedeli))::numeric,
      round(avg(COALESCE(s.kazanan_teklif, s.sozlesme_bedeli)))::numeric,
      bool_or(i.il = p_il),
      (p_bedel IS NOT NULL AND p_bedel > 0),
      (
        LEAST(count(*), 20)::numeric
        + (CASE WHEN bool_or(i.il = p_il) THEN 10 ELSE 0 END)
        + (CASE WHEN p_bedel IS NULL OR p_bedel <= 0 THEN 0
                ELSE round(8 * (1 - LEAST(
                       abs(ln(GREATEST(avg(COALESCE(s.kazanan_teklif, s.sozlesme_bedeli)), 1) / p_bedel))
                       / GREATEST(ln(p_bant), 0.0001), 1))::numeric, 1) END)
      )::numeric
    FROM public.ihale_sonuclari s
    JOIN public.ilanlar i ON i.id = s.ilan_id AND i.kategori = p_kategori
    WHERE s.kazanan_firma IS NOT NULL AND s.kazanan_firma <> ''
      AND (p_bedel IS NULL OR p_bedel <= 0
           OR COALESCE(s.kazanan_teklif, s.sozlesme_bedeli) BETWEEN p_bedel / p_bant AND p_bedel * p_bant)
    GROUP BY s.kazanan_firma
    ORDER BY 9 DESC, 5 DESC NULLS LAST
    LIMIT p_limit;
  ELSE
    -- Başlık dalı: IDF-relevans. Belirleyici (idf>=3) kelime paylaşan sonuç ilanları;
    -- firma skoru deneyim + paylaşılan idf toplamı + il + ölçek.
    RETURN QUERY
    WITH src_kw AS (
      SELECT kelime, idf FROM public.ihale_konu_kelimeleri_idf(p_baslik) WHERE idf >= 3.0
    ),
    -- KRİTİK (inceleme): sürüş kelime kümesinden (küçük) → ilanlar'a; her kelime için
    -- idx_ilanlar_baslik_fold_trgm bitmap scan devrede (v3.2'de düzeltilen 10sn'lik ters
    -- planı geri getirmez). GROUP BY i2.id → ilan başına TEK satır + paylaşılan idf toplamı
    -- (rel). Word-boundary ~ ile alt-dize yanlış-pozitifi elenir. src_kw boşsa (başlıkta
    -- belirleyici kelime yok) ilgili BOŞ → başlık dalı boş döner (dayanak yoksa gösterme).
    ilgili AS MATERIALIZED (
      SELECT i2.id, min(i2.il) AS il, sum(sk.idf) AS rel
      FROM src_kw sk
      JOIN public.ilanlar i2
        ON tr_fold(i2.baslik) LIKE '%' || sk.kelime || '%'
       AND tr_fold(i2.baslik) ~ ('\m' || sk.kelime || '\M')
      GROUP BY i2.id
    )
    SELECT
      s.kazanan_firma,
      (array_agg(s.yuklenici_id) FILTER (WHERE s.yuklenici_id IS NOT NULL))[1],
      mode() WITHIN GROUP (ORDER BY i.il),
      count(*),
      max(COALESCE(s.kazanan_teklif, s.sozlesme_bedeli))::numeric,
      round(avg(COALESCE(s.kazanan_teklif, s.sozlesme_bedeli)))::numeric,
      bool_or(i.il = p_il),
      (p_bedel IS NOT NULL AND p_bedel > 0),
      (
        LEAST(count(*), 20)::numeric
        -- IDF relevans (üst sınır 30). NOT: çok-lotlu ilan sonuç satırlarını çoğalttığından
        -- rel hafif şişebilir (inceleme, düşük önem) ama LEAST(,30) tavanlıyor; ilan-tekil
        -- relevans için sum yerine max(i.rel) alınmadı çünkü çok farklı ilan kazanan gerçek
        -- uzman öne çıkmalı — tavan bu iki uçu dengeler.
        + LEAST(sum(i.rel), 30)::numeric
        + (CASE WHEN bool_or(i.il = p_il) THEN 10 ELSE 0 END)
        + (CASE WHEN p_bedel IS NULL OR p_bedel <= 0 THEN 0
                ELSE round(8 * (1 - LEAST(
                       abs(ln(GREATEST(avg(COALESCE(s.kazanan_teklif, s.sozlesme_bedeli)), 1) / p_bedel))
                       / GREATEST(ln(p_bant), 0.0001), 1))::numeric, 1) END)
      )::numeric
    FROM public.ihale_sonuclari s
    JOIN ilgili i ON i.id = s.ilan_id
    WHERE s.kazanan_firma IS NOT NULL AND s.kazanan_firma <> ''
      AND (p_bedel IS NULL OR p_bedel <= 0
           OR COALESCE(s.kazanan_teklif, s.sozlesme_bedeli) BETWEEN p_bedel / p_bant AND p_bedel * p_bant)
    GROUP BY s.kazanan_firma
    ORDER BY 9 DESC, 5 DESC NULLS LAST
    LIMIT p_limit;
  END IF;
END
$fn$;

-- Anon kilidi KORUNMALI (kazanan_firma maskesi) — CREATE OR REPLACE grant'ı sıfırlamaz
-- ama imza aynı olduğundan garantiye al:
REVOKE EXECUTE ON FUNCTION public.ihaleye_uygun_firmalar(text, text, numeric, int, text, numeric) FROM PUBLIC, anon;
GRANT EXECUTE ON FUNCTION public.ihaleye_uygun_firmalar(text, text, numeric, int, text, numeric) TO authenticated, service_role;

COMMIT;

NOTIFY pgrst, 'reload schema';

-- Doğrulama (elle):
--   SELECT count(*) FROM ihale_kelime_idf;                                  -- ~on binlerce kelime
--   SELECT kelime, df, idf FROM ihale_kelime_idf ORDER BY idf DESC LIMIT 5; -- en nadir (yüksek idf)
--   SELECT kelime, df, idf FROM ihale_kelime_idf ORDER BY df DESC LIMIT 5;  -- en jenerik (düşük idf)
--   SELECT * FROM ihale_konu_kelimeleri_idf('10 KISIM 13 KALEM GIDA MADDESİ');
