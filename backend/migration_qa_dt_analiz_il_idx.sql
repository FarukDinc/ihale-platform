-- ============================================================================
-- migration_qa_dt_analiz_il_idx.sql — DT Analizi il-filtresi statement timeout
--   (2 Ağu 2026). dt_analiz_ozet(p_il=...) → _dt_ozet_json, `f` CTE:
--     WHERE il = p_il  → dogrudan_temin_ilanlari (2,97M) TAM-TABLO taranıyordu (il indekssiz)
--   → ANKARA gibi büyük ilde 15s statement_timeout AŞILIYOR ("Analiz alınamadı… timeout").
--   YIL filtresi çalışıyor çünkü `tarih` indeksli (idx_dt_ilanlari_tarih, MADDE 14); il için
--   karşılığı eksikti. il btree indeksi filtreyi il alt-kümesine indirir (join+median zaten
--   yıl yolunda kanıtlandığı gibi bu alt-kümede hızlı).
--
-- ⚠️ CONCURRENTLY → transaction bloğu YOK. Tek seferlik birkaç dk; tablo kilitlenmez.
-- Çalıştırma:
--   docker exec -i supabase-db psql -U supabase_admin -d postgres < backend/migration_qa_dt_analiz_il_idx.sql
-- ============================================================================
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_dt_ilanlari_il
  ON public.dogrudan_temin_ilanlari (il);

-- Kontrol (ANKARA artık <1-2s dönmeli):
--   \timing on
--   SELECT public.dt_analiz_ozet('ANKARA',NULL,NULL,NULL) -> 'toplam';
