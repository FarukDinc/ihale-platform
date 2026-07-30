-- ============================================================
-- MADDE 6 — Eşleşme algoritması iyileştirme (31 Tem 2026)
-- ------------------------------------------------------------
-- "Sizin İçin Katılabileceğiniz İhaleler" (firma_icin_acik_ihaleler) iyileştirmesi.
-- MEVCUT: kategori(+40) + il(+15) + bedel-yakınlık(+20); filtre kategori/kelime + ±%500 bant.
-- YENİ:
--   • IDARE SİNYALİ: firmanın en çok iş aldığı ilk 8 idare → o idarelerin açık ihaleleri
--     +25 puan + OR filtresine dahil (ilişki bazlı fırsat). Gerekçeye "sık çalıştığınız idare".
--   • BANT ±%500 → ±%300 (p_bant 5→3): alakasız ölçekli ihaleler daha çok elenir.
--   • Puanlar: kategori 40 · idare 25 · il 15 · bedel-yakınlık 20.
-- İmza AYNI → CREATE OR REPLACE (frontend değişmez; mevcut grant'lar korunur, yine de yeniden verilir).
-- SECURITY INVOKER (authenticated çağırır; idare authenticated'a açık). Wrapper SECURITY DEFINER.
--
-- Çalıştır (mevcut fonksiyon → superuser):
--   docker exec -i supabase-db psql -U supabase_admin -d postgres < backend/migration_firmam_eslesme_v2.sql
-- ============================================================

CREATE OR REPLACE FUNCTION public.firma_icin_acik_ihaleler(
  p_yuklenici_id uuid, p_limit int DEFAULT 12, p_bant numeric DEFAULT 3)
RETURNS TABLE (
  id uuid, baslik text, idare text, il text, kategori text,
  yaklasik_maliyet_min numeric, yaklasik_maliyet_max numeric, tahmini_bedel numeric,
  son_teklif_tarihi timestamptz, skor numeric, eslesme_nedeni text)
LANGUAGE sql STABLE AS $$
  WITH firma AS (
    SELECT
      (SELECT array_agg(k) FROM (
         SELECT i.kategori k FROM public.ihale_sonuclari s JOIN public.ilanlar i ON i.id=s.ilan_id
         WHERE s.yuklenici_id=p_yuklenici_id AND i.kategori IS NOT NULL
         GROUP BY i.kategori ORDER BY count(*) DESC LIMIT 5) t)          AS kategoriler,
      (SELECT array_agg(DISTINCT i.il) FROM public.ihale_sonuclari s JOIN public.ilanlar i ON i.id=s.ilan_id
         WHERE s.yuklenici_id=p_yuklenici_id AND i.il IS NOT NULL)       AS iller,
      (SELECT array_agg(k) FROM (
         SELECT i.idare k FROM public.ihale_sonuclari s JOIN public.ilanlar i ON i.id=s.ilan_id
         WHERE s.yuklenici_id=p_yuklenici_id AND i.idare IS NOT NULL
         GROUP BY i.idare ORDER BY count(*) DESC LIMIT 8) t)             AS idareler,   -- YENİ
      (SELECT percentile_cont(0.5) WITHIN GROUP (ORDER BY COALESCE(s.kazanan_teklif,s.sozlesme_bedeli))
         FROM public.ihale_sonuclari s WHERE s.yuklenici_id=p_yuklenici_id) AS bedel
  )
  SELECT i.id, i.baslik, i.idare, i.il, i.kategori,
         i.yaklasik_maliyet_min::numeric, i.yaklasik_maliyet_max::numeric, i.tahmini_bedel::numeric,
         i.son_teklif_tarihi::timestamptz,
         round((
           (CASE WHEN i.kategori = ANY(f.kategoriler) THEN 40 ELSE 0 END)
         + (CASE WHEN f.idareler IS NOT NULL AND i.idare = ANY(f.idareler) THEN 25 ELSE 0 END)  -- YENİ
         + (CASE WHEN i.il = ANY(f.iller) THEN 15 ELSE 0 END)
         + (CASE WHEN f.bedel IS NULL OR f.bedel<=0 THEN 0
                 ELSE 20*(1 - LEAST(abs(ln(GREATEST(
                        COALESCE(NULLIF(i.yaklasik_maliyet_max,0),NULLIF(i.tahmini_bedel,0),1),1)::numeric/f.bedel))/ln(p_bant),1)) END)
         )::numeric, 1)                                                    AS skor,
         (CASE WHEN i.kategori = ANY(f.kategoriler) THEN 'Uzmanlık alanınız' ELSE 'Benzer konu' END
          || CASE WHEN f.idareler IS NOT NULL AND i.idare = ANY(f.idareler) THEN ' · sık çalıştığınız idare' ELSE '' END
          || CASE WHEN i.il = ANY(f.iller) THEN ' · daha önce iş aldığınız il' ELSE '' END) AS eslesme_nedeni
  FROM public.ilanlar i, firma f
  WHERE i.durum='aktif'
    AND (i.son_teklif_tarihi IS NULL OR i.son_teklif_tarihi >= now())
    AND ( i.kategori = ANY(f.kategoriler)
       OR (f.idareler IS NOT NULL AND i.idare = ANY(f.idareler))   -- YENİ: ilişki bazlı
       OR EXISTS (
            SELECT 1 FROM public.ihale_konu_kelimeleri(
              (SELECT string_agg(i2.baslik,' ') FROM (
                 SELECT i3.baslik FROM public.ihale_sonuclari s2
                   JOIN public.ilanlar i3 ON i3.id=s2.ilan_id
                 WHERE s2.yuklenici_id=p_yuklenici_id LIMIT 50) i2)) t
            WHERE public.tr_fold(i.baslik) LIKE '%'||t.kelime||'%') )
    AND (f.bedel IS NULL OR f.bedel<=0
      OR COALESCE(NULLIF(i.yaklasik_maliyet_max,0),NULLIF(i.tahmini_bedel,0)) IS NULL
      OR COALESCE(NULLIF(i.yaklasik_maliyet_max,0),NULLIF(i.tahmini_bedel,0))
         BETWEEN f.bedel/p_bant AND f.bedel*p_bant)
  ORDER BY skor DESC, i.son_teklif_tarihi ASC NULLS LAST
  LIMIT p_limit;
$$;
REVOKE EXECUTE ON FUNCTION public.firma_icin_acik_ihaleler(uuid,int,numeric) FROM public, anon;
GRANT  EXECUTE ON FUNCTION public.firma_icin_acik_ihaleler(uuid,int,numeric) TO authenticated, service_role;

-- Wrapper: bant 5→3 (dashboard bu wrapper'ı çağırır).
CREATE OR REPLACE FUNCTION public.firmam_acik_ihaleler(p_limit int DEFAULT 12)
RETURNS TABLE (
  id uuid, baslik text, idare text, il text, kategori text,
  yaklasik_maliyet_min numeric, yaklasik_maliyet_max numeric, tahmini_bedel numeric,
  son_teklif_tarihi timestamptz, skor numeric, eslesme_nedeni text)
LANGUAGE sql STABLE SECURITY DEFINER SET search_path = public AS $$
  SELECT * FROM public.firma_icin_acik_ihaleler(
    (SELECT firma_id FROM public.kullanici_profiller WHERE id = auth.uid()), p_limit, 3);
$$;
REVOKE EXECUTE ON FUNCTION public.firmam_acik_ihaleler(int) FROM public, anon;
GRANT  EXECUTE ON FUNCTION public.firmam_acik_ihaleler(int) TO authenticated, service_role;

NOTIFY pgrst, 'reload schema';

-- Doğrulama (bir yuklenici id ile):
--   SELECT baslik, idare, skor, eslesme_nedeni FROM firma_icin_acik_ihaleler(
--     (SELECT id FROM yukleniciler WHERE ad ILIKE '%ÜNTES%' LIMIT 1), 6, 3);
