-- ============================================================
-- MADDE 18-B — Firma dizini 3-mod sıralama: DT + İkisi birlikte (31 Tem 2026)
-- ------------------------------------------------------------
-- Firma Analizi dizini şu an yalnız İHALE cirosuna (yukleniciler.toplam_ciro) göre sıralıyor.
-- Kullanıcı 3 mod istedi: ① Sadece İhale ② Sadece DT ③ İhale+DT birlikte.
--
-- TEMİZ EŞLEŞME: yukleniciler.normalize_ad = normalize_firma(ad) ve DT tarafı
--   normalize_firma(kazanan_firma) → AYNI normalizasyon (migration_analiz_rpc.sql'de doğrulandı)
--   → "birlikte" modunda KESİN isim eşitliği join'i (fuzzy yok, sahte eşleşme riski normalize_firma
--   ile sınırlı). İhale ve DT evrenleri "birlikte" modunda TOPLANIR ama bu BİLİNÇLİ bir üst-görünüm;
--   dt_bedel ayrı kolonda da döner (şeffaflık).
--
-- Çalıştır (superuser; MV ~853K DT satırı, hızlı):
--   docker exec -i supabase-db psql -U supabase_admin -d postgres < backend/migration_firma_dt_toplam_mv.sql
-- GECE REFRESH: REFRESH MATERIALIZED VIEW CONCURRENTLY public.firma_dt_toplam;  (run_scraper.sh'e eklendi)
-- ============================================================

-- 1) MV: normalize firma → DT sözleşme sayısı + toplam bedel + görünen ad.
DROP MATERIALIZED VIEW IF EXISTS public.firma_dt_toplam;
CREATE MATERIALIZED VIEW public.firma_dt_toplam AS
  SELECT public.normalize_firma(s.kazanan_firma)                        AS firma_norm,
         (array_agg(s.kazanan_firma ORDER BY s.sozlesme_tarihi DESC NULLS LAST))[1] AS ad,
         count(*)::bigint                                               AS dt_sozlesme,
         sum(COALESCE(s.kazanan_bedel, 0))::numeric                     AS dt_bedel
  FROM public.dogrudan_temin_sonuclari s
  WHERE s.kazanan_firma IS NOT NULL
  GROUP BY public.normalize_firma(s.kazanan_firma);
CREATE UNIQUE INDEX IF NOT EXISTS firma_dt_toplam_pk    ON public.firma_dt_toplam (firma_norm);
CREATE INDEX        IF NOT EXISTS firma_dt_toplam_bedel ON public.firma_dt_toplam (dt_bedel DESC);
GRANT SELECT ON public.firma_dt_toplam TO authenticated, service_role;   -- anon'a KAPALI (firma adı)

-- 2) DT modu: DT bedeline göre en yüksek firmalar (yuklenici id varsa detay linki için döner).
CREATE OR REPLACE FUNCTION public.firma_dizin_dt(
  p_ara text DEFAULT NULL, p_limit int DEFAULT 100, p_offset int DEFAULT 0)
RETURNS TABLE (id uuid, ad text, il text, toplam_sozlesme_sayisi bigint,
               toplam_ciro numeric, son_sozlesme_tarihi timestamptz, dt_bedel numeric)
LANGUAGE sql STABLE SECURITY DEFINER SET search_path = public AS $$
  SELECT y.id, d.ad, y.il, d.dt_sozlesme, d.dt_bedel, NULL::timestamptz, d.dt_bedel
  FROM public.firma_dt_toplam d
  LEFT JOIN public.yukleniciler y ON y.normalize_ad = d.firma_norm
  WHERE (p_ara IS NULL OR d.firma_norm LIKE '%'||public.normalize_firma(p_ara)||'%')
  ORDER BY d.dt_bedel DESC NULLS LAST, d.dt_sozlesme DESC
  LIMIT LEAST(GREATEST(p_limit,1),200) OFFSET GREATEST(p_offset,0);
$$;
REVOKE EXECUTE ON FUNCTION public.firma_dizin_dt(text,int,int) FROM public, anon;
GRANT  EXECUTE ON FUNCTION public.firma_dizin_dt(text,int,int) TO authenticated, service_role;

-- 3) İkisi birlikte: yukleniciler (ihale) + eşleşen DT → ciro+bedel toplamına göre.
CREATE OR REPLACE FUNCTION public.firma_dizin_birlikte(
  p_ara text DEFAULT NULL, p_il text DEFAULT NULL, p_limit int DEFAULT 100, p_offset int DEFAULT 0)
RETURNS TABLE (id uuid, ad text, il text, toplam_sozlesme_sayisi bigint,
               toplam_ciro numeric, son_sozlesme_tarihi timestamptz, dt_bedel numeric)
LANGUAGE sql STABLE SECURITY DEFINER SET search_path = public AS $$
  SELECT y.id, y.ad, y.il,
         (COALESCE(y.toplam_sozlesme_sayisi,0) + COALESCE(d.dt_sozlesme,0))::bigint,
         (COALESCE(y.toplam_ciro,0) + COALESCE(d.dt_bedel,0))::numeric AS tutar,
         y.son_sozlesme_tarihi, COALESCE(d.dt_bedel,0)
  FROM public.yukleniciler y
  LEFT JOIN public.firma_dt_toplam d ON d.firma_norm = y.normalize_ad
  WHERE (p_ara IS NULL OR y.arama_fold LIKE '%'||public.tr_fold(p_ara)||'%')
    AND (p_il  IS NULL OR y.il = p_il)
  ORDER BY tutar DESC NULLS LAST
  LIMIT LEAST(GREATEST(p_limit,1),200) OFFSET GREATEST(p_offset,0);
$$;
REVOKE EXECUTE ON FUNCTION public.firma_dizin_birlikte(text,text,int,int) FROM public, anon;
GRANT  EXECUTE ON FUNCTION public.firma_dizin_birlikte(text,text,int,int) TO authenticated, service_role;

-- Cron -U postgres refresh edebilsin diye sahibi postgres'e devret (diğer MV'lerle tutarlı).
ALTER MATERIALIZED VIEW public.firma_dt_toplam OWNER TO postgres;

NOTIFY pgrst, 'reload schema';

-- Doğrulama:
--   SELECT ad, toplam_sozlesme_sayisi, dt_bedel FROM firma_dizin_dt(NULL, 5, 0);
--   SELECT ad, toplam_ciro, dt_bedel FROM firma_dizin_birlikte(NULL, NULL, 5, 0);
