-- ============================================================
-- DT Analizi il filtresi timeout düzeltmesi (31 Tem 2026)
-- ------------------------------------------------------------
-- dt_analiz_ozet(p_il='ANKARA') → _dt_ozet_json filtreli yol timeout (15s aşımı).
-- Sebep: dogrudan_temin_ilanlari'nda DÜZ `il` indeksi yok (yalnız aktif-partial var) →
--   WHERE il = 'ANKARA' 1.49M satırı seq-scan. İl indeksiyle ANKARA alt-kümesine hızlı iner.
--
-- Çalıştır (CONCURRENTLY, kilitlemez):
--   docker exec -i supabase-db psql -U supabase_admin -d postgres < backend/migration_dt_ilanlari_il_index.sql
-- ============================================================

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_dt_ilanlari_il
  ON public.dogrudan_temin_ilanlari (il) WHERE il IS NOT NULL;

-- Doğrulama (artık <15s):
--   SELECT public.dt_analiz_ozet('ANKARA', NULL, NULL, NULL) -> 'toplam';
