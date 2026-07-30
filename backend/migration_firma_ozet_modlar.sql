-- ============================================================
-- MADDE 20 — Firma dizini KPI'ları mod-duyarlı (DT / İkisi) (31 Tem 2026)
-- ------------------------------------------------------------
-- Firma Dizini üst KPI'ları (Toplam Firma/Sözleşme/Ciro/İş Ortaklığı) hep "yalnız ihaleler"
-- (yuklenici_ozet). Kullanıcı: DT modunda DT'ye göre, İkisi modunda İhale+DT birleşik olsun.
-- yuklenici_ozet ile AYNI dönüş şekli → frontend moda göre farklı RPC çağırır.
--
-- Çalıştır (superuser):
--   docker exec -i supabase-db psql -U supabase_admin -d postgres < backend/migration_firma_ozet_modlar.sql
-- ============================================================

-- DT özeti: firma_dt_toplam MV'sinden (anlık). İş ortaklığı ~ adında "ortakl" geçenler.
CREATE OR REPLACE FUNCTION public.firma_ozet_dt()
RETURNS TABLE (toplam bigint, toplam_sozlesme numeric, toplam_ciro numeric, ortak_sayisi bigint)
LANGUAGE sql STABLE SECURITY DEFINER SET search_path = public AS $$
  SELECT count(*)::bigint,
         COALESCE(sum(dt_sozlesme),0)::numeric,
         COALESCE(sum(dt_bedel),0)::numeric,
         (count(*) FILTER (WHERE ad ILIKE '%ortakl%'))::bigint
  FROM public.firma_dt_toplam;
$$;
REVOKE EXECUTE ON FUNCTION public.firma_ozet_dt() FROM public;
GRANT  EXECUTE ON FUNCTION public.firma_ozet_dt() TO anon, authenticated, service_role;

-- İkisi birlikte: ihale (yuklenici_ozet_mv) + DT (firma_dt_toplam). Firma = normalize isim BİRLEŞİMİ
-- (union distinct — DT-only firmalar da sayılsın, çift sayılmasın). Diğerleri toplanır.
CREATE OR REPLACE FUNCTION public.firma_ozet_birlikte()
RETURNS TABLE (toplam bigint, toplam_sozlesme numeric, toplam_ciro numeric, ortak_sayisi bigint)
LANGUAGE sql STABLE SECURITY DEFINER SET search_path = public AS $$
  WITH ih AS (SELECT toplam, toplam_sozlesme, toplam_ciro, ortak_sayisi FROM public.yuklenici_ozet_mv),
       dt AS (SELECT count(*) c, COALESCE(sum(dt_sozlesme),0) s, COALESCE(sum(dt_bedel),0) b,
                     count(*) FILTER (WHERE ad ILIKE '%ortakl%') o FROM public.firma_dt_toplam),
       birlesik AS (SELECT count(*) n FROM (
                     SELECT normalize_ad AS x FROM public.yukleniciler WHERE normalize_ad IS NOT NULL
                     UNION
                     SELECT firma_norm FROM public.firma_dt_toplam) u)
  SELECT (SELECT n FROM birlesik)::bigint,
         ((SELECT toplam_sozlesme FROM ih) + (SELECT s FROM dt))::numeric,
         ((SELECT toplam_ciro FROM ih) + (SELECT b FROM dt))::numeric,
         ((SELECT ortak_sayisi FROM ih) + (SELECT o FROM dt))::bigint;
$$;
REVOKE EXECUTE ON FUNCTION public.firma_ozet_birlikte() FROM public;
GRANT  EXECUTE ON FUNCTION public.firma_ozet_birlikte() TO anon, authenticated, service_role;

NOTIFY pgrst, 'reload schema';

-- Doğrulama:
--   SELECT * FROM firma_ozet_dt();
--   SELECT * FROM firma_ozet_birlikte();
