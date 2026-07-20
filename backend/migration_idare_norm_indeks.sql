-- ============================================================================
-- idare_tur_tazele() hızlandırması — ifade indeksi
--
-- SORUN (20 Tem, ölçüldü): idare_tur_tazele() 340K backfill sonrası zincirde
-- 24+ dakika CPU-bound kaldı. İki UPDATE de JOIN koşulunda satır-başı
-- `idare_normalize(idare)` çağırıyor; ifade indeksi olmadığı için 1,9M + 1,49M
-- satırda tam tarama + her satırda fonksiyon değerlendirmesi. Fonksiyon
-- statement_timeout='1800s' ile korunmuş (yavaşlık biliniyormuş).
--
-- ÇÖZÜM: idare_normalize(idare) üzerine ifade indeksi. idare_normalize IMMUTABLE
-- (pg_proc.provolatile='i' ile doğrulandı) → ifade indeksi geçerli. Böylece
-- UPDATE'in JOIN'i (t.idare_norm = idare_normalize(i.idare)) indeksten yürür.
--
-- ⚠️ CONCURRENTLY + transaction DIŞINDA: 1,9M/1,49M satırda ACCESS EXCLUSIVE
-- kilidi almadan kurar (gece cron'unu / canlı sorguları dondurmaz). Her biri
-- ~birkaç dakika sürer.
--
-- Çalıştırma (VDS) — bf-zincir bittikten SONRA, tek tek:
--   docker exec -i supabase-db psql -U postgres -d postgres \
--     -c "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_ilanlar_idare_norm_expr ON public.ilanlar (public.idare_normalize(idare));"
--   docker exec -i supabase-db psql -U postgres -d postgres \
--     -c "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_dt_idare_norm_expr ON public.dogrudan_temin_ilanlari (public.idare_normalize(idare));"
--
-- Doğrulama sonrası: idare_tur_tazele()'yi tekrar koşup süreyi ölç (dakikalar → saniyeler beklenir).
-- ============================================================================

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_ilanlar_idare_norm_expr
  ON public.ilanlar (public.idare_normalize(idare));

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_dt_idare_norm_expr
  ON public.dogrudan_temin_ilanlari (public.idare_normalize(idare));
