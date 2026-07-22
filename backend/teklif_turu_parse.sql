-- ilan_metni'nden teklif-türü alanlarını çıkarır (idempotent + artımlı).
-- Tek-seferlik çalıştırılır + run_scraper.sh gece çağırır (ilan_metni backfill doldurdukça
-- yeni ilanlar işlenir). teklif_elektronik boolean daima set edilir → "işlendi" işareti;
-- WHERE guard işlenmemiş (tüm 4 kolon NULL) + ilan_metni dolu satırları seçer.

UPDATE public.ilanlar SET
  teklif_elektronik = (ilan_metni ~* 'elektronik ortamda|ekap üzerinden elektronik|elektronik eksiltme'),
  teklif_kismi = CASE
    WHEN ilan_metni ~* 'kısmi teklif.{0,25}veril[ae]mez|işin tamamı(na| için) teklif' THEN false
    WHEN ilan_metni ~* 'kısmi teklif(e açık| ?veril(ebil|ir|ecek))'                    THEN true
    ELSE NULL END,
  teklif_fiyat_turu = CASE
    WHEN ilan_metni ~* 'birim fiyat teklif' AND ilan_metni ~* 'götürü bedel' THEN 'karma'
    WHEN ilan_metni ~* 'birim fiyat teklif'                                  THEN 'birim'
    WHEN ilan_metni ~* 'götürü bedel'                                        THEN 'goturu'
    ELSE NULL END,
  teklif_istekli = CASE
    WHEN ilan_metni ~* 'yerli ve yabancı'                          THEN 'yerli_yabanci'
    WHEN ilan_metni ~* 'sadece yerli istekli|yalnızca yerli istekli' THEN 'yerli'
    ELSE NULL END
WHERE ilan_metni IS NOT NULL
  AND teklif_elektronik IS NULL AND teklif_kismi IS NULL
  AND teklif_fiyat_turu IS NULL AND teklif_istekli IS NULL;
