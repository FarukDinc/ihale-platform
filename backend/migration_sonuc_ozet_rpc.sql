-- sonuclananlar.html istatistik kartları için tek-çağrı özet (269K+ satır client'a indirilemez).
CREATE OR REPLACE FUNCTION public.sonuc_ozet()
RETURNS TABLE (toplam bigint, toplam_bedel numeric, ort_tenzilat numeric, farkli_firma bigint)
LANGUAGE sql STABLE
AS $$
  SELECT
    count(*),
    sum(COALESCE(kazanan_teklif, sozlesme_bedeli)),
    round(avg(kazanan_teklif_farki_yuzde)
          FILTER (WHERE kazanan_teklif_farki_yuzde IS NOT NULL
                    AND abs(kazanan_teklif_farki_yuzde) <= 100), 1),  -- uç değer koruması (bkz. denetim)
    count(DISTINCT kazanan_firma)
  FROM public.ihale_sonuclari
  WHERE kazanan_firma IS NOT NULL AND kazanan_firma <> '';
$$;

GRANT EXECUTE ON FUNCTION public.sonuc_ozet() TO anon, authenticated, service_role;
NOTIFY pgrst, 'reload schema';
