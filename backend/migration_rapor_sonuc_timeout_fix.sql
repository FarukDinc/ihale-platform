-- ============================================================
-- MADDE 7 — Sonuç Raporu "statement timeout" düzeltmesi (30 Tem 2026)
-- ------------------------------------------------------------
-- SORUN: rapor_sonuc, ihale_sonuclari'nı ÖNCE yalnız tarih (+kazanan_firma) ile
--   MATERIALIZED daraltıyordu → bir yıllık DEV küme. SONRA ilanlar'a join edip
--   il/kelime süzülüyordu; bu filtreler JOIN'DEN SONRA uygulandığı için
--   idx_ilanlar_baslik_fold_trgm / il indeksleri DEVREYE GİRMİYOR → dev nested-loop
--   → 57014 canceling statement due to statement timeout.
--
-- ÇÖZÜM: rapor_ihale ile AYNI mantık → sürücü tabloyu TERS ÇEVİR. Önce ilanlar'ı
--   (il + kategori + başlık trigram) süz (küçük aday kümesi, indeksli), SONRA
--   ihale_sonuclari'na ilan_id ile join et; tarih/bedel filtresini join sonrası uygula.
--
-- SEMANTİK NOTU: kelime artık İHALE BAŞLIĞINDA aranır (rapor_ihale ile birebir aynı
--   davranış). Eski COALESCE(baslik, kazanan_firma) fallback'i (yalnız baslik NULL
--   iken kazanan firmada arama) kaldırıldı — pratikte sonuç satırlarında baslik dolu.
--   İmza ve dönüş şekli AYNEN korundu → frontend değişmez.
-- ============================================================

CREATE OR REPLACE FUNCTION public.rapor_sonuc(
  p_kelime text DEFAULT NULL, p_il text DEFAULT NULL, p_kategori text DEFAULT NULL,
  p_bas date DEFAULT NULL, p_bit date DEFAULT NULL, p_min bigint DEFAULT NULL,
  p_offset int DEFAULT 0, p_limit int DEFAULT 50
) RETURNS jsonb LANGUAGE sql STABLE SECURITY INVOKER SET search_path = public AS $$
  WITH aday AS MATERIALIZED (   -- ÖNCE ilanlar'ı süz: il/kategori structural + başlık trigram (idx_ilanlar_baslik_fold_trgm)
    SELECT i.id AS ilan_id, i.baslik, i.idare, i.il, i.kategori
    FROM public.ilanlar i
    WHERE (p_il       IS NULL OR i.il = p_il)
      AND (p_kategori IS NULL OR i.kategori = p_kategori)
      AND (p_kelime   IS NULL OR public.tr_fold(i.baslik) LIKE '%'||public.tr_fold(p_kelime)||'%')
  ),
  filtre AS (
    SELECT s.id, s.ikn, a.baslik, s.kazanan_firma, a.idare, a.il, a.kategori,
           s.kazanan_teklif, s.sozlesme_bedeli, s.sozlesme_tarihi, s.sonuc_tarihi,
           s.tenzilat_yuzde, s.fesih_var, s.tasfiye_var, s.ilan_id
    FROM aday a
    JOIN public.ihale_sonuclari s ON s.ilan_id = a.ilan_id
    WHERE s.kazanan_firma IS NOT NULL   -- idx_ihale_sonuclari_yuklenici_id / idx_is_tarih predicate uyumu
      AND s.sonuc_tarihi >= COALESCE(p_bas, (current_date - interval '1 year')::date)
      AND (p_bit IS NULL OR s.sonuc_tarihi < (p_bit + 1))
      AND (p_min IS NULL OR COALESCE(s.sozlesme_bedeli,s.kazanan_teklif) >= p_min)
  ),
  say AS (SELECT count(*) AS n FROM (SELECT 1 FROM filtre LIMIT 50001) z)
  SELECT jsonb_build_object(
    'toplam', (SELECT n FROM say), 'tavan_asildi', ((SELECT n FROM say) >= 50001),
    'satirlar', COALESCE((SELECT jsonb_agg(to_jsonb(f)) FROM (
      SELECT * FROM filtre ORDER BY sonuc_tarihi DESC NULLS LAST
      OFFSET GREATEST(p_offset,0) LIMIT LEAST(GREATEST(p_limit,1),500)) f), '[]'::jsonb));
$$;
REVOKE EXECUTE ON FUNCTION public.rapor_sonuc(text,text,text,date,date,bigint,int,int) FROM public, anon;
GRANT  EXECUTE ON FUNCTION public.rapor_sonuc(text,text,text,date,date,bigint,int,int) TO authenticated, service_role;

-- İhale_sonuclari.ilan_id üzerinde indeks join için ŞART (yoksa aday→sonuc nested loop yavaş).
-- migration_firmam_eslesme.sql yuklenici_id indeksini ekledi; ilan_id de gerekli:
CREATE INDEX IF NOT EXISTS idx_ihale_sonuclari_ilan_id
  ON public.ihale_sonuclari (ilan_id) WHERE ilan_id IS NOT NULL;

NOTIFY pgrst, 'reload schema';
