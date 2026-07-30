-- ============================================================
-- DT Analizi filtreli yol hızlandırma — _dt_ozet_json MATERIALIZED CTE (31 Tem 2026)
-- ------------------------------------------------------------
-- dt_analiz_ozet('ANKARA') ~13s: il indeksi ANKARA'ya iniyor ama `f` CTE (ANKARA'nın ~235K
-- satırı) `son` + 7 kırılım + trend + bant tarafından ÇOK KEZ referanslandığı için tekrar
-- tekrar taranıyor. ÇÖZÜM: `f` ve `son`'u MATERIALIZED yap → bir kez hesaplanıp bellekte
-- tutulur, tüm kırılımlar aynı kümeyi kullanır (6+ tarama → 1 tarama). MV gerekmez.
-- İmza AYNI → CREATE OR REPLACE; dt_analiz_mv / dt_analiz_yil_mv aynen çalışır (sadece gövde).
--
-- Çalıştır (superuser):
--   docker exec -i supabase-db psql -U supabase_admin -d postgres < backend/migration_dt_ozet_materialized.sql
-- Not: dt_analiz_mv/dt_analiz_yil_mv'yi yeniden REFRESH etmeye gerek yok (gövde değişti, veri değil).
-- ============================================================

CREATE OR REPLACE FUNCTION public._dt_ozet_json(
  p_il text DEFAULT NULL, p_kategori text DEFAULT NULL, p_tur text DEFAULT NULL, p_yil int DEFAULT NULL
) RETURNS jsonb
LANGUAGE sql STABLE SECURITY DEFINER SET search_path = public AS $$
  WITH f AS MATERIALIZED (
    SELECT dt_no, tur, il, kategori, idare, idare_tur, tarih
    FROM public.dogrudan_temin_ilanlari
    WHERE (p_il IS NULL OR il = p_il)
      AND (p_kategori IS NULL OR kategori = p_kategori)
      AND (p_tur IS NULL OR tur = p_tur)
      AND (p_yil IS NULL OR (tarih >= make_date(p_yil,1,1) AND tarih < make_date(p_yil+1,1,1)))
  ),
  son AS MATERIALIZED (
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

NOTIFY pgrst, 'reload schema';

-- Doğrulama (artık çok daha hızlı olmalı):
--   \timing on
--   SELECT public.dt_analiz_ozet('ANKARA',NULL,NULL,NULL) -> 'toplam';
