-- Eşleştirme motoru: bir ihaleye (kategori + il + tahmini bedel) geçmiş kazanımlarına göre EN UYGUN
-- firmaları puanlayarak döndürür. Promena-benzeri e-satınalma + EKAP lead-gen'in temeli.
--
-- v2 iyileştirmeleri:
--  * BÖLGE = kazandığı ihalenin ili (ilanlar.il) → "Bolu/çevrede iş almış firma" (yuklenici_il çoğu null).
--  * KAPASİTE KADEMESİ bir FİLTRE (kullanıcı kuralı: 50M işe hiç 5M üstü iş almamışı ÇAĞIRMA):
--    p_bedel verilince max kazanım >= p_bedel * p_kapasite_esik (varsayılan %10) şartı.
--  * SKOR dengeli: deneyim (üst sınırlı) + aynı il bonusu + yüksek kapasite bonusu.

CREATE INDEX IF NOT EXISTS idx_ilanlar_kategori ON public.ilanlar (kategori);

-- Eski imzayı (5. param'sız) düşür — overload karışıklığını önle
DROP FUNCTION IF EXISTS public.ihaleye_uygun_firmalar(text, text, numeric, int);
DROP FUNCTION IF EXISTS public.ihaleye_uygun_firmalar(text, text, numeric, int, numeric);

CREATE OR REPLACE FUNCTION public.ihaleye_uygun_firmalar(
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
  skor             numeric
)
LANGUAGE sql STABLE
AS $$
  SELECT
    s.kazanan_firma,
    s.yuklenici_id,
    mode() WITHIN GROUP (ORDER BY i.il)                        AS firma_il,
    count(*)                                                   AS kategori_kazanim,
    max(COALESCE(s.kazanan_teklif, s.sozlesme_bedeli))         AS max_kazanim,
    round(avg(COALESCE(s.kazanan_teklif, s.sozlesme_bedeli)))  AS ort_kazanim,
    bool_or(i.il = p_il)                                       AS ayni_il,
    (max(COALESCE(s.kazanan_teklif, s.sozlesme_bedeli)) >= COALESCE(p_bedel, 0) * 0.5) AS kapasite_uygun,
    (
      LEAST(count(*), 20)::numeric                                          -- deneyim (üst sınır 20)
      + (CASE WHEN bool_or(i.il = p_il) THEN 10 ELSE 0 END)                 -- aynı ilde iş almış
      + (CASE WHEN max(COALESCE(s.kazanan_teklif, s.sozlesme_bedeli)) >= COALESCE(p_bedel, 0) * 0.5 THEN 6 ELSE 0 END) -- rahat kapasite
    )                                                          AS skor
  FROM public.ihale_sonuclari s
  JOIN public.ilanlar i ON i.id = s.ilan_id
  WHERE i.kategori = p_kategori
    AND s.kazanan_firma IS NOT NULL
    AND s.kazanan_firma <> ''
  GROUP BY s.kazanan_firma, s.yuklenici_id
  -- KAPASİTE FİLTRESİ: p_bedel verilmişse, hiç bu ölçeğe yakın iş almamış firmaları ELE
  HAVING p_bedel IS NULL
      OR max(COALESCE(s.kazanan_teklif, s.sozlesme_bedeli)) >= p_bedel * p_kapasite_esik
  ORDER BY skor DESC, max_kazanim DESC NULLS LAST
  LIMIT p_limit;
$$;

GRANT EXECUTE ON FUNCTION public.ihaleye_uygun_firmalar(text, text, numeric, int, numeric) TO anon, authenticated, service_role;

NOTIFY pgrst, 'reload schema';
