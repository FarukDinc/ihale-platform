-- ============================================================================
-- migration_qa_26_26_sonuc_tarihi_idx.sql — 26-26: Firma Segmentleri üst özet timeout
--   (2 Ağu 2026). firma_segment_sayilari() RPC'sinin 'ref_tarih' alt-sorgusu
--     SELECT max(s.sonuc_tarihi)::date FROM ihale_sonuclari s WHERE s.sonuc_tarihi <= now()
--   ihale_sonuclari.sonuc_tarihi'nde İNDEKS OLMADIĞI için 2,7M satırı tam-tablo tarıyordu
--   → RPC ~timeout → frontend catch tüm segment rozetlerini "—" ve pencereleri "hesaplanıyor…"
--   bırakıyordu. sonuc_tarihi btree indeksi max()'ı geri-tarama ile anlık yapar.
--   BONUS: MADDE 12/14'te not edilen "ihale_sonuclari sonuc_tarihi sıralaması TIMEOUT
--   (indekssiz tam-tablo)" sorununu da giderir.
--
-- ⚠️ CONCURRENTLY → transaction bloğu YOK (BEGIN/COMMIT koyma). 2,7M satır, tek seferlik
--   birkaç dakika sürebilir; tablo kilitlenmez.
-- Çalıştırma:
--   docker exec -i supabase-db psql -U supabase_admin -d postgres < backend/migration_qa_26_26_sonuc_tarihi_idx.sql
-- ============================================================================
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_ihale_sonuclari_sonuc_tarihi
  ON public.ihale_sonuclari (sonuc_tarihi);

-- Kontrol (ref_tarih anlık dönmeli, RPC timeout gitmeli):
--   EXPLAIN (ANALYZE, BUFFERS) SELECT max(sonuc_tarihi)::date FROM public.ihale_sonuclari WHERE sonuc_tarihi <= now();
--   \timing on
--   SELECT public.firma_segment_sayilari();
