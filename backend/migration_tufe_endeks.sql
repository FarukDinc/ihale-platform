-- ============================================================
-- TÜFE BUGÜNKÜ-DEĞER — enflasyon düzeltmeli tutar (25 Tem 2026)
-- Kaynak: TÜİK Tüketici Fiyat Endeksi (2003=100), YILLIK ORTALAMA.
--   https://www.hakedis.org/endeksler/tuketici-fiyat-genel-endeksi-ve-degisim-oranlari-2003
-- js/tufe.js ile BİREBİR aynı değerler (frontend ile tutarlılık şart).
-- Server-side kullanım: RPC'ler bugünkü-değer döndürmek isterse bu fonksiyonu çağırır.
-- ============================================================

BEGIN;

CREATE TABLE IF NOT EXISTS public.tufe_endeks (
  yil    int PRIMARY KEY,
  endeks numeric NOT NULL   -- 2003=100 bazlı yıllık ortalama
);

INSERT INTO public.tufe_endeks (yil, endeks) VALUES
  (2003, 100.00),
  (2004, 107.51), (2005, 117.51), (2006, 129.18), (2007, 140.44),
  (2008, 153.27), (2009, 164.50), (2010, 178.48), (2011, 189.58),
  (2012, 207.20), (2013, 222.49), (2014, 241.35), (2015, 261.30),
  (2016, 282.21), (2017, 313.08), (2018, 360.70), (2019, 418.58),
  (2020, 473.51), (2021, 569.03), (2022, 957.12), (2023, 1439.61),
  (2024, 2359.35), (2025, 3132.76), (2026, 3953.93)
ON CONFLICT (yil) DO UPDATE SET endeks = EXCLUDED.endeks;

-- Nominal tutarı sözleşme tarihine göre BUGÜNKÜ TL'ye çevirir.
-- Çeviremezse (tarih/endeks yok) nominal'i aynen döndürür.
CREATE OR REPLACE FUNCTION public.tufe_bugune(tutar bigint, tarih timestamptz)
RETURNS bigint
LANGUAGE plpgsql STABLE
AS $$
DECLARE
  y int;
  guncel numeric;
  taban numeric;
BEGIN
  IF tutar IS NULL OR tarih IS NULL THEN RETURN tutar; END IF;
  SELECT max(yil), (SELECT endeks FROM public.tufe_endeks ORDER BY yil DESC LIMIT 1)
    INTO y, guncel FROM public.tufe_endeks;
  y := extract(year FROM tarih)::int;
  IF y < 2003 THEN y := 2003; END IF;
  SELECT endeks INTO taban FROM public.tufe_endeks
    WHERE yil = LEAST(y, (SELECT max(yil) FROM public.tufe_endeks));
  IF taban IS NULL OR taban = 0 THEN RETURN tutar; END IF;
  RETURN round(tutar * (guncel / taban))::bigint;
END;
$$;

GRANT SELECT ON public.tufe_endeks TO anon, authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.tufe_bugune(bigint, timestamptz) TO anon, authenticated, service_role;

COMMIT;

NOTIFY pgrst, 'reload schema';

-- Test: SELECT public.tufe_bugune(1000000, '2015-06-01');  -- ~15,1 Mn beklenir
