-- ============================================================
-- İhaleGlobal — Kurum (İdare) Takibi
--
-- Kullanıcı bir idareyi (kurumu) "takip"e alabilir; idare_bildirim.py
-- (gece cron, gece scraper'ından SONRA) o idarenin yayınladığı YENİ bir
-- ilan bulursa takip eden kullanıcılara bildirimler'e kayıt açar + e-posta
-- gönderir (bildirim_email tercihi açıksa). takip_firmalar (Faz E1) ile
-- birebir aynı desen — bkz. migration_takip_firmalar.sql.
--
-- Çalıştırma: docker exec -i supabase-db psql -U postgres -d postgres < backend/migration_takip_idareler.sql
-- ============================================================

BEGIN;

CREATE TABLE IF NOT EXISTS public.takip_idareler (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  kullanici_id  UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  idare_ad      TEXT NOT NULL,
  olusturulma   TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (kullanici_id, idare_ad)
);

ALTER TABLE public.takip_idareler ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "takip_idareler_kendi_okur"  ON public.takip_idareler;
DROP POLICY IF EXISTS "takip_idareler_kendi_ekler"  ON public.takip_idareler;
DROP POLICY IF EXISTS "takip_idareler_kendi_siler"  ON public.takip_idareler;

CREATE POLICY "takip_idareler_kendi_okur" ON public.takip_idareler
  FOR SELECT USING (auth.uid() = kullanici_id);

CREATE POLICY "takip_idareler_kendi_ekler" ON public.takip_idareler
  FOR INSERT WITH CHECK (auth.uid() = kullanici_id);

CREATE POLICY "takip_idareler_kendi_siler" ON public.takip_idareler
  FOR DELETE USING (auth.uid() = kullanici_id);

GRANT SELECT, INSERT, DELETE ON public.takip_idareler TO authenticated;
GRANT SELECT, INSERT, DELETE ON public.takip_idareler TO service_role;

NOTIFY pgrst, 'reload schema';

COMMIT;

-- Kontrol
SELECT policyname, cmd, qual FROM pg_policies WHERE tablename = 'takip_idareler';
