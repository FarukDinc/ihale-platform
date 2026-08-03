-- ============================================================================
-- migration_sozlesme_ozet.sql — UV-6: Sözleşmeler sayfası üst stat tile'ları (3 Ağu 2026)
--
-- Sözleşmeler landing'e rakip düzeni stat tile'ları (Toplam Sözleşme / Toplam Bedel /
-- Ort. Tenzilat / Devam Eden). Global aggregate 2,72M satırda ~8,7s → CANLI RPC OLMAZ →
-- tek-satır MV (gece REFRESH CONCURRENTLY). Aggregate (sum/avg) hash-join YOK → /dev/shm
-- 64MB sorunu tetiklemez (bkz docker-shm-64mb-mv).
--
-- Aggregate global (firma-bağımsız, hassas değil) → anon'a AÇIK (rakip de özet sayıları
-- misafire gösteriyor; liste yine üye-only). Bkz [[veri-disa-aktarim-yasagi]] — bu MV firma adı içermez.
--
-- Çalıştırma:
--   docker exec -i supabase-db psql -U supabase_admin -d postgres < backend/migration_sozlesme_ozet.sql
-- ============================================================================

BEGIN;

CREATE MATERIALIZED VIEW IF NOT EXISTS public.sozlesme_ozet_mv AS
SELECT
  count(*)::bigint                                                              AS toplam_sozlesme,
  COALESCE(sum(sozlesme_bedeli), 0)::numeric                                    AS toplam_bedel,
  round(avg(tenzilat_yuzde) FILTER (WHERE abs(tenzilat_yuzde) < 100), 1)        AS ort_tenzilat,
  count(*) FILTER (WHERE is_bitis_tarihi IS NOT NULL AND is_bitis_tarihi >= now())::bigint AS devam,
  count(*) FILTER (WHERE is_bitis_tarihi IS NOT NULL AND is_bitis_tarihi <  now())::bigint AS biten
FROM public.ihale_sonuclari;

-- Tek satır MV — CONCURRENTLY refresh için sabit-ifade unique index (reads bloklanmaz; refresh ~8,7s aggregate).
CREATE UNIQUE INDEX IF NOT EXISTS idx_sozlesme_ozet_mv_tek ON public.sozlesme_ozet_mv ((1));

ANALYZE public.sozlesme_ozet_mv;

GRANT SELECT ON public.sozlesme_ozet_mv TO anon, authenticated, service_role;

COMMIT;

NOTIFY pgrst, 'reload schema';

-- DOĞRULAMA:
--   SELECT * FROM public.sozlesme_ozet_mv;
