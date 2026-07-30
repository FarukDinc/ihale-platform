-- ============================================================
-- MADDE 14 — DT Analizi'ne YIL filtresi (31 Tem 2026)
-- ------------------------------------------------------------
-- dt_analiz_ozet / _dt_ozet_json'a p_yil eklenir. Enflasyon nedeniyle ort/medyan kazanan
-- bedel yıla göre çok değişken → yıl bazlı süzme gerekli (MADDE 12 ile aynı gerekçe).
--
-- İmza DEĞİŞİYOR (3→4 arg) → CREATE OR REPLACE yetmez, DROP gerekir. dt_analiz_mv
-- _dt_ozet_json'a bağlı → önce MV DROP, sonra fonksiyonlar, sonra yeniden kur.
-- Yıl filtresi SARGABLE tarih aralığı (make_date) — extract(year) non-sargable olurdu.
-- DT tablosu 1.49M; yıl+opsiyonel filtre canlı yol (15s timeout) içinde döner. MV yalnız
-- filtresiz (p_yil NULL) yol için; yıl seçilince canlı hesaplanır.
--
-- Çalıştır (superuser):
--   docker exec -i supabase-db psql -U supabase_admin -d postgres < backend/migration_dt_analiz_yil.sql
-- GECE REFRESH aynı kalır: REFRESH MATERIALIZED VIEW public.dt_analiz_mv;
-- ============================================================

DROP MATERIALIZED VIEW IF EXISTS public.dt_analiz_mv;
DROP FUNCTION IF EXISTS public.dt_analiz_ozet(text, text, text);
DROP FUNCTION IF EXISTS public._dt_ozet_json(text, text, text);

-- 1) Ortak hesaplayıcı — p_yil eklendi (sargable tarih aralığı).
CREATE OR REPLACE FUNCTION public._dt_ozet_json(
  p_il text DEFAULT NULL, p_kategori text DEFAULT NULL, p_tur text DEFAULT NULL, p_yil int DEFAULT NULL
) RETURNS jsonb
LANGUAGE sql STABLE SECURITY DEFINER SET search_path = public AS $$
  WITH f AS (
    SELECT dt_no, tur, il, kategori, idare, idare_tur, tarih
    FROM public.dogrudan_temin_ilanlari
    WHERE (p_il IS NULL OR il = p_il)
      AND (p_kategori IS NULL OR kategori = p_kategori)
      AND (p_tur IS NULL OR tur = p_tur)
      AND (p_yil IS NULL OR (tarih >= make_date(p_yil,1,1) AND tarih < make_date(p_yil+1,1,1)))
  ),
  son AS (
    SELECT s.kazanan_bedel
    FROM public.dogrudan_temin_sonuclari s
    JOIN f ON f.dt_no = s.dt_no
    WHERE s.kazanan_bedel > 0
  )
  SELECT jsonb_build_object(
    'toplam',       (SELECT count(*) FROM f),
    'sonuclanan',   (SELECT count(*) FROM son),
    'ort_bedel',    (SELECT round(avg(kazanan_bedel)) FROM son),
    'medyan_bedel', (SELECT round(percentile_cont(0.5) WITHIN GROUP (ORDER BY kazanan_bedel)) FROM son),
    'tur', (SELECT coalesce(jsonb_agg(jsonb_build_object('k',k,'n',n) ORDER BY n DESC), '[]'::jsonb)
            FROM (SELECT tur AS k, count(*) AS n FROM f WHERE tur IS NOT NULL AND btrim(tur)<>'' GROUP BY tur ORDER BY count(*) DESC LIMIT 10) t),
    'il', (SELECT coalesce(jsonb_agg(jsonb_build_object('k',k,'n',n) ORDER BY n DESC), '[]'::jsonb)
           FROM (SELECT il AS k, count(*) AS n FROM f WHERE il IS NOT NULL AND btrim(il)<>'' GROUP BY il ORDER BY count(*) DESC LIMIT 15) t),
    'kategori', (SELECT coalesce(jsonb_agg(jsonb_build_object('k',k,'n',n) ORDER BY n DESC), '[]'::jsonb)
                 FROM (SELECT kategori AS k, count(*) AS n FROM f WHERE kategori IS NOT NULL AND btrim(kategori)<>'' GROUP BY kategori ORDER BY count(*) DESC LIMIT 15) t),
    'idare', (SELECT coalesce(jsonb_agg(jsonb_build_object('k',k,'n',n) ORDER BY n DESC), '[]'::jsonb)
              FROM (SELECT idare AS k, count(*) AS n FROM f WHERE idare IS NOT NULL AND btrim(idare)<>'' GROUP BY idare ORDER BY count(*) DESC LIMIT 12) t),
    'idare_tur', (SELECT coalesce(jsonb_agg(jsonb_build_object('k',k,'n',n) ORDER BY n DESC), '[]'::jsonb)
                  FROM (SELECT idare_tur AS k, count(*) AS n FROM f WHERE idare_tur IS NOT NULL AND btrim(idare_tur)<>'' GROUP BY idare_tur ORDER BY count(*) DESC LIMIT 12) t),
    'trend', (SELECT coalesce(jsonb_object_agg(ay, n), '{}'::jsonb)
              FROM (SELECT to_char(date_trunc('month', tarih), 'YYYY-MM') AS ay, count(*) AS n
                    FROM f WHERE (p_yil IS NOT NULL OR tarih >= (now() - interval '24 months')) GROUP BY 1) t),
    'bedel_bant', (SELECT jsonb_build_object(
        'b0', count(*) FILTER (WHERE kazanan_bedel < 50000),
        'b1', count(*) FILTER (WHERE kazanan_bedel >= 50000    AND kazanan_bedel < 200000),
        'b2', count(*) FILTER (WHERE kazanan_bedel >= 200000   AND kazanan_bedel < 1000000),
        'b3', count(*) FILTER (WHERE kazanan_bedel >= 1000000  AND kazanan_bedel < 5000000),
        'b4', count(*) FILTER (WHERE kazanan_bedel >= 5000000)
      ) FROM son)
  );
$$;

-- 2) MV — filtresiz TAM özet (p_yil NULL de dahil dört argüman).
CREATE MATERIALIZED VIEW public.dt_analiz_mv AS
  SELECT 1 AS id, public._dt_ozet_json(NULL, NULL, NULL, NULL) AS ozet;
CREATE UNIQUE INDEX IF NOT EXISTS dt_analiz_mv_pk ON public.dt_analiz_mv (id);

-- 3) Genel RPC — p_yil eklendi. Filtre YOKSA (yıl dahil) MV; varsa canlı.
CREATE OR REPLACE FUNCTION public.dt_analiz_ozet(
  p_il text DEFAULT NULL, p_kategori text DEFAULT NULL, p_tur text DEFAULT NULL, p_yil int DEFAULT NULL
) RETURNS jsonb
LANGUAGE plpgsql STABLE SECURITY DEFINER
SET search_path = public SET statement_timeout = '15s' AS $$
BEGIN
  IF (p_il IS NULL AND p_kategori IS NULL AND p_tur IS NULL AND p_yil IS NULL) THEN
    RETURN (SELECT ozet FROM public.dt_analiz_mv);   -- filtresiz: MV'den anında
  END IF;
  RETURN public._dt_ozet_json(p_il, p_kategori, p_tur, p_yil);  -- filtreli/yıllı: canlı
END;
$$;

REVOKE ALL ON FUNCTION public._dt_ozet_json(text, text, text, int) FROM public;
REVOKE ALL ON FUNCTION public.dt_analiz_ozet(text, text, text, int) FROM public;
GRANT EXECUTE ON FUNCTION public.dt_analiz_ozet(text, text, text, int) TO authenticated, service_role;

NOTIFY pgrst, 'reload schema';

-- Doğrulama:
--   SELECT public.dt_analiz_ozet(NULL,NULL,NULL,2024) -> 'toplam';   -- 2024 DT sayısı
