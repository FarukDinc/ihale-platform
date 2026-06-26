-- İhale detay + yaklaşık maliyet kolonları
-- Supabase Dashboard → SQL Editor'a yapıştırıp bir kez çalıştır.

ALTER TABLE ilanlar
  ADD COLUMN IF NOT EXISTS itiraz_bedeli        numeric,
  ADD COLUMN IF NOT EXISTS yaklasik_maliyet_min bigint,
  ADD COLUMN IF NOT EXISTS yaklasik_maliyet_max bigint,
  ADD COLUMN IF NOT EXISTS isin_yapilacagi_yer  text,
  ADD COLUMN IF NOT EXISTS ihale_yeri           text,
  ADD COLUMN IF NOT EXISTS okas                 text,
  ADD COLUMN IF NOT EXISTS ilan_metni           text,
  ADD COLUMN IF NOT EXISTS belgeler             jsonb;
