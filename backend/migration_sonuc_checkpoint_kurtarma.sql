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
