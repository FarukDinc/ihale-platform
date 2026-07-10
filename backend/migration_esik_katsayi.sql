-- Faz C4 — Sınır değer katsayısı (N)
-- Yapım işi ilanlarının ilan metninde geçer ("...sınır değer katsayısı (N) = 1,00").
-- ekap_scraper.py artık bunu ilan_metni'nden regex ile çıkarıp yazıyor (esik_katsayi_parse).
-- Bulunamayan ilanlarda (Mal/Hizmet, ya da metin parse edilemeyen Yapım ilanları) NULL kalır.
BEGIN;

ALTER TABLE ilanlar ADD COLUMN IF NOT EXISTS esik_katsayi NUMERIC;

COMMENT ON COLUMN ilanlar.esik_katsayi IS
  'Yapım işi sınır değer katsayısı (N), ilan metninden regex ile çıkarılır. Diğer ihale türlerinde ve parse edilemeyen kayıtlarda NULL.';

COMMIT;
