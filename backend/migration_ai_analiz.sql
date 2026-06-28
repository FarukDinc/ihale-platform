-- İhalePlatform — AI Analiz kolonları
-- Çalıştırma: Supabase Dashboard → SQL Editor

ALTER TABLE ilanlar
  ADD COLUMN IF NOT EXISTS yapay_zeka_ozeti  text,
  ADD COLUMN IF NOT EXISTS analiz_tarihi     timestamptz,
  ADD COLUMN IF NOT EXISTS analiz_pdf_turu   text;   -- 'ilan_metni' | 'pdf_vision'

COMMENT ON COLUMN ilanlar.yapay_zeka_ozeti IS 'Gemini AI şartname analizi — formatlanmış markdown';
COMMENT ON COLUMN ilanlar.analiz_tarihi     IS 'AI analizinin yapıldığı tarih';
COMMENT ON COLUMN ilanlar.analiz_pdf_turu   IS 'Analizin kaynağı: ilan_metni veya pdf_vision';

-- ilk_gorulme: gerçek "yeni kayıt" takibi için
-- (olusturulma her upsert'te güncellenir, ilk_gorulme yalnız INSERT'te set edilir)
ALTER TABLE ilanlar
  ADD COLUMN IF NOT EXISTS ilk_gorulme timestamptz DEFAULT NOW();

-- Mevcut kayıtlara olusturulma değerini kopyala (geçmiş veri)
UPDATE ilanlar SET ilk_gorulme = olusturulma WHERE ilk_gorulme IS NULL;

COMMENT ON COLUMN ilanlar.ilk_gorulme IS 'İlk kez DB''ye yazıldığı tarih — upsert''te değişmez';
