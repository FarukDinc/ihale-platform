-- ============================================================================
-- migration_ai_kategori.sql — AI kategori backfill işaret kolonu (16 Tem 2026)
--
-- Amaç: OKAS'sız + kelime kurallarının çözemediği "Diğer" ilanları Gemini ile
-- 41 kanonik kategoriden birine oturtmak. TASARIM İLKESİ: her satır ömründe YALNIZCA
-- BİR KEZ AI'a gider; sonucu (kategori değişse de değişmese de) burada işaretlenir ve
-- bir daha asla sorulmaz → idempotent, tekrar-çalıştırma token israfı YOK.
--
-- ai_kategori_denendi:
--   NULL           → hiç denenmedi (kuyrukta).
--   <zaman damgası> → denendi. Kategori spesifik olduysa satır zaten 'Diğer' değil
--                     (doğal olarak kuyruk dışı); 'Diğer' kaldıysa da bu damga tekrar
--                     seçilmesini engeller. Taksonomi ileride büyürse damgayı bir
--                     kesim tarihinden eskiler için NULL'layıp yeniden denetebiliriz.
--
-- Çalıştır: docker exec -i supabase-db psql -U postgres -d postgres < backend/migration_ai_kategori.sql
-- Idempotent: ADD COLUMN IF NOT EXISTS / CREATE INDEX IF NOT EXISTS.
-- ============================================================================

ALTER TABLE public.ilanlar
  ADD COLUMN IF NOT EXISTS ai_kategori_denendi timestamptz;

COMMENT ON COLUMN public.ilanlar.ai_kategori_denendi IS
  'ai_kategori_backfill.py bu satiri Gemini''ye sordu (zaman damgasi). NULL=hic denenmedi. '
  'Bir kez denenen satir (sonuc Diger kalsa bile) tekrar sorulmaz -> idempotent, token israfi yok.';

-- Kısmi indeks: "sıradaki denenmemiş Diğer" seçimi tablo büyüse de anlık kalsın.
-- Predicate sabit-eşitlik (IMMUTABLE); yalnızca kuyruktaki satırları indeksler → küçük kalır.
CREATE INDEX IF NOT EXISTS idx_ilanlar_ai_kategori_kuyruk
  ON public.ilanlar (id)
  WHERE kategori = 'Diğer' AND ai_kategori_denendi IS NULL;

-- Yeni kolon PostgREST şemasına girsin (service_role PATCH ile yazacak; kolon ilanlar'ın
-- mevcut grant'ını miras alır — ek grant gerekmez).
NOTIFY pgrst, 'reload schema';

-- Doğrulama (elle):
--   SELECT count(*) FROM ilanlar WHERE kategori = 'Diğer' AND ai_kategori_denendi IS NULL;  -- kuyruk boyu
--   SELECT count(*) FROM ilanlar WHERE ai_kategori_denendi IS NOT NULL;                     -- denenmiş toplam
