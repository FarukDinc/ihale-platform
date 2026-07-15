-- ilanlar (~256K satır) en sıcak filtre/sıralama kolonlarında index yoktu → her liste/dashboard/anasayfa
-- yüklemesinde seq scan + top-N sort. Denetim bulgusu #6/#16.
-- (durum, son_teklif_tarihi): Güncel/Geçmiş sekme filtresi + durum='aktif' filtresi + son_teklif sıralama.
CREATE INDEX IF NOT EXISTS idx_ilanlar_durum_son_teklif
  ON public.ilanlar (durum, son_teklif_tarihi DESC NULLS LAST);
-- son_teklif_tarihi tek başına (durum'suz global sıralama/aralık).
CREATE INDEX IF NOT EXISTS idx_ilanlar_son_teklif_tarihi
  ON public.ilanlar (son_teklif_tarihi DESC NULLS LAST);
-- ilan_tarihi (en yeni sıralaması).
CREATE INDEX IF NOT EXISTS idx_ilanlar_ilan_tarihi
  ON public.ilanlar (ilan_tarihi DESC NULLS LAST);
ANALYZE public.ilanlar;
