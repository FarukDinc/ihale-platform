-- ============================================================================
-- MADDE 20-B — Harita: İhale/DT toggle + il×sektör firma sıralaması + son-1-yıl ölçütü
-- (31 Tem 2026)
-- ----------------------------------------------------------------------------
-- Mevcut harita TÜMÜYLE İhale-bazlı, tüm-zaman. Kullanıcı: ① İhale/DT toggle →
-- choropleth yoğunluğu + firma listesi o baza göre. ② Sektör (var) + ölçüt:
-- en çok ciro · sözleşme · son-1-yıl ciro · son-1-yıl sözleşme.
--
-- MİMARİ (mevcut deseni AYNEN izler):
--   · BÜYÜK MV il_sektor_firma_mv (il×sektör×firma, FİRMA ADI içerir → anon KAPALI).
--     Buna son-1-yıl FILTER kolonları (sozlesme_1y/bedel_1y) eklenir → REBUILD gerekir.
--   · MINI MV il_sektor_ozet_mv (il×sektör yoğunluk, İSİM YOK → anon AÇIK) büyükten türer.
--     CASCADE ile düşer → bu migrationda YENİDEN kurulur (yoksa dashboard/harita yoğunluğu kırılır).
--   · DT için AYNI ikili: il_sektor_firma_dt_mv (anon kapalı) + il_sektor_ozet_dt_mv (anon açık).
--   · Firma listesi RPC'leri (isim döner) → yalnız authenticated. Yoğunluk RPC'leri → anon.
--
-- ⚠️ ANON MASKE KORUNUR: yeni MV varsayılan ayrıcalıkla anon-açık DOĞAR → firma-adı içeren
--    MV'lerde önce REVOKE (bkz. hafıza anon-maske-iki-kok-neden). DT tarih kaynağı i.tarih (~%100).
--
-- Çalıştır (superuser; REBUILD'ler normalize_firma nedeniyle DAKİKALAR sürer):
--   docker exec -i supabase-db psql -U supabase_admin -d postgres < backend/migration_harita_20b.sql
-- GECE REFRESH (run_scraper.sh): 4 MV — il_sektor_firma_mv, il_sektor_ozet_mv (var) +
--   il_sektor_firma_dt_mv, il_sektor_ozet_dt_mv (YENİ; büyük→mini sırası).
-- ============================================================================

-- ── 0) DT join indeksleri ──
CREATE INDEX IF NOT EXISTS idx_dt_sonuclari_dt_no     ON public.dogrudan_temin_sonuclari (dt_no);
CREATE INDEX IF NOT EXISTS idx_dt_ilanlari_dtno       ON public.dogrudan_temin_ilanlari (dt_no);
CREATE INDEX IF NOT EXISTS idx_dt_ilanlari_ilfold_kat ON public.dogrudan_temin_ilanlari (tr_fold(il), kategori);

-- ============================================================================
-- 1) İHALE büyük MV'yi son-1-yıl kolonlarıyla YENİDEN kur. CASCADE il_sektor_ozet_mv'yi
--    düşürür → aşağıda 2)'de yeniden kurulur. now() REFRESH anında değerlenir (rolling 1y).
-- ============================================================================
DROP MATERIALIZED VIEW IF EXISTS public.il_sektor_firma_mv CASCADE;
CREATE MATERIALIZED VIEW public.il_sektor_firma_mv AS
SELECT i.il                                                                    AS il,
       tr_fold(i.il)                                                           AS il_fold,
       COALESCE(NULLIF(btrim(i.kategori), ''), 'Diğer')                        AS kategori,
       normalize_firma(s.kazanan_firma)                                        AS firma_norm,
       (array_agg(s.kazanan_firma ORDER BY s.sonuc_tarihi DESC NULLS LAST))[1] AS ad,
       max(s.sonuc_tarihi)                                                     AS son_tarih,
       count(*)::bigint                                                        AS sozlesme,
       sum(COALESCE(s.kazanan_teklif, 0))                                      AS toplam_bedel,
       count(*) FILTER (WHERE s.sonuc_tarihi >= now() - interval '1 year')::bigint AS sozlesme_1y,
       sum(COALESCE(s.kazanan_teklif,0)) FILTER (WHERE s.sonuc_tarihi >= now() - interval '1 year') AS bedel_1y
FROM public.ihale_sonuclari s
JOIN public.ilanlar i ON i.id = s.ilan_id
WHERE s.kazanan_firma IS NOT NULL
  AND i.il IS NOT NULL AND btrim(i.il) <> ''
  AND normalize_firma(s.kazanan_firma) IS NOT NULL
GROUP BY i.il, tr_fold(i.il),
         COALESCE(NULLIF(btrim(i.kategori), ''), 'Diğer'),
         normalize_firma(s.kazanan_firma);
CREATE UNIQUE INDEX IF NOT EXISTS idx_il_sektor_firma_mv_pk   ON public.il_sektor_firma_mv (il, kategori, firma_norm);
CREATE INDEX        IF NOT EXISTS idx_il_sektor_firma_mv_fold ON public.il_sektor_firma_mv (il_fold, kategori);
ANALYZE public.il_sektor_firma_mv;
ALTER MATERIALIZED VIEW public.il_sektor_firma_mv OWNER TO postgres;      -- cron -U postgres refresh
REVOKE ALL ON public.il_sektor_firma_mv FROM anon, public;                -- FİRMA ADI → anon KAPALI (maske korunur)
GRANT  SELECT ON public.il_sektor_firma_mv TO authenticated, service_role;

-- ── 2) MINI MV (isim yok → anon açık) + il_sektor_ozet() geri yükle (imza/format aynı) ──
DROP MATERIALIZED VIEW IF EXISTS public.il_sektor_ozet_mv;
CREATE MATERIALIZED VIEW public.il_sektor_ozet_mv AS
SELECT il, kategori, count(*)::bigint AS firma_adet,
       sum(sozlesme)::bigint AS sozlesme_adet, sum(toplam_bedel) AS toplam_bedel
FROM public.il_sektor_firma_mv GROUP BY il, kategori;
CREATE UNIQUE INDEX IF NOT EXISTS idx_il_sektor_ozet_mv_pk ON public.il_sektor_ozet_mv (il, kategori);
ALTER MATERIALIZED VIEW public.il_sektor_ozet_mv OWNER TO postgres;
GRANT SELECT ON public.il_sektor_ozet_mv TO anon, authenticated, service_role;

CREATE OR REPLACE FUNCTION public.il_sektor_ozet()
RETURNS jsonb LANGUAGE sql STABLE AS $$
  SELECT COALESCE(jsonb_agg(jsonb_build_object(
           'il', il, 'kategori', kategori, 'firma_adet', firma_adet,
           'sozlesme_adet', sozlesme_adet, 'toplam_bedel', toplam_bedel)), '[]'::jsonb)
  FROM public.il_sektor_ozet_mv;
$$;
ALTER FUNCTION public.il_sektor_ozet() SET statement_timeout = '15s';
GRANT EXECUTE ON FUNCTION public.il_sektor_ozet() TO anon, authenticated, service_role;

-- ── 3) İhale firma sıralaması + p_son_yil + p_olcut (3-arg eski çağrılar default'la düşer) ──
DROP FUNCTION IF EXISTS public.il_sektor_firmalar(text[], text, int);
CREATE OR REPLACE FUNCTION public.il_sektor_firmalar(
  p_il_folds text[], p_kategori text DEFAULT NULL, p_limit int DEFAULT 8,
  p_son_yil boolean DEFAULT false, p_olcut text DEFAULT 'bedel')
RETURNS TABLE(ad text, sozlesme bigint, toplam_bedel numeric)
LANGUAGE sql STABLE AS $$
  SELECT (array_agg(ad ORDER BY son_tarih DESC NULLS LAST))[1] AS ad,
         sum(CASE WHEN p_son_yil THEN sozlesme_1y ELSE sozlesme END)::bigint AS sozlesme,
         sum(CASE WHEN p_son_yil THEN bedel_1y   ELSE toplam_bedel END)      AS toplam_bedel
  FROM public.il_sektor_firma_mv
  WHERE il_fold = ANY(p_il_folds)
    AND (p_kategori IS NULL OR kategori = p_kategori)
  GROUP BY firma_norm
  HAVING sum(CASE WHEN p_son_yil THEN sozlesme_1y ELSE sozlesme END) > 0
  ORDER BY CASE WHEN p_olcut='sozlesme'
             THEN sum(CASE WHEN p_son_yil THEN sozlesme_1y ELSE sozlesme END)::numeric
             ELSE sum(CASE WHEN p_son_yil THEN bedel_1y   ELSE toplam_bedel END) END DESC,
           sum(CASE WHEN p_son_yil THEN sozlesme_1y ELSE sozlesme END) DESC
  LIMIT GREATEST(1, LEAST(COALESCE(p_limit, 8), 50));
$$;
ALTER FUNCTION public.il_sektor_firmalar(text[], text, int, boolean, text) SET statement_timeout = '15s';
GRANT EXECUTE ON FUNCTION public.il_sektor_firmalar(text[], text, int, boolean, text) TO anon, authenticated, service_role;

-- ============================================================================
-- 4) DT büyük MV (firma ADI içerir → anon KAPALI). Yıl kaynağı i.tarih (~%100 dolu).
-- ============================================================================
DROP MATERIALIZED VIEW IF EXISTS public.il_sektor_firma_dt_mv CASCADE;
CREATE MATERIALIZED VIEW public.il_sektor_firma_dt_mv AS
SELECT i.il                                                                     AS il,
       tr_fold(i.il)                                                            AS il_fold,
       COALESCE(NULLIF(btrim(i.kategori), ''), 'Diğer')                         AS kategori,
       normalize_firma(s.kazanan_firma)                                         AS firma_norm,
       (array_agg(s.kazanan_firma ORDER BY i.tarih DESC NULLS LAST))[1]         AS ad,
       max(i.tarih)                                                             AS son_tarih,
       count(*)::bigint                                                         AS sozlesme,
       sum(COALESCE(s.kazanan_bedel, 0))                                        AS toplam_bedel,
       count(*) FILTER (WHERE i.tarih >= now() - interval '1 year')::bigint     AS sozlesme_1y,
       sum(COALESCE(s.kazanan_bedel,0)) FILTER (WHERE i.tarih >= now() - interval '1 year') AS bedel_1y
FROM public.dogrudan_temin_sonuclari s
JOIN public.dogrudan_temin_ilanlari i ON i.dt_no = s.dt_no
WHERE s.kazanan_firma IS NOT NULL
  AND i.il IS NOT NULL AND btrim(i.il) <> ''
  AND normalize_firma(s.kazanan_firma) IS NOT NULL
GROUP BY i.il, tr_fold(i.il),
         COALESCE(NULLIF(btrim(i.kategori), ''), 'Diğer'),
         normalize_firma(s.kazanan_firma);
CREATE UNIQUE INDEX IF NOT EXISTS idx_il_sektor_firma_dt_mv_pk   ON public.il_sektor_firma_dt_mv (il, kategori, firma_norm);
CREATE INDEX        IF NOT EXISTS idx_il_sektor_firma_dt_mv_fold ON public.il_sektor_firma_dt_mv (il_fold, kategori);
ANALYZE public.il_sektor_firma_dt_mv;
ALTER MATERIALIZED VIEW public.il_sektor_firma_dt_mv OWNER TO postgres;
REVOKE ALL ON public.il_sektor_firma_dt_mv FROM anon, public;             -- FİRMA ADI → anon KAPALI
GRANT  SELECT ON public.il_sektor_firma_dt_mv TO authenticated, service_role;

-- ── 5) DT MINI MV (isim yok → anon açık) + yoğunluk RPC ──
DROP MATERIALIZED VIEW IF EXISTS public.il_sektor_ozet_dt_mv;
CREATE MATERIALIZED VIEW public.il_sektor_ozet_dt_mv AS
SELECT il, kategori, count(*)::bigint AS firma_adet,
       sum(sozlesme)::bigint AS sozlesme_adet, sum(toplam_bedel) AS toplam_bedel
FROM public.il_sektor_firma_dt_mv GROUP BY il, kategori;
CREATE UNIQUE INDEX IF NOT EXISTS idx_il_sektor_ozet_dt_mv_pk ON public.il_sektor_ozet_dt_mv (il, kategori);
ALTER MATERIALIZED VIEW public.il_sektor_ozet_dt_mv OWNER TO postgres;
GRANT SELECT ON public.il_sektor_ozet_dt_mv TO anon, authenticated, service_role;

CREATE OR REPLACE FUNCTION public.il_sektor_ozet_dt()
RETURNS jsonb LANGUAGE sql STABLE AS $$
  SELECT COALESCE(jsonb_agg(jsonb_build_object(
           'il', il, 'kategori', kategori, 'firma_adet', firma_adet,
           'sozlesme_adet', sozlesme_adet, 'toplam_bedel', toplam_bedel)), '[]'::jsonb)
  FROM public.il_sektor_ozet_dt_mv;
$$;
ALTER FUNCTION public.il_sektor_ozet_dt() SET statement_timeout = '15s';
GRANT EXECUTE ON FUNCTION public.il_sektor_ozet_dt() TO anon, authenticated, service_role;

-- ── 6) DT firma sıralaması (isim döner) → SECURITY DEFINER, yalnız authenticated ──
CREATE OR REPLACE FUNCTION public.il_sektor_firmalar_dt(
  p_il_folds text[], p_kategori text DEFAULT NULL, p_limit int DEFAULT 8,
  p_son_yil boolean DEFAULT false, p_olcut text DEFAULT 'bedel')
RETURNS TABLE(ad text, sozlesme bigint, toplam_bedel numeric)
LANGUAGE sql STABLE SECURITY DEFINER SET search_path = public AS $$
  SELECT (array_agg(ad ORDER BY son_tarih DESC NULLS LAST))[1] AS ad,
         sum(CASE WHEN p_son_yil THEN sozlesme_1y ELSE sozlesme END)::bigint AS sozlesme,
         sum(CASE WHEN p_son_yil THEN bedel_1y   ELSE toplam_bedel END)      AS toplam_bedel
  FROM public.il_sektor_firma_dt_mv
  WHERE il_fold = ANY(p_il_folds)
    AND (p_kategori IS NULL OR kategori = p_kategori)
  GROUP BY firma_norm
  HAVING sum(CASE WHEN p_son_yil THEN sozlesme_1y ELSE sozlesme END) > 0
  ORDER BY CASE WHEN p_olcut='sozlesme'
             THEN sum(CASE WHEN p_son_yil THEN sozlesme_1y ELSE sozlesme END)::numeric
             ELSE sum(CASE WHEN p_son_yil THEN bedel_1y   ELSE toplam_bedel END) END DESC,
           sum(CASE WHEN p_son_yil THEN sozlesme_1y ELSE sozlesme END) DESC
  LIMIT GREATEST(1, LEAST(COALESCE(p_limit, 8), 50));
$$;
ALTER FUNCTION public.il_sektor_firmalar_dt(text[], text, int, boolean, text) SET statement_timeout = '20s';
REVOKE EXECUTE ON FUNCTION public.il_sektor_firmalar_dt(text[], text, int, boolean, text) FROM public, anon;
GRANT  EXECUTE ON FUNCTION public.il_sektor_firmalar_dt(text[], text, int, boolean, text) TO authenticated, service_role;

NOTIFY pgrst, 'reload schema';

-- Doğrulama:
--   SELECT count(*) FROM il_sektor_firma_mv;  SELECT count(*) FROM il_sektor_firma_dt_mv;
--   SELECT jsonb_array_length(il_sektor_ozet());  SELECT jsonb_array_length(il_sektor_ozet_dt());
--   SELECT * FROM il_sektor_firmalar(ARRAY['ankara'],NULL,5,true,'bedel');       -- İhale son-1-yıl ciro
--   SELECT * FROM il_sektor_firmalar_dt(ARRAY['ankara'],NULL,5,false,'sozlesme'); -- DT tüm-zaman sözleşme
--   -- anon maske testi (anon rolüyle): il_sektor_firma_mv / _dt_mv → permission denied BEKLENİR.
