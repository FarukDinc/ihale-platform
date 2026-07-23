-- ilanlar'a EKAP iç ihale kimliği (64-hane hash) — rakip yol haritası #4 "Şartname/ilan belge erişimi".
--
-- SORUN: EKAP'ın resmî doküman sayfası (VatandasIlanGoruntuleme.aspx) İKN ile DEĞİL, EKAP'ın
-- iç `ihaleId` hash'iyle açılıyor. Bu hash'i hiç saklamıyorduk → 1,96M ilandan yalnız 1.436'sında
-- belge linki vardı (o da detay turunda `belgeler` jsonb'ına düşenler).
--
-- ÇÖZÜM: hash zaten liste yanıtında (`item["id"]`) GELİYOR, `ihaleleri_isle` onu sadece ekap_id
-- için yedek olarak kullanıp atıyordu. Kolona yazmak EK İSTEK MALİYETİ GETİRMEZ — bedava.
-- Böylece her ilan için belge sayfasına doğrudan link üretilebilir (indirme/CAPTCHA/Storage YOK).
--
-- Geçmiş satırlar: liste API'si (sayfa başı ~55 KB, detay çağrısı yok) ile ucuz doldurulabilir;
-- ⛔ ayrı bir tur olarak, gece cron'uyla ÇAKIŞMADAN (aynı anda tek ağır proxy işi kuralı).
ALTER TABLE public.ilanlar ADD COLUMN IF NOT EXISTS ekap_ihale_id text;

-- Misafir de belge linkini görebilsin: hash hassas veri değil, EKAP'ın kendi genel sayfasının anahtarı.
-- ⚠️ Sonradan eklenen kolon kolon-GRANT'a girmez → anon'da 42501 ile sayfayı öldürür (bkz. anon maske dersi).
GRANT SELECT (ekap_ihale_id) ON public.ilanlar TO anon;

-- Backfill'in "eksik olanı bul" sorgusu için (yalnız NULL olanları indeksle — küçük kalır).
CREATE INDEX IF NOT EXISTS idx_ilanlar_ekap_ihale_id_eksik
    ON public.ilanlar (ikn) WHERE ekap_ihale_id IS NULL AND kaynak = 'ekap';

NOTIFY pgrst, 'reload schema';
