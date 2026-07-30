-- ============================================================
-- MADDE 7-edge (B) — geniş kelime-tek sonuç aramasında 6 ay varsayılanı (31 Tem 2026)
-- ------------------------------------------------------------
-- Çok yaygın kelime tek başına (il/kategori/tarih yok) 17K+ sonuç eşleyip yavaşlıyordu.
-- ÇÖZÜM: SADECE bu durumda (p_kelime var, p_il YOK, p_kategori YOK, p_bas YOK) varsayılan
--   alt-tarih 1 yıl yerine SON 6 AY → sonuç kümesi küçülür, hızlanır. Kullanıcı tarih
--   GİRERSE COALESCE(p_bas, …) onun değerini kullanır → SEÇTİĞİ TARİHE DOKUNULMAZ; isterse
--   geriye genişletir. İmza/dönüş AYNI → frontend değişmez.
--
-- Çalıştır (mevcut fonksiyon → superuser):
--   docker exec -i supabase-db psql -U supabase_admin -d postgres < backend/migration_rapor_sonuc_6ay.sql
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
      AND (p_kelime   IS NULL OR i.baslik_fold LIKE '%'||public.tr_fold(p_kelime)||'%')
  ),
  filtre AS (
    SELECT s.id, s.ikn, a.baslik, s.kazanan_firma, a.idare, a.il, a.kategori,
           s.kazanan_teklif, s.sozlesme_bedeli, s.sozlesme_tarihi, s.sonuc_tarihi,
           s.tenzilat_yuzde, s.fesih_var, s.tasfiye_var, s.ilan_id
    FROM aday a
    JOIN public.ihale_sonuclari s ON s.ilan_id = a.ilan_id
    WHERE s.kazanan_firma IS NOT NULL
      -- Kullanıcı tarih verdiyse ONA DOKUNMA. Vermediyse: geniş kelime-tek arama (kelime var,
      -- il/kategori yok) ise varsayılan SON 6 AY; aksi halde SON 1 YIL.
      AND s.sonuc_tarihi >= COALESCE(
            p_bas,
            (current_date - CASE
               WHEN p_kelime IS NOT NULL AND p_il IS NULL AND p_kategori IS NULL
               THEN interval '6 months' ELSE interval '1 year' END)::date)
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

-- Doğrulama (artık çok daha hızlı olmalı):
--   \timing on
--   SELECT public.rapor_sonuc('okul', NULL, NULL, NULL, NULL, NULL, 0, 20) -> 'toplam';
