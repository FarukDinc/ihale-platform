-- ============================================================
-- İhalePlatform — Bildirim Sistemi Migrasyonu
-- Çalıştırma: Supabase Dashboard → SQL Editor
-- ============================================================

-- 1) Takip tablosu (localStorage yerine DB'de)
CREATE TABLE IF NOT EXISTS takip (
  id         uuid DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id    uuid REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
  ilan_id    uuid REFERENCES ilanlar(id)    ON DELETE CASCADE NOT NULL,
  created_at timestamptz DEFAULT now(),
  UNIQUE(user_id, ilan_id)
);

ALTER TABLE takip ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users manage own takip" ON takip;
CREATE POLICY "Users manage own takip" ON takip
  FOR ALL USING (auth.uid() = user_id);

-- Hızlı sorgu için index
CREATE INDEX IF NOT EXISTS takip_user_id_idx ON takip(user_id);
CREATE INDEX IF NOT EXISTS takip_ilan_id_idx ON takip(ilan_id);


-- 2) Bildirimler tablosu (in-app + e-posta logu)
CREATE TABLE IF NOT EXISTS bildirimler (
  id         uuid DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id    uuid REFERENCES auth.users(id) ON DELETE CASCADE NOT NULL,
  tip        text NOT NULL CHECK (tip IN ('ihale','sistem','email')),
  baslik     text NOT NULL,
  aciklama   text,
  ilan_id    uuid REFERENCES ilanlar(id) ON DELETE SET NULL,
  okunmus    boolean DEFAULT false,
  email_gonderildi boolean DEFAULT false,
  created_at timestamptz DEFAULT now()
);

ALTER TABLE bildirimler ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Users see own bildirimler" ON bildirimler;
CREATE POLICY "Users see own bildirimler" ON bildirimler
  FOR ALL USING (auth.uid() = user_id);

-- Service role insert için (notify.py kullanır)
DROP POLICY IF EXISTS "Service insert bildirimler" ON bildirimler;
CREATE POLICY "Service insert bildirimler" ON bildirimler
  FOR INSERT WITH CHECK (true);

CREATE INDEX IF NOT EXISTS bildirimler_user_id_idx ON bildirimler(user_id);
CREATE INDEX IF NOT EXISTS bildirimler_okunmus_idx  ON bildirimler(user_id, okunmus);


-- 3) Profil tablosuna bildirim tercihleri
ALTER TABLE profil
  ADD COLUMN IF NOT EXISTS bildirim_son_teklif  boolean DEFAULT true,
  ADD COLUMN IF NOT EXISTS bildirim_yeni_ihale  boolean DEFAULT true,
  ADD COLUMN IF NOT EXISTS bildirim_email       boolean DEFAULT false,
  ADD COLUMN IF NOT EXISTS bildirim_gun_oncesi  integer DEFAULT 3;  -- kaç gün kala uyarsın

-- ============================================================
-- Kontrol
SELECT 'takip tablosu OK'      FROM pg_tables WHERE tablename = 'takip'      LIMIT 1;
SELECT 'bildirimler tablosu OK' FROM pg_tables WHERE tablename = 'bildirimler' LIMIT 1;
