-- ============================================================
-- MADDE 14 (perf) — DT yıl-özeti MV + tarih indeksi (31 Tem 2026)
-- ------------------------------------------------------------
-- SORUN: dt_analiz_ozet(...,p_yil) yıl-tek-başına ~12.4s (ANKARA yok, tüm Türkiye o yıl).
--   dogrudan_temin_ilanlari 1.49M, tarih indekssiz → make_date aralığı seq scan.
-- ÇÖZÜM (MADDE 12 deseni):
--   (a) idx_dt_ilanlari_tarih → yıl aralığı sargable (MV kurulumu + yıl+il canlı yolu hızlanır).
--   (b) dt_analiz_yil_mv → yıl başına TAM özet (2004→bugün, ~23 satır). Yıl-TEK seçim MV'den
--       ANINDA. Yıl + il/kategori/tür kombosu CANLI (alt-küme küçük, indeksle hızlı).
--
-- Çalıştır (superuser; MV kurulumu ~1-3 dk — 23 yıl × özet):
--   docker exec -i supabase-db psql -U supabase_admin -d postgres < backend/migration_dt_analiz_yil_mv.sql
-- GECE REFRESH: REFRESH MATERIALIZED VIEW CONCURRENTLY public.dt_analiz_yil_mv;
--               REFRESH MATERIALIZED VIEW public.dt_analiz_mv;
-- ============================================================

-- (a) tarih indeksi — yıl aralığı sargable
CREATE INDEX IF NOT EXISTS idx_dt_ilanlari_tarih
  ON public.dogrudan_temin_ilanlari (tarih) WHERE tarih IS NOT NULL;

-- (b) yıl-özeti MV: her yıl için _dt_ozet_json(NULL,NULL,NULL,yil)
DROP MATERIALIZED VIEW IF EXISTS public.dt_analiz_yil_mv;
CREATE MATERIALIZED VIEW public.dt_analiz_yil_mv AS
  SELECT y::int AS yil, public._dt_ozet_json(NULL, NULL, NULL, y::int) AS ozet
  FROM generate_series(2004, extract(year FROM now())::int) AS y;
CREATE UNIQUE INDEX IF NOT EXISTS dt_analiz_yil_mv_pk ON public.dt_analiz_yil_mv (yil);
GRANT SELECT ON public.dt_analiz_yil_mv TO authenticated, service_role;

-- Wrapper: yıl-TEK → yıl-MV; hiç filtre yok → genel MV; yıl+diğer → canlı.
CREATE OR REPLACE FUNCTION public.dt_analiz_ozet(
  p_il text DEFAULT NULL, p_kategori text DEFAULT NULL, p_tur text DEFAULT NULL, p_yil int DEFAULT NULL
) RETURNS jsonb
LANGUAGE plpgsql STABLE SECURITY DEFINER
SET search_path = public SET statement_timeout = '15s' AS $$
BEGIN
  IF (p_il IS NULL AND p_kategori IS NULL AND p_tur IS NULL AND p_yil IS NULL) THEN
    RETURN (SELECT ozet FROM public.dt_analiz_mv);                       -- hiç filtre: genel MV
  ELSIF (p_il IS NULL AND p_kategori IS NULL AND p_tur IS NULL AND p_yil IS NOT NULL) THEN
    RETURN COALESCE((SELECT ozet FROM public.dt_analiz_yil_mv WHERE yil = p_yil),
                    public._dt_ozet_json(NULL, NULL, NULL, p_yil));      -- yıl-tek: yıl-MV (yoksa canlı)
  END IF;
  RETURN public._dt_ozet_json(p_il, p_kategori, p_tur, p_yil);          -- yıl+diğer: canlı (küçük)
END;
$$;
GRANT EXECUTE ON FUNCTION public.dt_analiz_ozet(text, text, text, int) TO authenticated, service_role;

NOTIFY pgrst, 'reload schema';

-- Doğrulama (anlık olmalı):
--   \timing on
--   SELECT public.dt_analiz_ozet(NULL,NULL,NULL,2024) -> 'toplam';
