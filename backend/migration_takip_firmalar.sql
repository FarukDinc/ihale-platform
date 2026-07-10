-- ============================================================
-- İhalePlatform — Faz E1: Rakip Takibi
--
-- Kullanıcı bir firmayı (yükleniciyi) "takip"e alabilir; rakip_bildirim.py
-- (gece cron, ekap_sonuc_backfill.py'den SONRA) yeni bir ihale_sonuclari
-- satırında takip edilen firma kazanan çıkarsa bildirimler'e kayıt açar.
--
-- firma_ad ham metin (normalize_ad DEĞİL) — firma-analiz.html zaten ILIKE
-- '%FIRMA%' ile aradığı için burada da aynı basit substring eşleşmesi
-- kullanılıyor (rakip_bildirim.py'deki esleşiyor() fonksiyonu).
--
-- Çalıştırma: docker exec -i supabase-db psql -U postgres -d postgres < backend/migration_takip_firmalar.sql
-- ============================================================

BEGIN;

CREATE TABLE IF NOT EXISTS public.takip_firmalar (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  kullanici_id  UUID NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
  firma_ad      TEXT NOT NULL,
  olusturulma   TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (kullanici_id, firma_ad)
);

ALTER TABLE public.takip_firmalar ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "takip_firmalar_kendi_okur"  ON public.takip_firmalar;
DROP POLICY IF EXISTS "takip_firmalar_kendi_ekler"  ON public.takip_firmalar;
DROP POLICY IF EXISTS "takip_firmalar_kendi_siler"  ON public.takip_firmalar;

CREATE POLICY "takip_firmalar_kendi_okur" ON public.takip_firmalar
  FOR SELECT USING (auth.uid() = kullanici_id);

CREATE POLICY "takip_firmalar_kendi_ekler" ON public.takip_firmalar
  FOR INSERT WITH CHECK (auth.uid() = kullanici_id);

CREATE POLICY "takip_firmalar_kendi_siler" ON public.takip_firmalar
  FOR DELETE USING (auth.uid() = kullanici_id);

GRANT SELECT, INSERT, DELETE ON public.takip_firmalar TO authenticated;

NOTIFY pgrst, 'reload schema';

COMMIT;

-- Kontrol
SELECT policyname, cmd, qual FROM pg_policies WHERE tablename = 'takip_firmalar';
