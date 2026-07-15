-- ilanlar.kaynak CHECK'ine 'ilan_gov' (Basın İlan Kurumu / ilan.gov.tr gazete ilanları) eklenir.
-- Kullanıcı talebi: EKAP dışında ilan.gov.tr'den de ihale çekilir; kaynak 'ekap' GÖSTERİLMEZ.
ALTER TABLE ilanlar DROP CONSTRAINT IF EXISTS ilanlar_kaynak_check;
ALTER TABLE ilanlar ADD CONSTRAINT ilanlar_kaynak_check
  CHECK (kaynak = ANY (ARRAY['ekap'::text, 'ozel'::text, 'uluslararasi'::text, 'ilan_gov'::text]));
