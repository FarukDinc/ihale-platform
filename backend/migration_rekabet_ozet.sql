-- rekabet-analizi.html server-side: tüm ilanlar client'a inip 8 breakdown JS'te hesaplanıyordu (#4).
-- Tek RPC filtreye (durum/il/kategori) göre tüm gruplamaları jsonb döndürür. durum/il/kategori indexleri var.
CREATE OR REPLACE FUNCTION public.rekabet_ozet(
  p_durum text DEFAULT NULL, p_il text DEFAULT NULL, p_kategori text DEFAULT NULL
)
RETURNS jsonb
LANGUAGE sql STABLE
AS $$
  WITH f AS (
    SELECT tur, il, idare, usul, yaklasik_maliyet_min AS m, kategori,
           COALESCE(ilan_tarihi, son_teklif_tarihi) AS tarih
    FROM public.ilanlar
    WHERE (p_durum    IS NULL OR durum    = p_durum)
      AND (p_il       IS NULL OR il       = p_il)
      AND (p_kategori IS NULL OR kategori = p_kategori)
  )
  SELECT jsonb_build_object(
    'toplam',       (SELECT count(*) FROM f),
    'ort_maliyet',  (SELECT COALESCE(round(avg(m)),0) FROM f WHERE m > 0),
    'maliyet_adet', (SELECT count(*) FROM f WHERE m > 0),
    'tur',      (SELECT COALESCE(jsonb_agg(jsonb_build_object('k',k,'n',n) ORDER BY n DESC),'[]'::jsonb)
                 FROM (SELECT tur k, count(*) n FROM f WHERE tur IS NOT NULL GROUP BY tur) x),
    'il',       (SELECT COALESCE(jsonb_agg(jsonb_build_object('k',k,'n',n) ORDER BY n DESC),'[]'::jsonb)
                 FROM (SELECT il k, count(*) n FROM f WHERE il IS NOT NULL GROUP BY il) x),
    'usul',     (SELECT COALESCE(jsonb_agg(jsonb_build_object('k',k,'n',n) ORDER BY n DESC),'[]'::jsonb)
                 FROM (SELECT usul k, count(*) n FROM f WHERE usul IS NOT NULL GROUP BY usul ORDER BY count(*) DESC LIMIT 60) x),
    'kategori', (SELECT COALESCE(jsonb_agg(jsonb_build_object('k',k,'n',n) ORDER BY n DESC),'[]'::jsonb)
                 FROM (SELECT kategori k, count(*) n FROM f WHERE kategori IS NOT NULL GROUP BY kategori) x),
    'idare',    (SELECT COALESCE(jsonb_agg(jsonb_build_object('k',k,'n',n) ORDER BY n DESC),'[]'::jsonb)
                 FROM (SELECT idare k, count(*) n FROM f WHERE idare IS NOT NULL GROUP BY idare ORDER BY count(*) DESC LIMIT 20) x),
    'tur_maliyet', (SELECT COALESCE(jsonb_agg(jsonb_build_object('k',k,'sayi',sayi,'ort',ort) ORDER BY ort DESC NULLS LAST),'[]'::jsonb)
                 FROM (SELECT tur k, count(*) sayi, round(avg(m) FILTER (WHERE m > 0)) ort
                       FROM f WHERE tur IS NOT NULL GROUP BY tur) x),
    'trend', (SELECT COALESCE(jsonb_object_agg(ay, n),'{}'::jsonb)
                 FROM (SELECT to_char(tarih, 'YYYY-MM') ay, count(*) n
                       FROM f WHERE tarih IS NOT NULL AND tarih >= (now() - interval '24 months')
                       GROUP BY 1) x),
    'butce', jsonb_build_object(
      'b0',   (SELECT count(*) FROM f WHERE m > 0 AND m <  500000),
      'b1',   (SELECT count(*) FROM f WHERE m >= 500000    AND m < 2000000),
      'b2',   (SELECT count(*) FROM f WHERE m >= 2000000   AND m < 10000000),
      'b3',   (SELECT count(*) FROM f WHERE m >= 10000000  AND m < 50000000),
      'b4',   (SELECT count(*) FROM f WHERE m >= 50000000  AND m < 200000000),
      'b5',   (SELECT count(*) FROM f WHERE m >= 200000000),
      'byok', (SELECT count(*) FROM f WHERE m IS NULL OR m <= 0)
    )
  );
$$;
GRANT EXECUTE ON FUNCTION public.rekabet_ozet(text, text, text) TO anon, authenticated, service_role;
NOTIFY pgrst, 'reload schema';
