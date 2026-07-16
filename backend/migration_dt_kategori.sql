-- ============================================================
-- migration_dt_kategori.sql — dogrudan_temin_ilanlari.kategori
-- 41 kanonik kategori (adlar js/kategoriler.js + kategori_siniflandir.py ile birebir).
-- DT'de OKAS yok → kategori_belirle(None, tur, baslik) ile keyword+tür fallback (backfill Python'da).
--
-- Çalıştırma: docker exec -i supabase-db psql -U postgres -d postgres < backend/migration_dt_kategori.sql
-- NOT: Adım C (CONCURRENTLY) transaction dışında — backfill BİTTİKTEN sonra ayrıca çalıştırılır.
-- ============================================================

-- ADIM A: kolon (NULLable, DEFAULT yok → tablo rewrite YOK, milisaniyelik metadata değişikliği)
BEGIN;
SET LOCAL lock_timeout = '5s';  -- ACCESS EXCLUSIVE kuyrukta okuyucuları bloklamasın; timeout'ta tekrar dene
ALTER TABLE public.dogrudan_temin_ilanlari
  ADD COLUMN IF NOT EXISTS kategori TEXT;
COMMIT;

-- ŞART: PostgREST kolonu görmezse scraper upsert + backfill PATCH PGRST204 ile düşer
NOTIFY pgrst, 'reload schema';

-- ADIM B: BACKFILL — SQL'de DEĞİL, Python'da (tek doğruluk kaynağı: kategori_siniflandir.kategori_belirle)
--   python backend/dt_kategori_backfill.py --dry-run   # önce ~50K örneklem dağılımı
--   python backend/dt_kategori_backfill.py             # keyset, idempotent, kesilirse yeniden çalıştır

-- ADIM C: index — backfill BİTTİKTEN SONRA, transaction DIŞINDA (bu satır ayrıca elle çalıştırılır):
--   CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_dt_ilanlari_kategori_tarih
--     ON public.dogrudan_temin_ilanlari (kategori, tarih DESC);

-- ADIM D: doğrulama
--   SELECT kategori, count(*) FROM public.dogrudan_temin_ilanlari GROUP BY 1 ORDER BY 2 DESC;
--   SELECT count(*) FILTER (WHERE kategori IS NULL) AS kalan_null FROM public.dogrudan_temin_ilanlari;
