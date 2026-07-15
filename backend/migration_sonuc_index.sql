-- sonuclananlar.html sayfalı sorgusu için: kazanan_firma dolu satırlarda 3 sıralama alanına partial index.
-- ORDER BY + LIMIT/OFFSET'i tam-tablo sıralamasından index-scan'e indirir (353K satır → timeout yok).
CREATE INDEX IF NOT EXISTS idx_is_tarih
  ON public.ihale_sonuclari (sonuc_tarihi DESC NULLS LAST)
  WHERE kazanan_firma IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_is_bedel
  ON public.ihale_sonuclari (kazanan_teklif DESC NULLS LAST)
  WHERE kazanan_firma IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_is_tenzilat
  ON public.ihale_sonuclari (kazanan_teklif_farki_yuzde DESC NULLS LAST)
  WHERE kazanan_firma IS NOT NULL;

ANALYZE public.ihale_sonuclari;
