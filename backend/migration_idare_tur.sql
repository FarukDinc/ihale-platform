-- ============================================================================
-- migration_idare_tur.sql — İDARE TÜRÜ sınıflandırması: şema + boşluk alarmı
--                                                                (18 Tem 2026)
-- Kullanıcı hedefi: "kurumları EKAP'taki gibi kategorize et" → ihalelerde
--   "sadece belediyeler / sadece hastaneler" gibi filtreleme.
--
-- MİMARİ KARARI (kullanıcı itirazıyla şekillendi):
--   Tek seferlik DETSİS dump'ı BAYATLAR (yeni birim açılır, ad değişir) ve
--   DETSİS adlarını EKAP adlarına bulanık eşleştirmek gerekir. Bu yüzden:
--   (a) Kaynak = EKAP'ın DETSİS-türevli idare listesi → adlar `ilanlar.idare`
--       ile BİREBİR aynı string (bulanık eşleştirme YOK), gece tazelenir.
--   (b) Boşluk dedektörü: ihalede görünüp eşlemede olmayan idareler raporlanır
--       (yeni açılan birimler buraya düşer) → idare_tur_bosluk().
--   (c) Boşluk asla "sınıfsız" kalmaz: kural/AI ile GEÇİCİ sınıflanır, `kaynak`
--       alanı bunu işaretler; resmî tazeleme gelince otoriter değerle ezilir.
--
-- Çalıştırma:
--   docker exec -i supabase-db psql -U postgres -d postgres < backend/migration_idare_tur.sql
-- Idempotent.
-- ============================================================================

-- ── 1) Normalize: idare adı → eşleme anahtarı ───────────────────────────────
-- tr_fold (mevcut, IMMUTABLE) üzerine: noktalama sadeleştirme + çoklu boşluk tekleme.
-- IMMUTABLE olmak ZORUNDA — ifade indeksi bunun üzerine kurulacak
-- (bkz. statement-timeout dersi: satır-başı fonksiyon filtresi indekssiz ölür).
CREATE OR REPLACE FUNCTION public.idare_normalize(s text)
  RETURNS text
  LANGUAGE sql
  IMMUTABLE
  PARALLEL SAFE
AS $$
  SELECT btrim(regexp_replace(
           regexp_replace(public.tr_fold(coalesce(s, '')), '[^a-z0-9]+', ' ', 'g'),
           '\s+', ' ', 'g'));
$$;

-- ── 2) Eşleme tablosu ───────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.idare_tur (
  idare_norm   text PRIMARY KEY,              -- idare_normalize(idare) — join anahtarı
  idare_ad     text NOT NULL,                 -- EKAP'taki görünen ad
  tur          text NOT NULL,                 -- buyuksehir_belediye | belediye | saglik | ...
  ust_kurum    text,                          -- DETSİS hiyerarşisinden üst kurum adı
  detsis_no    text,                          -- resmî DETSİS numarası (varsa)
  kaynak       text NOT NULL DEFAULT 'kural', -- 'ekap-detsis'=kesin | 'kural' | 'ai'  (geçici)
  guven        smallint NOT NULL DEFAULT 50,  -- 0-100
  guncelleme   timestamptz NOT NULL DEFAULT now(),
  CONSTRAINT idare_tur_kaynak_chk CHECK (kaynak IN ('ekap-detsis','kural','ai','elle'))
);

CREATE INDEX IF NOT EXISTS idx_idare_tur_tur    ON public.idare_tur (tur);
CREATE INDEX IF NOT EXISTS idx_idare_tur_kaynak ON public.idare_tur (kaynak);

COMMENT ON TABLE  public.idare_tur IS
  'İdare adı → tür eşlemesi. kaynak=ekap-detsis OTORİTER; kural/ai GEÇİCİ (tazelemede ezilir).';
COMMENT ON COLUMN public.idare_tur.kaynak IS
  'ekap-detsis: EKAP/DETSİS hiyerarşisinden kesin | kural: ad kalıbından | ai: model çıkarımı | elle: manuel düzeltme';

-- ── 3) İFADE İNDEKSİ (kritik) ───────────────────────────────────────────────
-- ilanlar.idare üzerinde normalize'lı join/filtre yapılacak. İndeks olmadan
-- 350K+ satırda satır-başı fonksiyon çağrısı → statement timeout.
CREATE INDEX IF NOT EXISTS idx_ilanlar_idare_norm
  ON public.ilanlar (public.idare_normalize(idare));

-- ── 4) (b) BOŞLUK DEDEKTÖRÜ ─────────────────────────────────────────────────
-- İhalelerde görünüp eşlemede KARŞILIĞI OLMAYAN idareler (yeni açılan birimler).
-- jsonb döner → 1000 satır tavanına takılmaz (kırpılma dersi).
CREATE OR REPLACE FUNCTION public.idare_tur_bosluk(p_limit int DEFAULT 500)
  RETURNS jsonb
  LANGUAGE sql
  STABLE
AS $$
  WITH eksik AS (
    SELECT i.idare,
           public.idare_normalize(i.idare) AS idare_norm,
           count(*)      AS ihale_sayisi,
           max(i.ilan_tarihi) AS son_ilan
    FROM public.ilanlar i
    LEFT JOIN public.idare_tur t
           ON t.idare_norm = public.idare_normalize(i.idare)
    WHERE i.idare IS NOT NULL AND i.idare <> '' AND t.idare_norm IS NULL
    GROUP BY i.idare
    ORDER BY count(*) DESC
    LIMIT p_limit
  )
  SELECT jsonb_build_object(
    'eksik_idare_sayisi', (SELECT count(*) FROM eksik),
    'eksik_ihale_sayisi', (SELECT coalesce(sum(ihale_sayisi), 0) FROM eksik),
    'liste',              coalesce((SELECT jsonb_agg(to_jsonb(eksik)) FROM eksik), '[]'::jsonb)
  );
$$;

-- ── 5) Kapsama raporu (sağlık göstergesi) ───────────────────────────────────
-- Kaç ihale sınıflanmış, hangi kaynakla, tür dağılımı ne?
CREATE OR REPLACE FUNCTION public.idare_tur_kapsama()
  RETURNS jsonb
  LANGUAGE sql
  STABLE
AS $$
  WITH j AS (
    SELECT t.tur, t.kaynak
    FROM public.ilanlar i
    LEFT JOIN public.idare_tur t ON t.idare_norm = public.idare_normalize(i.idare)
    WHERE i.idare IS NOT NULL AND i.idare <> ''
  )
  SELECT jsonb_build_object(
    'toplam_ihale',       (SELECT count(*) FROM j),
    'siniflanmis',        (SELECT count(*) FROM j WHERE tur IS NOT NULL),
    'kapsama_yuzde',      (SELECT round(100.0 * count(*) FILTER (WHERE tur IS NOT NULL) / nullif(count(*),0), 1) FROM j),
    'kaynak_dagilimi',    (SELECT coalesce(jsonb_object_agg(coalesce(kaynak,'yok'), n), '{}'::jsonb)
                             FROM (SELECT kaynak, count(*) n FROM j GROUP BY kaynak) x),
    'tur_dagilimi',       (SELECT coalesce(jsonb_object_agg(coalesce(tur,'yok'), n), '{}'::jsonb)
                             FROM (SELECT tur, count(*) n FROM j GROUP BY tur) y)
  );
$$;

-- ── 6) Tür bazlı idare listesi (arayüz filtresi için) ───────────────────────
CREATE OR REPLACE FUNCTION public.idare_tur_liste(p_tur text DEFAULT NULL)
  RETURNS jsonb
  LANGUAGE sql
  STABLE
AS $$
  SELECT coalesce(jsonb_agg(to_jsonb(t) ORDER BY t.idare_ad), '[]'::jsonb)
  FROM (
    SELECT idare_ad, tur, ust_kurum, kaynak
    FROM public.idare_tur
    WHERE p_tur IS NULL OR tur = p_tur
  ) t;
$$;

-- ── Yetkiler ────────────────────────────────────────────────────────────────
-- Tür dağılımı/kapsama istatistiktir (vitrin) → anon görebilir.
-- Boşluk raporu operasyoneldir → yalnız service_role.
GRANT EXECUTE ON FUNCTION public.idare_tur_kapsama()        TO anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.idare_tur_liste(text)      TO authenticated, service_role;
REVOKE EXECUTE ON FUNCTION public.idare_tur_bosluk(int)     FROM PUBLIC;
REVOKE EXECUTE ON FUNCTION public.idare_tur_bosluk(int)     FROM anon;
GRANT  EXECUTE ON FUNCTION public.idare_tur_bosluk(int)     TO service_role;

-- Tablo: okuma girişli kullanıcıya, yazma yalnız service_role (scraper).
ALTER TABLE public.idare_tur ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS idare_tur_oku ON public.idare_tur;
CREATE POLICY idare_tur_oku ON public.idare_tur FOR SELECT TO authenticated USING (true);
GRANT SELECT ON public.idare_tur TO authenticated;
GRANT ALL    ON public.idare_tur TO service_role;

-- Ağır agregasyon güvenliği (proconfig dersi: ALTER'lar CREATE'lerden SONRA)
ALTER FUNCTION public.idare_tur_bosluk(int)  SET statement_timeout = '30s';
ALTER FUNCTION public.idare_tur_kapsama()    SET statement_timeout = '30s';

NOTIFY pgrst, 'reload schema';

-- Kontrol:
--   SELECT public.idare_tur_kapsama();                 -- baslangicta kapsama %0
--   SELECT public.idare_tur_bosluk(20)->'eksik_idare_sayisi';
--   SELECT public.idare_normalize('T.C. ANKARA BÜYÜKŞEHİR BELEDİYESİ');  -- 'tc ankara buyuksehir belediyesi'
