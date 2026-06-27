-- ============================================================
-- İhalePlatform — Abonelik Alanları Migrasyonu
-- Çalıştırma: Supabase Dashboard → SQL Editor
-- ============================================================

-- profil tablosuna plan takip kolonları
ALTER TABLE profil
  ADD COLUMN IF NOT EXISTS plan               text    DEFAULT 'free',
  ADD COLUMN IF NOT EXISTS plan_baslangic     timestamptz,
  ADD COLUMN IF NOT EXISTS plan_bitis         timestamptz,
  ADD COLUMN IF NOT EXISTS iyzico_payment_id  text;

-- Plan değeri kısıtı
ALTER TABLE profil
  DROP CONSTRAINT IF EXISTS profil_plan_check;

ALTER TABLE profil
  ADD CONSTRAINT profil_plan_check CHECK (plan IN ('free','pro','kurumsal','enterprise','PRO'));

-- Hızlı sorgular için index
CREATE INDEX IF NOT EXISTS profil_plan_idx ON profil(plan);

-- ============================================================
-- Kontrol
SELECT user_id, plan FROM profil LIMIT 5;
