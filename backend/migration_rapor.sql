-- ============================================================
-- İHALE / SONUÇ RAPORLARI (ÜCRETLİ) — 26 Tem 2026 (v2: perf düzeltmesi)
-- KULLANICI KARARI: rapor ÜCRETLİ (Pro), EXCEL PREMIUM (kurumsal); alt kademe ekranda
-- ~5000 satır/ilk sayfalar. CSV/Excel yasağını KONTROLLÜ açar (login+Pro+satır tavanı+Excel
-- yalnız kurumsal+filigran). anon ASLA.
--
-- ⚡ PERF: v1'de il/kategori JOIN'li ilanlar üzerinden filtreleniyordu → planner önce
-- 208K İstanbul ilanı seçip 200K nested-loop yapıyordu (16s). ÇÖZÜM: birincil tabloyu
-- (tarih+bedel) MATERIALIZED CTE ile ÖNCE daralt (idx_is_tarih/idx_ilanlar_etkin_tarih),
-- SONRA ilanlar'a join edip il/kategori süz. Tarih verilmezse son 1 yıl varsayılan (tavan).
-- ============================================================

CREATE OR REPLACE FUNCTION public.rapor_ihale(
  p_kelime text DEFAULT NULL, p_il text DEFAULT NULL, p_kategori text DEFAULT NULL,
  p_bas date DEFAULT NULL, p_bit date DEFAULT NULL, p_min bigint DEFAULT NULL,
  p_durum text DEFAULT NULL, p_offset int DEFAULT 0, p_limit int DEFAULT 50
) RETURNS jsonb LANGUAGE sql STABLE SECURITY INVOKER SET search_path = public AS $$
  WITH taban AS MATERIALIZED (  -- ilanlar'ı tarih+durum+bedel ile ÖNCE daralt (idx_ilanlar_etkin_tarih)
    SELECT i.id, i.ikn, i.ekap_id, i.baslik, i.idare, i.il, i.kategori, i.durum,
           i.etkin_tarih, i.son_teklif_tarihi,
           COALESCE(i.yaklasik_maliyet_max, i.yaklasik_maliyet_min, i.tahmini_bedel) AS bedel
    FROM public.ilanlar i
    WHERE i.etkin_tarih >= COALESCE(p_bas, (current_date - interval '1 year')::date)
      AND (p_bit   IS NULL OR i.etkin_tarih < (p_bit + 1))
      AND (p_durum IS NULL OR i.durum = p_durum)
      AND (p_min   IS NULL OR COALESCE(i.yaklasik_maliyet_max,i.yaklasik_maliyet_min,i.tahmini_bedel) >= p_min)
  ),
  filtre AS (
    SELECT * FROM taban t
    WHERE (p_il IS NULL OR t.il = p_il)
      AND (p_kategori IS NULL OR t.kategori = p_kategori)
      AND (p_kelime IS NULL OR public.tr_fold(t.baslik) LIKE '%'||public.tr_fold(p_kelime)||'%')
  ),
  say AS (SELECT count(*) AS n FROM (SELECT 1 FROM filtre LIMIT 50001) z)
  SELECT jsonb_build_object(
    'toplam', (SELECT n FROM say), 'tavan_asildi', ((SELECT n FROM say) >= 50001),
    'satirlar', COALESCE((SELECT jsonb_agg(to_jsonb(f)) FROM (
      SELECT * FROM filtre ORDER BY etkin_tarih DESC NULLS LAST
      OFFSET GREATEST(p_offset,0) LIMIT LEAST(GREATEST(p_limit,1),500)) f), '[]'::jsonb));
$$;
REVOKE EXECUTE ON FUNCTION public.rapor_ihale(text,text,text,date,date,bigint,text,int,int) FROM public, anon;
GRANT  EXECUTE ON FUNCTION public.rapor_ihale(text,text,text,date,date,bigint,text,int,int) TO authenticated, service_role;

CREATE OR REPLACE FUNCTION public.rapor_sonuc(
  p_kelime text DEFAULT NULL, p_il text DEFAULT NULL, p_kategori text DEFAULT NULL,
  p_bas date DEFAULT NULL, p_bit date DEFAULT NULL, p_min bigint DEFAULT NULL,
  p_offset int DEFAULT 0, p_limit int DEFAULT 50
) RETURNS jsonb LANGUAGE sql STABLE SECURITY INVOKER SET search_path = public AS $$
  WITH taban AS MATERIALIZED (  -- ihale_sonuclari'nı tarih+bedel ile ÖNCE daralt (idx_is_tarih)
    SELECT s.id, s.ikn, s.ilan_id, s.kazanan_firma, s.kazanan_teklif, s.sozlesme_bedeli,
           s.sozlesme_tarihi, s.sonuc_tarihi, s.tenzilat_yuzde, s.fesih_var, s.tasfiye_var
    FROM public.ihale_sonuclari s
    WHERE s.kazanan_firma IS NOT NULL   -- idx_is_tarih KISMİ indeksinin predicate'i (kullanım şart)
      AND s.sonuc_tarihi >= COALESCE(p_bas, (current_date - interval '1 year')::date)
      AND (p_bit IS NULL OR s.sonuc_tarihi < (p_bit + 1))
      AND (p_min IS NULL OR COALESCE(s.sozlesme_bedeli,s.kazanan_teklif) >= p_min)
  ),
  filtre AS (
    SELECT t.id, t.ikn, i.baslik, t.kazanan_firma, i.idare, i.il, i.kategori,
           t.kazanan_teklif, t.sozlesme_bedeli, t.sozlesme_tarihi, t.sonuc_tarihi,
           t.tenzilat_yuzde, t.fesih_var, t.tasfiye_var, t.ilan_id
    FROM taban t LEFT JOIN public.ilanlar i ON i.id = t.ilan_id
    WHERE (p_il IS NULL OR i.il = p_il)
      AND (p_kategori IS NULL OR i.kategori = p_kategori)
      AND (p_kelime IS NULL OR public.tr_fold(COALESCE(i.baslik,t.kazanan_firma)) LIKE '%'||public.tr_fold(p_kelime)||'%')
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

NOTIFY pgrst, 'reload schema';
