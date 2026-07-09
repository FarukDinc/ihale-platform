-- ============================================================
-- SONUÇ VERİSİ — çok kısımlı (lot) ihale desteği (9 Tem 2026, ÖNCELİK 10 Faz A2)
-- Bir ihalede birden fazla kazanan/kısım olabilir (sozlesmeBilgiList birden fazla eleman).
-- ekap_sonuc_backfill.py artık her kısmı ayrı satır yazıyor; bunun için (ilan_id, kisim_no)
-- birleşik anahtar gerekiyor. NON-DESTRUCTIVE: mevcut satırlar kisim_no=1 alır.
-- Çalıştır: VDS psql -f  VE  managed Supabase SQL Editor (cutover'a dek ikisinde de).
-- ============================================================

BEGIN;

ALTER TABLE ihale_sonuclari
  ADD COLUMN IF NOT EXISTS kisim_no INTEGER NOT NULL DEFAULT 1;

-- ilan_id tek başına PK/UNIQUE idiyse onu (ilan_id, kisim_no) birleşimine genişlet.
-- Önce olası eski tekil kısıtı bul ve kaldır (isim ortamlar arası değişebildiği için pg_constraint'ten sorgula).
DO $$
DECLARE
  con_name text;
BEGIN
  SELECT conname INTO con_name
  FROM pg_constraint
  WHERE conrelid = 'ihale_sonuclari'::regclass
    AND contype IN ('p', 'u')
    AND array_length(conkey, 1) = 1
    AND conkey = ARRAY[(SELECT attnum FROM pg_attribute
                         WHERE attrelid = 'ihale_sonuclari'::regclass AND attname = 'ilan_id')]
  LIMIT 1;

  IF con_name IS NOT NULL THEN
    EXECUTE format('ALTER TABLE ihale_sonuclari DROP CONSTRAINT %I', con_name);
  END IF;
END $$;

CREATE UNIQUE INDEX IF NOT EXISTS idx_ihale_sonuclari_ilan_kisim
  ON ihale_sonuclari (ilan_id, kisim_no);

COMMIT;

NOTIFY pgrst, 'reload schema';
