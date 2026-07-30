-- ============================================================
-- MADDE 12 (perf) — il × yıl × firma materialized view (31 Tem 2026)
-- ------------------------------------------------------------
-- SORUN: il_firma_yil canlıda ~20 sn (ANKARA 2024) → PostgREST timeout. ANKARA+yıl
--   kesişimi binlerce sonuç; normalize_firma() GROUP BY + non-sargable yıl extract pahalı.
-- ÇÖZÜM (proje deseni: statement-timeout-edge = MV + gece REFRESH): ağır agregatı
--   önceden hesapla; il_firma_yil MV'den indeksli anlık okur (<50ms).
--   MV kurulumu tek seferlik ağır tarama (ihale_sonuclari 2.9M) — dakikalar sürebilir, normal.
--
-- Çalıştır (superuser; MV kurulumu uzun sürebilir):
--   docker exec -i supabase-db psql -U supabase_admin -d postgres < backend/migration_il_yil_firma_mv.sql
-- GECE REFRESH: cron'a eklenecek → REFRESH MATERIALIZED VIEW CONCURRENTLY public.il_yil_firma;
-- ============================================================

-- 1) MV: her (il_fold, yıl, normalize firma) için sözleşme sayısı + toplam bedel + görünen ad.
DROP MATERIALIZED VIEW IF EXISTS public.il_yil_firma;
CREATE MATERIALIZED VIEW public.il_yil_firma AS
  SELECT public.tr_fold(i.il)                               AS il_fold,
         extract(year FROM COALESCE(s.sozlesme_tarihi, s.sonuc_tarihi))::int AS yil,
         public.normalize_firma(s.kazanan_firma)            AS firma_norm,
         (array_agg(s.kazanan_firma ORDER BY s.sonuc_tarihi DESC NULLS LAST))[1] AS ad,
         count(*)::bigint                                   AS sozlesme,
         sum(COALESCE(s.kazanan_teklif, 0))::numeric        AS toplam_bedel
  FROM public.ihale_sonuclari s
  JOIN public.ilanlar i ON i.id = s.ilan_id
  WHERE s.kazanan_firma IS NOT NULL
    AND i.il IS NOT NULL
    AND COALESCE(s.sozlesme_tarihi, s.sonuc_tarihi) IS NOT NULL
  GROUP BY 1, 2, 3
  WITH DATA;

-- CONCURRENTLY refresh için UNIQUE indeks ŞART; sorgu için (il_fold, yil, toplam_bedel DESC).
CREATE UNIQUE INDEX IF NOT EXISTS idx_il_yil_firma_uniq ON public.il_yil_firma (il_fold, yil, firma_norm);
CREATE INDEX IF NOT EXISTS idx_il_yil_firma_sirala ON public.il_yil_firma (il_fold, yil, toplam_bedel DESC);

GRANT SELECT ON public.il_yil_firma TO anon, authenticated, service_role;

-- 2) il_firma_yil → artık MV'den okur (anlık). İmza aynı → frontend değişmez.
CREATE OR REPLACE FUNCTION public.il_firma_yil(
  p_il_folds text[], p_yil int, p_limit int DEFAULT 8)
RETURNS TABLE (ad text, sozlesme bigint, toplam_bedel numeric)
LANGUAGE sql STABLE SECURITY INVOKER SET search_path = public AS $$
  SELECT ad, sozlesme, toplam_bedel
  FROM public.il_yil_firma
  WHERE il_fold = ANY(p_il_folds) AND yil = p_yil
  ORDER BY toplam_bedel DESC, sozlesme DESC
  LIMIT LEAST(GREATEST(p_limit, 1), 50);
$$;
GRANT EXECUTE ON FUNCTION public.il_firma_yil(text[], int, int) TO anon, authenticated, service_role;

NOTIFY pgrst, 'reload schema';

-- Doğrulama (anlık olmalı):
--   \timing on
--   SELECT * FROM il_firma_yil(ARRAY['ankara'], 2024, 8);
