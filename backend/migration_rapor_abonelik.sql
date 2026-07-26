-- ============================================================
-- RUTİN RAPOR ABONELİĞİ (#6) — 26 Tem 2026
-- "Raporunu oluştur, iş fırsatını kaçırma": kullanıcı rapor kriterini kaydeder →
-- gece cron her yeni eşleşen ihale/sonuç için bildirim + (tercihse) e-posta gönderir.
-- Mevcut bildirim/e-posta altyapısını (notify.py, bildirimler) yeniden kullanır. EXPORT DEĞİL.
-- ============================================================

CREATE TABLE IF NOT EXISTS public.rapor_abonelikleri (
  id           uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  kullanici_id uuid NOT NULL,
  ad           text NOT NULL,               -- kullanıcının verdiği rapor adı
  tip          text NOT NULL CHECK (tip IN ('ihale','sonuc')),
  kriter       jsonb NOT NULL DEFAULT '{}',  -- {kelime,il,kategori,min,durum}
  son_gonderim timestamptz,                  -- en son bildirim üretim anı (artımlı için)
  aktif        boolean DEFAULT true,
  olusturulma  timestamptz DEFAULT now()
);
ALTER TABLE public.rapor_abonelikleri ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "ra_kendi_okur"  ON public.rapor_abonelikleri;
DROP POLICY IF EXISTS "ra_kendi_ekler"  ON public.rapor_abonelikleri;
DROP POLICY IF EXISTS "ra_kendi_siler"  ON public.rapor_abonelikleri;
DROP POLICY IF EXISTS "ra_kendi_gunceller" ON public.rapor_abonelikleri;
CREATE POLICY "ra_kendi_okur"      ON public.rapor_abonelikleri FOR SELECT USING (auth.uid() = kullanici_id);
CREATE POLICY "ra_kendi_ekler"     ON public.rapor_abonelikleri FOR INSERT WITH CHECK (auth.uid() = kullanici_id);
CREATE POLICY "ra_kendi_siler"     ON public.rapor_abonelikleri FOR DELETE USING (auth.uid() = kullanici_id);
CREATE POLICY "ra_kendi_gunceller" ON public.rapor_abonelikleri FOR UPDATE USING (auth.uid() = kullanici_id);
GRANT SELECT, INSERT, DELETE, UPDATE ON public.rapor_abonelikleri TO authenticated;
GRANT SELECT, UPDATE                 ON public.rapor_abonelikleri TO service_role;  -- gece cron okur+son_gonderim yazar
-- anon'a GRANT YOK (varsayılan REVOKE).

CREATE INDEX IF NOT EXISTS ix_rapor_abonelik_aktif ON public.rapor_abonelikleri (aktif) WHERE aktif;

NOTIFY pgrst, 'reload schema';
