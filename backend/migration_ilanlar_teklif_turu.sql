-- ilanlar'a teklif-türü filtre alanları (rakip ihaleciler.com'da var, bizde yoktu).
--
-- Kaynak: ilanlar.ilan_metni (EKAP ilan HTML metni). EKAP LİSTE endpoint'i bu alanları
-- döndürmez; yalnız ilan metninde/detayında var → ilan_metni dolu olan ilanlarda parse edilir
-- (şu an ~%2,6; ilan_metni backfill ilerledikçe kapsam büyür). Parse SQL regex ile yapılır
-- (teklif_turu_parse: tek-seferlik + run_scraper.sh gecelik UPDATE).
--
-- ⚠️ ANON MASKE (bkz. [[anon-maske-iki-kok-neden]] kök-neden C): SONRADAN eklenen kolon
-- anon kolon-GRANT'ına OTOMATİK girmez → ihaleler.html misafir yolunda bu kolonu SELECT/WHERE
-- ederse 42501 sayfayı öldürür. Bu alanlar HASSAS DEĞİL (kamuya açık ihale nitelikleri) →
-- anon'a SELECT GRANT veriliyor.

ALTER TABLE public.ilanlar
  ADD COLUMN IF NOT EXISTS teklif_elektronik boolean,          -- e-ihale (elektronik ortamda)
  ADD COLUMN IF NOT EXISTS teklif_kismi      boolean,          -- kısmi teklif verilebilir mi
  ADD COLUMN IF NOT EXISTS teklif_fiyat_turu text,             -- 'birim' | 'goturu' | 'karma'
  ADD COLUMN IF NOT EXISTS teklif_istekli    text;             -- 'yerli' | 'yerli_yabanci'

-- Anon (misafir) bu 4 kolonu okuyabilsin (filtre + görünüm). Hassas değil.
GRANT SELECT (teklif_elektronik, teklif_kismi, teklif_fiyat_turu, teklif_istekli)
  ON public.ilanlar TO anon;

-- Filtre indeksleri — yalnız NULL-olmayanlar (kısmi doluluk; ölü uzayı indekslemez).
CREATE INDEX IF NOT EXISTS idx_ilanlar_teklif_kismi   ON public.ilanlar (teklif_kismi)      WHERE teklif_kismi IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_ilanlar_teklif_fiyat   ON public.ilanlar (teklif_fiyat_turu) WHERE teklif_fiyat_turu IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_ilanlar_teklif_istekli ON public.ilanlar (teklif_istekli)    WHERE teklif_istekli IS NOT NULL;

NOTIFY pgrst, 'reload schema';
