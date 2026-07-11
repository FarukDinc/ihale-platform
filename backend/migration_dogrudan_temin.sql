-- ============================================================
-- İhaleGlobal — Doğrudan Temin İlanları
--
-- EKAP'ın (eski/legacy domain) Doğrudan Temin Duyuru Sayfası zaten canlı ve
-- herkese açık veri sunuyor (ekap.kik.gov.tr/EKAP/YeniIhaleArama.aspx?dt=true,
-- endpoint: Ortak/YeniIhaleAramaData.ashx?metot=dtAra — 12 Tem 2026'da
-- doğrulandı, oturum gerektirmiyor). ekapv2'deki "yeni pilot" (17 Tem 2026)
-- ile KARIŞTIRILMASIN — bu, o pilottan BAĞIMSIZ, hâlihazırda var olan sistem.
--
-- Rekabetçi ihalelerden (ilanlar) farklı bir yaşam döngüsü olduğu için
-- (teklif/rekabet süreci yok, doğrudan alım) ayrı bir tabloda tutuluyor.
--
-- Çalıştırma: docker exec -i supabase-db psql -U postgres -d postgres < backend/migration_dogrudan_temin.sql
-- ============================================================

BEGIN;

CREATE TABLE IF NOT EXISTS public.dogrudan_temin_ilanlari (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  dt_no         TEXT NOT NULL UNIQUE,   -- EKAP DT No, örn "26DT1304013" (E1)
  baslik        TEXT,                    -- E2
  idare         TEXT,                    -- E3
  tur           TEXT,                    -- E4 çevrilmiş: Mal/Yapım/Hizmet/Danışmanlık
  il            TEXT,                    -- E12 çevrilmiş: standart il adı
  tarih         TIMESTAMPTZ,             -- E7 parse edilmiş
  durum         TEXT,                    -- E9 çevrilmiş (bkz. script'teki enumDtDurumlari)
  duyuru_var    BOOLEAN NOT NULL DEFAULT false,  -- E13
  dokuman_var   BOOLEAN NOT NULL DEFAULT false,  -- E14
  olusturulma   TIMESTAMPTZ NOT NULL DEFAULT now(),
  guncellenme   TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_dt_ilanlari_idare ON public.dogrudan_temin_ilanlari (idare);
CREATE INDEX IF NOT EXISTS idx_dt_ilanlari_tarih ON public.dogrudan_temin_ilanlari (tarih DESC);

ALTER TABLE public.dogrudan_temin_ilanlari ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "dt_ilanlari_herkes_okur" ON public.dogrudan_temin_ilanlari;
CREATE POLICY "dt_ilanlari_herkes_okur" ON public.dogrudan_temin_ilanlari
  FOR SELECT USING (true);

-- ilanlar ile aynı desen: anon+authenticated SELECT (herkese açık, EKAP'ta zaten
-- öyle), yazma sadece service_role (scraper).
GRANT SELECT ON public.dogrudan_temin_ilanlari TO anon;
GRANT SELECT ON public.dogrudan_temin_ilanlari TO authenticated;
GRANT SELECT, INSERT, UPDATE ON public.dogrudan_temin_ilanlari TO service_role;

NOTIFY pgrst, 'reload schema';

COMMIT;

-- Kontrol
SELECT policyname, cmd, qual FROM pg_policies WHERE tablename = 'dogrudan_temin_ilanlari';
