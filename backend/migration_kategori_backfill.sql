-- İhalePlatform — Kategori backfill (mevcut kayıtlar için)
-- Çalıştırma: Supabase Dashboard → SQL Editor
-- NOT: Önce migration_ai_analiz.sql çalıştırılmış olmalı (ilk_gorulme + analiz kolonları)

-- 1. OKAS kodunun ilk 2 hanesiyle kategori eşleştir
UPDATE ilanlar
SET kategori = CASE LEFT(REGEXP_REPLACE(COALESCE(okas, ''), '[^0-9]', '', 'g'), 2)
  WHEN '03' THEN 'Tarım & Ormancılık'
  WHEN '09' THEN 'Enerji'
  WHEN '14' THEN 'Madencilik'
  WHEN '15' THEN 'Gıda & İçecek'
  WHEN '16' THEN 'Tarım Makineleri'
  WHEN '18' THEN 'Giyim & Tekstil'
  WHEN '19' THEN 'Deri & Kauçuk'
  WHEN '22' THEN 'Basın & Yayın'
  WHEN '24' THEN 'Kimyasal Ürünler'
  WHEN '30' THEN 'BT Ekipmanları'
  WHEN '31' THEN 'Elektrik Malzemeleri'
  WHEN '32' THEN 'İletişim'
  WHEN '33' THEN 'Tıbbi Cihazlar'
  WHEN '34' THEN 'Ulaşım Araçları'
  WHEN '35' THEN 'Güvenlik'
  WHEN '37' THEN 'Spor & Eğlence'
  WHEN '38' THEN 'Labaratuvar'
  WHEN '39' THEN 'Mobilya & Temizlik'
  WHEN '41' THEN 'Su'
  WHEN '42' THEN 'Sanayi Makineleri'
  WHEN '43' THEN 'Madencilik Ekipmanı'
  WHEN '44' THEN 'İnşaat Malzemeleri'
  WHEN '45' THEN 'İnşaat & Yapım'
  WHEN '48' THEN 'Yazılım'
  WHEN '50' THEN 'Bakım & Onarım'
  WHEN '51' THEN 'Montaj'
  WHEN '55' THEN 'Konaklama & Yemek'
  WHEN '60' THEN 'Ulaşım Hizmetleri'
  WHEN '63' THEN 'Lojistik'
  WHEN '64' THEN 'Posta & İletişim'
  WHEN '65' THEN 'Kamu Hizmetleri'
  WHEN '66' THEN 'Sigorta & Finans'
  WHEN '70' THEN 'Gayrimenkul'
  WHEN '71' THEN 'Mimarlık & Mühendislik'
  WHEN '72' THEN 'Bilişim Hizmetleri'
  WHEN '73' THEN 'Ar-Ge'
  WHEN '75' THEN 'Kamu Yönetimi'
  WHEN '76' THEN 'Petrol & Gaz'
  WHEN '77' THEN 'Bahçe & Çevre'
  WHEN '79' THEN 'İdari Hizmetler'
  WHEN '80' THEN 'Eğitim'
  WHEN '85' THEN 'Sağlık'
  WHEN '90' THEN 'Çevre Hizmetleri'
  WHEN '92' THEN 'Kültür & Medya'
  WHEN '98' THEN 'Diğer Hizmetler'
  ELSE NULL
END
WHERE kategori IS NULL AND okas IS NOT NULL AND okas <> '';

-- 2. OKAS yoksa ihale türünden türet
UPDATE ilanlar SET kategori = 'İnşaat & Yapım'
WHERE kategori IS NULL AND tur = 'Yapım';

-- 3. Kaç kayıt güncellendi
SELECT kategori, COUNT(*) as adet
FROM ilanlar
WHERE kategori IS NOT NULL
GROUP BY kategori
ORDER BY adet DESC;
