-- migration_sonuc_checkpoint_kurtarma.sql
--
-- AMAC: ekap_sonuc_scraper.py'deki "checkpoint veriden once" hatasinin (B3)
-- GECMISTE yol actigi sessiz kaybi kurtarmak. O hata yuzunden bazi ihaleler
-- scrape_log'da basarili=TRUE damgalandi ama ihale_sonuclari'na hic yazilmadi
-- (gather sonrasi in-memory flush kesildi ya da batch yazma hata verdi).
-- islenmemis_ihaleler() basarili=TRUE'lari haric tuttugu icin bu ihaleler bir
-- daha CEKILMIYOR. Asagidaki UPDATE, verisi olmayan bu "yetim" checkpoint'leri
-- basarili=FALSE'a cevirir; boylece bir sonraki normal turda (ve --retry-failed
-- ile) tekrar cekilirler. Kod tarafi artik once-veri-sonra-checkpoint yazdigi
-- icin bu tekrar guvenli.
--
-- IDEMPOTENT: birden fazla kez calistirilabilir; sadece verisi olmayan TRUE
-- satirlari etkiler. NOT EXISTS kullanildi (NOT IN + NULL tuzagindan kacinmak
-- icin).
--
-- ONCE ETKIYI GOR (opsiyonel, sadece okur):
--   SELECT count(*) AS kurtarilacak
--   FROM scrape_log sl
--   WHERE sl.basarili = true
--     AND NOT EXISTS (SELECT 1 FROM ihale_sonuclari s WHERE s.ekap_id = sl.ekap_id);

-- ⛔ 21 Tem — UYGULANMADI, İKİ SEBEP (ölçümle doğrulandı):
--   (1) NO-OP: scrape_log'da başarılı=true kayıt YOK (ekap_sonuc_scraper.py prod'da hiç
--       koşmamış; ihale_sonuclari'nı ekap_sonuc_backfill.py dolduruyor, ilan_id anahtarıyla).
--   (2) BOZUK JOIN: aşağıdaki NOT EXISTS `s.ekap_id = sl.ekap_id` ile eşleştiriyor ama
--       ihale_sonuclari.ekap_id TÜM satırlarda NULL (ilanlar_sonuc view'ındaki aynı bozuk
--       join — bkz. migration_sonucjoin_fix.sql). scrape_log dolu OLSAYDI bu NOT EXISTS her
--       satırda true olur ve TÜM başarılı kayıtları false'a çevirirdi (devasa gereksiz
--       yeniden çekim). Doğru anahtar ilan_id/ihale_id olmalı.
-- Bu blok, hem NO-OP olduğu hem de join'i düzeltilmeden GÜVENLİ olmadığı için ABORT guard'lı.
-- ekap_sonuc_scraper.py ileride prod'a alınırsa: önce join'i ilan_id'ye çevir, sonra bu guard'ı kaldır.
DO $$
BEGIN
  RAISE EXCEPTION 'ABORT: bu kurtarma NO-OP ve join''i bozuk (ihale_sonuclari.ekap_id NULL). Uygulanmadan once ilan_id anahtarina cevir. Bkz. dosya basi.';
END $$;

BEGIN;

UPDATE scrape_log sl
SET basarili    = false,
    hata_mesaji = 'kurtarma: checkpoint TRUE idi ama ihale_sonuclari kaydi yok (sessiz kayip B3)'
WHERE sl.basarili = true
  AND sl.ekap_id IS NOT NULL
  AND NOT EXISTS (
        SELECT 1 FROM ihale_sonuclari s WHERE s.ekap_id = sl.ekap_id
  );

COMMIT;
