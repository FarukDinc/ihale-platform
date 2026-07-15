-- Eşleştirme motoru: bir ihaleye (kategori + il + tahmini bedel) geçmiş kazanımlarına göre EN UYGUN
-- firmaları puanlayarak döndürür. Promena-benzeri e-satınalma + EKAP lead-gen'in temeli.
-- Puanlama: kategoride kazanım sayısı + aynı il bonusu + KAPASİTE kademesi (bu ölçekte iş almış mı).

CREATE INDEX IF NOT EXISTS idx_ilanlar_kategori ON public.ilanlar (kategori);

CREATE OR REPLACE FUNCTION public.ihaleye_uygun_firmalar(
  p_kategori text,
  p_il      text    DEFAULT NULL,
  p_bedel   numeric DEFAULT NULL,
  p_limit   int     DEFAULT 20
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
  skor             numeric
)
LANGUAGE sql STABLE
AS $$
  SELECT
    s.kazanan_firma,
    s.yuklenici_id,
    max(s.yuklenici_il)                                        AS firma_il,
    count(*)                                                   AS kategori_kazanim,
    max(COALESCE(s.kazanan_teklif, s.sozlesme_bedeli))         AS max_kazanim,
    round(avg(COALESCE(s.kazanan_teklif, s.sozlesme_bedeli)))  AS ort_kazanim,
    bool_or(s.yuklenici_il = p_il)                             AS ayni_il,
    (max(COALESCE(s.kazanan_teklif, s.sozlesme_bedeli)) >= COALESCE(p_bedel, 0) * 0.15) AS kapasite_uygun,
    (
      count(*)::numeric
      + (CASE WHEN bool_or(s.yuklenici_il = p_il) THEN 5 ELSE 0 END)
      + (CASE WHEN max(COALESCE(s.kazanan_teklif, s.sozlesme_bedeli)) >= COALESCE(p_bedel, 0) * 0.15 THEN 3 ELSE 0 END)
    )                                                          AS skor
  FROM public.ihale_sonuclari s
  JOIN public.ilanlar i ON i.id = s.ilan_id
  WHERE i.kategori = p_kategori
    AND s.kazanan_firma IS NOT NULL
    AND s.kazanan_firma <> ''
  GROUP BY s.kazanan_firma, s.yuklenici_id
  ORDER BY skor DESC, max_kazanim DESC NULLS LAST
  LIMIT p_limit;
$$;

GRANT EXECUTE ON FUNCTION public.ihaleye_uygun_firmalar(text, text, numeric, int) TO anon, authenticated, service_role;

NOTIFY pgrst, 'reload schema';
