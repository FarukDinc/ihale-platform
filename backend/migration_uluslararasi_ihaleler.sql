-- Uluslararası ihaleler AYRI tablo — Türkiye analizlerine (ilanlar/firma/sektör/kurum) KARIŞMASIN.
-- Kullanıcı kararı: yurtdışı ihaleler ayrı bir ekranda gösterilecek, Türkiye sonuçlarını kirletmeyecek.
-- Kaynak: TED Europa (AB), ileride Gürcistan vb. Veriler TÜRKÇE'ye çevrilerek saklanır.

CREATE TABLE IF NOT EXISTS public.uluslararasi_ihaleler (
  id               uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  kaynak           text NOT NULL DEFAULT 'ted',          -- 'ted' | 'georgia' | ...
  publication_no   text UNIQUE NOT NULL,                  -- TED publication-number (dedup anahtarı)
  baslik           text,                                  -- Türkçe (çevrilmiş)
  orijinal_baslik  text,                                  -- İngilizce (kaynak dil)
  aciklama         text,                                  -- Türkçe açıklama (opsiyonel)
  ulke             text,                                  -- Türkçe ülke adı (ör. "İspanya")
  ulke_kodu        text,                                  -- ISO (ESP, DEU, ...)
  idare            text,                                  -- alıcı / contracting authority
  kategori         text,                                  -- Türkçe iş-dostu kategori (CPV'den)
  cpv              text,                                  -- CPV kodu (ilk)
  tur              text,                                  -- Mal | Hizmet | Yapım
  tahmini_bedel    numeric,
  para_birimi      text DEFAULT 'EUR',
  ilan_tarihi      timestamptz,
  son_teklif_tarihi timestamptz,
  orijinal_url     text,                                  -- TED notice sayfası
  olusturulma      timestamptz DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_ulus_ihale_tarih ON public.uluslararasi_ihaleler (son_teklif_tarihi);
CREATE INDEX IF NOT EXISTS idx_ulus_ihale_ulke ON public.uluslararasi_ihaleler (ulke_kodu);
CREATE INDEX IF NOT EXISTS idx_ulus_ihale_kategori ON public.uluslararasi_ihaleler (kategori);

ALTER TABLE public.uluslararasi_ihaleler ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "ulus_ihale_herkes_okur" ON public.uluslararasi_ihaleler;
CREATE POLICY "ulus_ihale_herkes_okur" ON public.uluslararasi_ihaleler
  FOR SELECT USING (true);

GRANT SELECT ON public.uluslararasi_ihaleler TO anon;
GRANT SELECT ON public.uluslararasi_ihaleler TO authenticated;
GRANT SELECT, INSERT, UPDATE ON public.uluslararasi_ihaleler TO service_role;

NOTIFY pgrst, 'reload schema';
