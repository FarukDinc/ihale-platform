-- ============================================================
-- MADDE 7-edge — Sonuç Raporu kelime-tek-başına yavaşlığı (31 Tem 2026)
-- ------------------------------------------------------------
-- MADDE 7 filtreli aramaları hızlandırdı (belpa+ANKARA → anlık). Ama kelime TEK BAŞINA
-- (il/kategori/tarih filtresiz) hâlâ yavaştı: aday CTE `tr_fold(i.baslik) LIKE` İFADESİNİ
-- kullanıyordu → STORED trigram indeksini (idx_ilanlar_baslik_fold_trgm2, `baslik_fold`
-- kolonu üzerinde) KULLANAMIYOR, ilanlar (1.96M) seq scan.
--
-- ÇÖZÜM: misafir aramasının kanıtlı-hızlı yolunu kullan → STORED `baslik_fold` kolonu
-- (tr_fold(baslik||okas||isin_yapilacagi_yer), GIN trigram indeksli). Kelime artık başlık +
-- OKAS + işin yapılacağı yerde aranır (daha iyi kapsam) ve indeks devrede → kelime-tek hızlı.
-- İmza/dönüş AYNI → frontend değişmez.
--
-- Çalıştır (mevcut fonksiyon → superuser):
--   docker exec -i supabase-db psql -U supabase_admin -d postgres < backend/migration_rapor_sonuc_edge_fix.sql
-- ============================================================

CREATE OR REPLACE FUNCTION public.rapor_sonuc(
  p_kelime text DEFAULT NULL, p_il text DEFAULT NULL, p_kategori text DEFAULT NULL,
  p_bas date DEFAULT NULL, p_bit date DEFAULT NULL, p_min bigint DEFAULT NULL,
  p_offset int DEFAULT 0, p_limit int DEFAULT 50
) RETURNS jsonb LANGUAGE sql STABLE SECURITY INVOKER SET search_path = public AS $$
  WITH aday AS MATERIALIZED (
    SELECT i.id AS ilan_id, i.baslik, i.idare, i.il, i.kategori
    FROM public.ilanlar i
    WHERE (p_il       IS NULL OR i.il = p_il)
      AND (p_kategori IS NULL OR i.kategori = p_kategori)
      -- STORED baslik_fold + idx_ilanlar_baslik_fold_trgm2 (kelime-tek dahi indeksli/hızlı)
      AND (p_kelime   IS NULL OR i.baslik_fold LIKE '%'||public.tr_fold(p_kelime)||'%')
  ),
  filtre AS (
    SELECT s.id, s.ikn, a.baslik, s.kazanan_firma, a.idare, a.il, a.kategori,
           s.kazanan_teklif, s.sozlesme_bedeli, s.sozlesme_tarihi, s.sonuc_tarihi,
           s.tenzilat_yuzde, s.fesih_var, s.tasfiye_var, s.ilan_id
    FROM aday a
    JOIN public.ihale_sonuclari s ON s.ilan_id = a.ilan_id
    WHERE s.kazanan_firma IS NOT NULL
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

NOTIFY pgrst, 'reload schema';

-- Doğrulama (kelime-tek, artık hızlı olmalı):
--   \timing on
--   SELECT public.rapor_sonuc('okul', NULL, NULL, NULL, NULL, NULL, 0, 20) -> 'toplam';
