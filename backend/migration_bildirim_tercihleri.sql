-- Bildirim tercihleri — profil tablosuna kullanıcı opt-in kolonları
-- notify.py bunları okur (e-posta bildirimi açık kullanıcıları seçmek için).
-- ADDITIVE + güvenli defaults: kimse opt-in olmadan mail gönderilmez.
-- Supabase SQL Editor'da (veya VDS psql) çalıştır.

ALTER TABLE profil
  ADD COLUMN IF NOT EXISTS bildirim_email      BOOLEAN NOT NULL DEFAULT false,  -- e-posta bildirimi açık mı
  ADD COLUMN IF NOT EXISTS bildirim_son_teklif BOOLEAN NOT NULL DEFAULT true,   -- son teklif tarihi yaklaşınca uyar
  ADD COLUMN IF NOT EXISTS bildirim_gun_oncesi INTEGER NOT NULL DEFAULT 3;      -- kaç gün önceden uyarılsın

-- PostgREST şema cache'ini yenile (yeni kolonlar API'de görünsün)
NOTIFY pgrst, 'reload schema';
