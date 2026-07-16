-- Uluslararası ihaleler dünya haritası: ülke bazında ihale sayısı (ulke_kodu = ISO-A3).
CREATE OR REPLACE FUNCTION public.ulke_ihale_dagilimi()
RETURNS TABLE(ulke_kodu text, ulke text, adet bigint)
LANGUAGE sql STABLE
AS $$
  SELECT ulke_kodu, max(ulke), count(*)::bigint
  FROM public.uluslararasi_ihaleler
  WHERE ulke_kodu IS NOT NULL AND btrim(ulke_kodu) <> ''
  GROUP BY ulke_kodu;
$$;
GRANT EXECUTE ON FUNCTION public.ulke_ihale_dagilimi() TO anon, authenticated, service_role;
NOTIFY pgrst, 'reload schema';
