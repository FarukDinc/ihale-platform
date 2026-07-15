-- Coğrafi-ağırlıklı eşleştirme: mevcut ihaleye_uygun_firmalar + il_merkez mesafesiyle yakınlık bonusu.
-- Harita/RFQ "En Uygun N Üretici" için: aynı il > yakın il > uzak il. Mevcut RPC'yi BOZMAZ (yeni ad).
-- tr_fold prod'da mevcut; il_merkez migration_il_merkez.sql ile kurulur.

DROP FUNCTION IF EXISTS public.ihaleye_uygun_firmalar_geo(text, text, numeric, int, numeric);

CREATE OR REPLACE FUNCTION public.ihaleye_uygun_firmalar_geo(
  p_kategori      text,
  p_il            text    DEFAULT NULL,
  p_bedel         numeric DEFAULT NULL,
  p_limit         int     DEFAULT 20,
  p_kapasite_esik numeric DEFAULT 0.10
)
RETURNS TABLE (
  kazanan_firma    text,
  yuklenici_id     uuid,
  firma_il         text,
  kategori_kazanim bigint,
  max_kazanim      numeric,
  ort_kazanim      numeric,
  ayni_il          boolean,
  kapasite_uygun   boolean,
  mesafe_km        numeric,
  skor             numeric
)
LANGUAGE sql STABLE
AS $$
  WITH firma AS (
    SELECT
      s.kazanan_firma,
      s.yuklenici_id,
      mode() WITHIN GROUP (ORDER BY i.il)                       AS firma_il,
      count(*)                                                  AS kategori_kazanim,
      max(COALESCE(s.kazanan_teklif, s.sozlesme_bedeli))        AS max_kazanim,
      round(avg(COALESCE(s.kazanan_teklif, s.sozlesme_bedeli))) AS ort_kazanim,
      bool_or(i.il = p_il)                                      AS ayni_il
    FROM public.ihale_sonuclari s
    JOIN public.ilanlar i ON i.id = s.ilan_id
    WHERE i.kategori = p_kategori
      AND s.kazanan_firma IS NOT NULL AND s.kazanan_firma <> ''
    GROUP BY s.kazanan_firma, s.yuklenici_id
    HAVING p_bedel IS NULL
        OR max(COALESCE(s.kazanan_teklif, s.sozlesme_bedeli)) >= p_bedel * p_kapasite_esik
  ),
  hedef AS (   -- her zaman tek satır (bulunmazsa NULL)
    SELECT
      (SELECT enlem  FROM public.il_merkez WHERE il_key = tr_fold(p_il)) AS h_lat,
      (SELECT boylam FROM public.il_merkez WHERE il_key = tr_fold(p_il)) AS h_lng
  )
  SELECT
    f.kazanan_firma, f.yuklenici_id, f.firma_il, f.kategori_kazanim,
    f.max_kazanim, f.ort_kazanim, f.ayni_il,
    (f.max_kazanim >= COALESCE(p_bedel, 0) * 0.5)              AS kapasite_uygun,
    CASE WHEN h.h_lat IS NOT NULL AND fm.enlem IS NOT NULL
      THEN round((111.0 * sqrt(power(fm.enlem - h.h_lat, 2)
             + power((fm.boylam - h.h_lng) * cos(radians((fm.enlem + h.h_lat)/2)), 2)))::numeric, 0)
      ELSE NULL END                                           AS mesafe_km,
    (
      LEAST(f.kategori_kazanim, 20)::numeric                                     -- deneyim
      + (CASE WHEN f.ayni_il THEN 12 ELSE 0 END)                                 -- aynı il
      + (CASE WHEN f.max_kazanim >= COALESCE(p_bedel, 0) * 0.5 THEN 6 ELSE 0 END)-- kapasite
      + COALESCE(GREATEST(0, 10 - (111.0 * sqrt(power(fm.enlem - h.h_lat, 2)
             + power((fm.boylam - h.h_lng) * cos(radians((fm.enlem + h.h_lat)/2)), 2))) / 60.0), 0) -- yakınlık (0-10, ~600km'de 0)
    )                                                          AS skor
  FROM firma f
  LEFT JOIN public.il_merkez fm ON fm.il_key = tr_fold(f.firma_il)
  CROSS JOIN hedef h
  ORDER BY skor DESC, f.max_kazanim DESC NULLS LAST
  LIMIT p_limit;
$$;

GRANT EXECUTE ON FUNCTION public.ihaleye_uygun_firmalar_geo(text, text, numeric, int, numeric) TO anon, authenticated, service_role;
NOTIFY pgrst, 'reload schema';
