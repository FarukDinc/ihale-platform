-- İhalePlatform — Veri Temizlik Migration
-- Çalıştırma: Supabase Dashboard → SQL Editor

-- ─────────────────────────────────────────────
-- 1. İL NORMALIZE: Title Case → BÜYÜK HARF
--    DB standardı BÜYÜK HARF (İSTANBUL, ANKARA).
--    Birkaç seed kayıt Title Case idi.
-- ─────────────────────────────────────────────
UPDATE ilanlar
SET il = UPPER(il)
WHERE il IS NOT NULL AND il <> UPPER(il);

-- Sonuç: kaç kayıt düzeltildi
SELECT 'il_normalize' as islem, COUNT(*) as etkilenen
FROM ilanlar WHERE il IS NOT NULL AND il = UPPER(il);

-- ─────────────────────────────────────────────
-- 2. MOJIBAKE DÜZELTMESİ
--    UTF-8 karakterler Latin-1 olarak iki kez encode edilmiş kayıtlar.
--    Örüntü: 'Ä°' yerine 'İ', 'ÅŸ' yerine 'ş', vb.
--    PostgreSQL'de convert_from/encode ile düzeltme:
-- ─────────────────────────────────────────────

-- Önce mojibake olan kayıtları kontrol et:
SELECT COUNT(*) as mojibake_adet
FROM ilanlar
WHERE baslik ~ 'Ã|Ä|Å' OR idare ~ 'Ã|Ä|Å';

-- Düzeltme fonksiyonu (bir kez oluştur, sonra sil):
CREATE OR REPLACE FUNCTION fix_mojibake(s TEXT) RETURNS TEXT AS $$
BEGIN
  BEGIN
    RETURN convert_from(s::bytea, 'UTF8');
  EXCEPTION WHEN OTHERS THEN
    RETURN s;
  END;
END;
$$ LANGUAGE plpgsql IMMUTABLE;

-- NOT: PostgreSQL'de bytea cast text'i hex olarak alır.
-- Gerçek mojibake düzeltmesi için Python script'i daha güvenilir.
-- Bu migration il normalize içindir; mojibake için backend/mojibake_fix.py kullan.

-- Fonksiyonu temizle
DROP FUNCTION IF EXISTS fix_mojibake(TEXT);

-- ─────────────────────────────────────────────
-- 3. USUL NORMALIZE (eski kayıtlar)
--    Bazı kayıtlarda usul hâlâ ham EKAP enum içeriyor.
--    Örn: "TENDER_SEARCH.ENUMERATIONS.SEARCH_METHOD.OPEN"
-- ─────────────────────────────────────────────
UPDATE ilanlar SET usul = 'Açık İhale'
WHERE usul ILIKE '%OPEN%' AND usul NOT ILIKE '%kapandı%';

UPDATE ilanlar SET usul = 'Pazarlık Usulü'
WHERE usul ILIKE '%BARGAIN%';

UPDATE ilanlar SET usul = 'Belli İstekliler Arasında'
WHERE usul ILIKE '%CERTAIN_BIDDERS%' OR usul ILIKE '%AMONG_CERTAIN%';

UPDATE ilanlar SET usul = 'Doğrudan Temin'
WHERE usul ILIKE '%DIRECT_PROCUREMENT%';

UPDATE ilanlar SET usul = 'Tasarım Yarışması'
WHERE usul ILIKE '%DESIGN_COMPETITION%';

UPDATE ilanlar SET usul = 'Çerçeve Anlaşma'
WHERE usul ILIKE '%FRAMEWORK%';

-- Sonuç
SELECT usul, COUNT(*) FROM ilanlar
WHERE usul IS NOT NULL
GROUP BY usul ORDER BY COUNT(*) DESC LIMIT 15;
