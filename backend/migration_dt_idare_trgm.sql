-- =============================================================================
-- migration_dt_idare_trgm.sql — dogrudan_temin_ilanlari.idare için GIN trgm indeksi
-- =============================================================================
--
-- SORUN: DT'de `idare ILIKE '%...%'` 2,9M satırda indekslenemiyordu → 57014 TIMEOUT.
-- Belirtiler: (1) v1-ihaleler DT idare-filtreli sonuç/geçmiş "Liste yüklenemedi",
-- (2) kurum-analiz Dağılım Analizi → Doğrudan Temin "yüklenemedi" (kurum_dt_ozet).
-- (arama_fold DENENDİ ama o kolon DT'de YOK — migration_dt_arama prod'a uygulanmamış.)
--
-- ÇÖZÜM: idare kolonuna doğrudan pg_trgm GIN indeksi → ILIKE substring araması hızlanır.
-- Böylece hem v1-ihaleler DT idare filtresi hem kurum_dt_ozet(idare ILIKE) hızlı çalışır,
-- arama_fold bağımlılığı olmadan.
--
-- ⚠️ CREATE INDEX CONCURRENTLY: transaction bloğu DIŞINDA çalışır (BEGIN/COMMIT YOK).
-- Okumaları/yazmaları bloklamaz; 2,9M satırda birkaç dakika sürebilir.
--
-- Uygulama (BEGIN'siz, doğrudan):
--   docker exec -i supabase-db psql -U supabase_admin -d postgres < backend/migration_dt_idare_trgm.sql
-- =============================================================================

CREATE EXTENSION IF NOT EXISTS pg_trgm;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_dt_idare_trgm
  ON public.dogrudan_temin_ilanlari USING gin (idare gin_trgm_ops);

ANALYZE public.dogrudan_temin_ilanlari;

-- DOĞRULAMA:
--   EXPLAIN SELECT count(*) FROM public.dogrudan_temin_ilanlari WHERE idare ILIKE '%ankara%';
--   -- "Bitmap Index Scan on idx_dt_idare_trgm" görülmeli.
