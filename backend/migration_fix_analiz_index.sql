-- İhalePlatform — idx_ilanlar_analiz btree index hatası düzeltme
-- Hata: "index row size 2712 exceeds btree version 4 maximum 2704"
-- Çözüm: Büyük text alanı üzerindeki btree index'i kaldır
-- Çalıştırma: Supabase Dashboard → SQL Editor

-- Problematik index'i kaldır
DROP INDEX IF EXISTS idx_ilanlar_analiz;

-- Gerekirse: analiz_tarihi üzerine küçük/hızlı bir index (isteğe bağlı)
CREATE INDEX IF NOT EXISTS idx_ilanlar_analiz_tarihi ON ilanlar (analiz_tarihi);
