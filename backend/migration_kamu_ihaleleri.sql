-- Kamu Kurumu İhaleleri — EKAP DIŞI kamu satınalma kaynakları (DMO, Jandarma) AYRI tablo.
-- Ana `ilanlar` (EKAP, 351K, embedding/eşleşme/RLS) KİRLENMESİN diye uluslararasi_ihaleler deseniyle
-- ayrı tutulur; bu kaynaklar seyrek alanlı (yaklaşık maliyet/OKAS yok) ve ayrı ekranda gösterilir.
-- kaynak: 'dmo' (Devlet Malzeme Ofisi) | 'jandarma' (J.Gn.K. vatandaş ihale sorgu).

CREATE TABLE IF NOT EXISTS public.kamu_ihaleleri (
  id                uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  kaynak            text NOT NULL,                 -- 'dmo' | 'jandarma'
  kaynak_id         text NOT NULL,                 -- DMO ihale no / Jandarma PSN token (dedup anahtarı)
  baslik            text,
  idare             text,                          -- DMO: talep eden kurum/başlık; Jandarma: birlik adı
  kategori          text,                          -- DMO: kendi kategori adı; Jandarma: keyword'den (opsiyonel)
  tur               text,                          -- Mal | Hizmet | Yapım (türetilebildiğinde)
  aciklama          text,                          -- Jandarma AÇIKLAMA / DMO ek konu
  talep_no          text,                          -- DMO Talep Takip Numarası
  ekap_referans     text,                          -- Jandarma açıklamasında geçen EKAP DT no (izleme/dedup)
  ilan_tarihi       timestamptz,
  son_teklif_tarihi timestamptz,
  orijinal_url      text,                          -- kaynak detay sayfası
  olusturulma       timestamptz NOT NULL DEFAULT now(),
  guncellenme       timestamptz NOT NULL DEFAULT now(),
  UNIQUE (kaynak, kaynak_id)
);

CREATE INDEX IF NOT EXISTS idx_kamu_ihale_kaynak ON public.kamu_ihaleleri (kaynak);
CREATE INDEX IF NOT EXISTS idx_kamu_ihale_tarih  ON public.kamu_ihaleleri (son_teklif_tarihi DESC NULLS LAST);
CREATE INDEX IF NOT EXISTS idx_kamu_ihale_olus   ON public.kamu_ihaleleri (olusturulma DESC);

ALTER TABLE public.kamu_ihaleleri ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "kamu_ihale_herkes_okur" ON public.kamu_ihaleleri;
CREATE POLICY "kamu_ihale_herkes_okur" ON public.kamu_ihaleleri
  FOR SELECT USING (true);

GRANT SELECT ON public.kamu_ihaleleri TO anon;
GRANT SELECT ON public.kamu_ihaleleri TO authenticated;
GRANT SELECT, INSERT, UPDATE ON public.kamu_ihaleleri TO service_role;

NOTIFY pgrst, 'reload schema';
