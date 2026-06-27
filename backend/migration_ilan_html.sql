-- İhalePlatform — İlan HTML alanı + belgeler JSON alanı
-- Çalıştırma: Supabase Dashboard → SQL Editor

ALTER TABLE ilanlar
  ADD COLUMN IF NOT EXISTS ilan_html text;

-- Mevcut ilan_metni'nden ilan_html oluşturma (geçmiş veri temizleme)
-- Eski data zaten html_temizle() ile işlenmiş, orijinal HTML yok
-- Sadece yeni scrape'lerden itibaren ilan_html dolacak

COMMENT ON COLUMN ilanlar.ilan_html IS 'EKAP veriHtml — orijinal HTML, frontend render eder';
