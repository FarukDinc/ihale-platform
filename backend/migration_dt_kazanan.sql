-- ============================================================================
-- migration_dt_kazanan.sql — Doğrudan Temin kazanan firma + bedel altyapısı (18 Tem 2026)
--
-- ARKA PLAN: DT sonuç verisi (kazanan firma/bedel) EKAP'ta CAPTCHA arkasında
-- SANILIYORDU (bkz. hafıza: dt-kazanan-captcha). 18 Tem'de canlı doğrulandı: CAPTCHA
-- yalnız HTML sayfasını (DogrudanTeminDetay.aspx) korur; Angular'ın veriyi çektiği
-- ASIL JSON API'si (YeniIhaleAramaData.ashx?metot=dtDetayGetir) TAMAMEN AÇIK —
-- hiç CAPTCHA çözmeden, kimliksiz bir httpx oturumundan bile E10/E11 (dogrudanTeminId/
-- IdareId) ile doğrudan çağrılabiliyor (canlı test: 0 CAPTCHA, 100% başarı — bkz.
-- YAPILACAKLAR.md). Gemini/CAPTCHA-çözme altyapısı GEREKMİYOR — dtAra listesindeki
-- E10/E11'in dt_kazanan_scraper.py'de düz GET'e çevrilmesi yeterli.
--
-- Akış: dtAra liste yanıtındaki E10 (dogrudanTeminId) + E11 (IdareId) token'ları
-- şimdiye dek ATILIYORDU (ekap_dogrudan_temin_scraper.py saklamıyordu) — bu
-- migration hem saklama alanını açıyor hem yeni sonuç tablosunu kuruyor.
--
-- Çalıştır: docker exec -i supabase-db psql -U postgres -d postgres < backend/migration_dt_kazanan.sql
-- Idempotent: IF NOT EXISTS / CREATE OR REPLACE. Tekrarı zararsız.
-- ============================================================================

BEGIN;

-- 1) dogrudan_temin_ilanlari: E10/E11/E13/E14 token'ları (detay/sonuç sayfası erişimi için).
--    dt_ihale_token/dt_idare_token BİLİNÇLİ anon+authenticated'a KAPALI (sadece service_role) —
--    bunlar frontend'in hiç ihtiyaç duymadığı, yalnızca scraper'ın DogrudanTeminDetay.aspx
--    URL'i kurmak için kullandığı dahili EKAP token'ları (kolon-grant EKLENMEDİĞİ için
--    Postgres'te varsayılan KAPALI kalır — migration_anon_maske.sql'in dinamik "idare hariç
--    hepsi" listesine de eklenmemeleri için o dosyaya ayrı bir REVOKE eklendi, aşağıda not).
ALTER TABLE public.dogrudan_temin_ilanlari
  ADD COLUMN IF NOT EXISTS dt_ihale_token   TEXT,      -- E10 (dogrudanTeminId, şifreli)
  ADD COLUMN IF NOT EXISTS dt_idare_token   TEXT,      -- E11 (IdareId, şifreli)
  ADD COLUMN IF NOT EXISTS dt_ilan_var_mi   BOOLEAN,   -- E13
  ADD COLUMN IF NOT EXISTS dt_dosya_var_mi  BOOLEAN,   -- E14
  ADD COLUMN IF NOT EXISTS kazanan_denendi  TIMESTAMPTZ;  -- yuklenici_yenile/ai_kategori_denendi deseniyle
                                                            -- aynı: bir kez denenen dt_no bir daha seçilmez
                                                            -- (başarısız da olsa — CAPTCHA/veri yoksa tekrar
                                                            -- denemek anlamsız token israfı olurdu).

-- durum bazlı KPI sayımları (dashboard) + "sonuç grubu" kuyruk seçimi için — tablo 1.48M
-- satır, indekssiz count(*) WHERE durum IN (...) Statement Timeout Edge riski taşır.
CREATE INDEX IF NOT EXISTS idx_dt_ilanlari_durum ON public.dogrudan_temin_ilanlari (durum);

-- Kazanan-scraper kuyruğu: token'ı olan + henüz denenmemiş satırlar (81 il × büyük hacim
-- ama bu partial index kuyruğu küçük tutar — token'sız/denenmiş satırlar hiç görünmez).
CREATE INDEX IF NOT EXISTS idx_dt_ilanlari_kazanan_kuyruk
  ON public.dogrudan_temin_ilanlari (dt_no)
  WHERE dt_ihale_token IS NOT NULL AND kazanan_denendi IS NULL;

-- 2) Yeni tablo: dogrudan_temin_sonuclari — bir dt_no'nun BİRDEN FAZLA sözleşme kalemi
--    olabilir (EKAP'ın SozlesmeBilgisiList dizisi) → satır-başına-kalem, ihale_sonuclari'nin
--    kısım/lot modeliyle aynı fikir. enc_sozlesme_id EKAP'ın kendi tekil anahtarı (upsert için).
CREATE TABLE IF NOT EXISTS public.dogrudan_temin_sonuclari (
  id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  dt_no              TEXT NOT NULL,                 -- dogrudan_temin_ilanlari.dt_no (FK yok — scraper sırası garanti değil)
  enc_sozlesme_id    TEXT UNIQUE,                    -- EKAP EncSozlesmeID — NULL olabilir (bazı eski kayıtlarda yok), o zaman upsert dt_no+kazanan_bedel ile dedup edilir
  kazanan_firma      TEXT,                           -- IstekliAdi
  kazanan_bedel      NUMERIC,                        -- SozlesmeBedeli (bedel_parse ile ayrıştırılmış)
  sozlesme_tarihi    TIMESTAMPTZ,                    -- SozlesmeTarihi
  en_yuksek_teklif   NUMERIC,
  en_dusuk_teklif    NUMERIC,
  sozlesme_mi        BOOLEAN,                        -- true=sözleşmeli, false=alım (SozlesmeVeyaAlimBilgisi)
  yuklenici_id       UUID,                           -- İLERİDE doldurulur (ayrı normalize_firma eşleme turu —
                                                       -- YUKLENICILER'E BİLEREK HENÜZ KARIŞTIRILMIYOR, bkz. hafıza
                                                       -- dt-kazanan-captcha: "ihale cirosuna karıştırma" kararı)
  olusturulma        TIMESTAMPTZ NOT NULL DEFAULT now(),
  guncellenme        TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_dt_sonuc_dt_no         ON public.dogrudan_temin_sonuclari (dt_no);
CREATE INDEX IF NOT EXISTS idx_dt_sonuc_kazanan_firma ON public.dogrudan_temin_sonuclari (kazanan_firma) WHERE kazanan_firma IS NOT NULL;

ALTER TABLE public.dogrudan_temin_sonuclari ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "dt_sonuc_herkes_okur" ON public.dogrudan_temin_sonuclari;
CREATE POLICY "dt_sonuc_herkes_okur" ON public.dogrudan_temin_sonuclari FOR SELECT USING (true);

-- Anon maskeleme: kazanan_firma + yuklenici_id KAPALI (kimlik), bedel/tarih/sayılar AÇIK
-- (ihale_sonuclari ile AYNI ilke — "Sayılar/tarihler misafire açık, kimlik kapalı").
--
-- REVOKE ŞART — atlanırsa kolon-GRANT DEKORATİF kalır: self-hosted Supabase'de
-- "ALTER DEFAULT PRIVILEGES ... GRANT ALL ON TABLES TO anon" yürürlükte olduğu için
-- yeni tablo doğuştan tablo-geneli anon SELECT'e sahiptir; kolon-GRANT yetkiyi
-- daraltmaz, ekler. (Bu satır ilk sürümde unutuldu → migration_dt_anon_fix.sql)
REVOKE SELECT ON public.dogrudan_temin_sonuclari FROM anon;
GRANT SELECT (
  id, dt_no, kazanan_bedel, sozlesme_tarihi, en_yuksek_teklif, en_dusuk_teklif,
  sozlesme_mi, olusturulma
) ON public.dogrudan_temin_sonuclari TO anon;
GRANT SELECT ON public.dogrudan_temin_sonuclari TO authenticated;
GRANT SELECT, INSERT, UPDATE ON public.dogrudan_temin_sonuclari TO service_role;

COMMIT;

NOTIFY pgrst, 'reload schema';

-- Doğrulama (elle):
--   SELECT count(*) FROM dogrudan_temin_ilanlari WHERE dt_ihale_token IS NOT NULL;  -- retrofit sonrası artmalı
--   SET ROLE anon; SELECT kazanan_firma FROM dogrudan_temin_sonuclari LIMIT 1;      -- 42501 (insufficient_privilege) beklenir
--   RESET ROLE;
