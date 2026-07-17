-- ============================================================================
-- migration_ai_kategori_jenerik.sql (17 Tem 2026) — AI kategori backfill'i JENERİK
-- KOVALARA genişlet + eski etiket birleştir.
--
-- KÖK NEDEN (bu oturumda ölçüldü): eşleştirme motorunun asıl körlüğü OKAS değil
-- (OKAS zaten %2,8) — ilanların %58'i "Mal Alımı"/"Hizmet Alımı"/"Diğer" gibi
-- JENERİK kovada; bunlar EKAP'ın satınalma-TÜRÜ, sektör DEĞİL → "konusu ne?"
-- sorusuna cevap vermiyor, uygun-firma/benzer-ihale algoritması kör kalıyor.
--   Mal Alımı   86.992
--   Diğer       67.658   (mevcut AI backfill yalnız bunu hedefliyordu)
--   Hizmet Alımı 50.980
--   ≈ 205.630 satır AI ile kanonik sektöre oturtulabilir.
--
-- AYRICA (bu migration önce çalıştıran): migration_ai_kategori.sql PROD'A HİÇ
-- UYGULANMAMIŞ (ai_kategori_denendi kolonu yoktu) → gece cron her gece "migration
-- eksik" deyip çıkmış, AI backfill hiç çalışmamış. Bu dosya kolonu da kurar (idempotent).
--
-- BONUS (deterministik, AI'sız): "İnşaat & Yapım" (22.104) ESKİ etiket — js/kategoriler.js'teki
-- 41 kanonikte YOK → sektör filtresi/harita onu görmüyor. Kanonik karşılığına birleştirilir
-- (net sektör sinyali taşıdığından AI'a sormaya gerek yok, tek UPDATE).
--
-- Çalıştır: docker exec -i supabase-db psql -U postgres -d postgres < backend/migration_ai_kategori_jenerik.sql
-- Idempotent: ADD COLUMN / CREATE INDEX IF NOT EXISTS; UPDATE yalnız eşleşen satırı değiştirir.
-- ============================================================================

-- 1) İşaret kolonu (migration_ai_kategori.sql hiç koşmadıysa da burada garanti)
ALTER TABLE public.ilanlar
  ADD COLUMN IF NOT EXISTS ai_kategori_denendi timestamptz;

COMMENT ON COLUMN public.ilanlar.ai_kategori_denendi IS
  'ai_kategori_backfill.py bu satiri Gemini''ye sordu (zaman damgasi). NULL=hic denenmedi. '
  'Bir kez denenen satir (sonuc jenerik kalsa bile) tekrar sorulmaz -> idempotent, token israfi yok.';

-- 2) Legacy "İnşaat & Yapım" → kanonik. AI'sız, deterministik; ai_kategori_denendi'ye DOKUNMAZ
--    (zaten kanonik olacağı için kuyruğa girmez). Konu sinyali net (inşaat) olduğundan güvenli.
UPDATE public.ilanlar
   SET kategori = 'İnşaat - Altyapı - Üstyapı - Yapım'
 WHERE kategori = 'İnşaat & Yapım';

-- 3) Kuyruk indeksi: "sıradaki denenmemiş JENERİK satır" seçimi tablo büyüse de anlık kalsın.
--    Predicate IN-listesi (IMMUTABLE) + ai_kategori_denendi IS NULL → yalnız kuyruktakileri indeksler.
--    Eski dar indeks (yalnız 'Diğer') düşürülür — bu genişi onu kapsar.
DROP INDEX IF EXISTS public.idx_ilanlar_ai_kategori_kuyruk;
CREATE INDEX IF NOT EXISTS idx_ilanlar_ai_kategori_kuyruk_jenerik
  ON public.ilanlar (id)
  WHERE kategori IN ('Diğer', 'Mal Alımı', 'Hizmet Alımı') AND ai_kategori_denendi IS NULL;

NOTIFY pgrst, 'reload schema';

-- Doğrulama (elle):
--   SELECT kategori, count(*) FROM ilanlar
--     WHERE kategori IN ('Diğer','Mal Alımı','Hizmet Alımı') AND ai_kategori_denendi IS NULL
--     GROUP BY kategori ORDER BY 2 DESC;                    -- kuyruk kırılımı
--   SELECT count(*) FROM ilanlar WHERE kategori = 'İnşaat & Yapım';   -- 0 olmalı (birleşti)
