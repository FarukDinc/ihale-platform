-- Kayıtlı aramalar + okundu takibi → localStorage'dan DB'ye (rakip yol haritası #5 ve #6).
--
-- SORUN: her ikisi de yalnızca localStorage'daydı (`ihale_kayitli_aramalar_v1`,
-- `ihale_okundu_v1`) → cihaz değişince / tarayıcı temizlenince kayboluyor, telefon ile
-- masaüstü birbirini görmüyor. Rakipte bunlar hesaba bağlı.
--
-- TASARIM: localStorage KALIYOR (anlık arayüz + misafir desteği); DB arka planda senkron
-- kaynak. `yerel_id` yerel kaydın Date.now() anahtarını taşır → mevcut çağrı noktaları
-- (sil(id) vb.) değişmeden çalışır.

-- ── Kayıtlı aramalar ────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.kayitli_aramalar (
    id          uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id     uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    yerel_id    bigint,                       -- istemcideki Date.now() anahtarı
    ad          text NOT NULL,
    params      jsonb NOT NULL DEFAULT '{}',  -- mevcutFiltreleriOku() çıktısı
    olusturulma timestamptz NOT NULL DEFAULT now(),
    UNIQUE (user_id, yerel_id)                -- tekrarlı senkron kopya üretmesin
);
CREATE INDEX IF NOT EXISTS idx_kayitli_aramalar_user ON public.kayitli_aramalar (user_id, olusturulma DESC);

ALTER TABLE public.kayitli_aramalar ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS kayitli_aramalar_kendi ON public.kayitli_aramalar;
CREATE POLICY kayitli_aramalar_kendi ON public.kayitli_aramalar
    FOR ALL TO authenticated
    USING (user_id = auth.uid()) WITH CHECK (user_id = auth.uid());

-- ── Okundu takibi ───────────────────────────────────────────────────────────
CREATE TABLE IF NOT EXISTS public.ilan_okundu (
    user_id      uuid NOT NULL REFERENCES auth.users(id) ON DELETE CASCADE,
    ilan_id      uuid NOT NULL,               -- ilanlar.id (FK YOK: DT/dış kaynak id'si de düşebilir)
    okundu_tarih timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (user_id, ilan_id)
);
CREATE INDEX IF NOT EXISTS idx_ilan_okundu_user ON public.ilan_okundu (user_id, okundu_tarih DESC);

ALTER TABLE public.ilan_okundu ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS ilan_okundu_kendi ON public.ilan_okundu;
CREATE POLICY ilan_okundu_kendi ON public.ilan_okundu
    FOR ALL TO authenticated
    USING (user_id = auth.uid()) WITH CHECK (user_id = auth.uid());

-- ⛔ anon'a AÇILMAZ: kullanıcıya özel veri. Yeni tablo varsayılan ayrıcalıkla anon-açık
-- doğabiliyor (bkz. anon maske dersi A maddesi) → önce REVOKE, sonra authenticated'a ver.
REVOKE ALL ON public.kayitli_aramalar FROM anon;
REVOKE ALL ON public.ilan_okundu      FROM anon;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.kayitli_aramalar TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.ilan_okundu      TO authenticated;
-- service_role da ŞART: backend işleri (bülten üretimi, hesap silme temizliği, destek) bu
-- tablolara erişemezse sessizce 42501 yer. RLS'i zaten baypas eder, kısıtlayan tek şey GRANT'tı.
GRANT SELECT, INSERT, UPDATE, DELETE ON public.kayitli_aramalar TO service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.ilan_okundu      TO service_role;

NOTIFY pgrst, 'reload schema';
