-- ============================================================================
-- migration_qa_26_27_parlayan.sql — 26-27: "Parlayan Yıldızlar"a 0-taban karışması
--   (2 Ağu 2026). Eski seg_parlayan'da OR dalı "yeni gelip büyük iş yapan (ilk kez +
--   son12≥20Mn)" firmaları da Parlayan'a sokuyordu → önceki_12ay=0 olan ilk-kez JV'ler
--   (TAŞYAPI 0→48B, +182.126%) "Parlayan"da görünüyordu. Bunlar zaten seg_ilk_kez'de.
--   FIX: seg_parlayan = YALNIZ gerçek 2x büyüme (önceki döneme dayanan baz var).
--   Fonksiyonun gerisi migration_firma_segmentleri.sql ile birebir aynı.
--
-- Çalıştırma:
--   docker exec -i supabase-db psql -U supabase_admin -d postgres < backend/migration_qa_26_27_parlayan.sql
--   Sonra tazele:  SELECT public.yuklenici_segment_yenile();
-- ============================================================================
CREATE OR REPLACE FUNCTION public.yuklenici_segment_yenile()
RETURNS integer
LANGUAGE plpgsql
AS $$
DECLARE
  ref_tarih date;
  guncellenen integer;
BEGIN
  SELECT max(sonuc_tarihi)::date INTO ref_tarih
  FROM public.ihale_sonuclari
  WHERE sonuc_tarihi <= now();
  IF ref_tarih IS NULL THEN
    ref_tarih := current_date;
  END IF;

  WITH pencere AS (
    SELECT
      public.normalize_firma(s.kazanan_firma) AS normalize_ad,
      SUM(s.kazanan_teklif) FILTER (
        WHERE s.sonuc_tarihi >  (ref_tarih - INTERVAL '12 months')
          AND s.sonuc_tarihi <= ref_tarih)                     AS son12,
      SUM(s.kazanan_teklif) FILTER (
        WHERE s.sonuc_tarihi >  (ref_tarih - INTERVAL '24 months')
          AND s.sonuc_tarihi <= (ref_tarih - INTERVAL '12 months')) AS onceki12,
      COUNT(*) FILTER (
        WHERE s.sonuc_tarihi >  (ref_tarih - INTERVAL '12 months')
          AND s.sonuc_tarihi <= ref_tarih)                     AS say12,
      MIN(s.sonuc_tarihi)::date AS ilk_tarih,
      COALESCE(SUM(s.kazanan_teklif), 0) AS toplam
    FROM public.ihale_sonuclari s
    WHERE s.kazanan_firma IS NOT NULL
      AND public.normalize_firma(s.kazanan_firma) IS NOT NULL
      AND s.sonuc_tarihi IS NOT NULL
    GROUP BY public.normalize_firma(s.kazanan_firma)
  ),
  hesap AS (
    SELECT
      normalize_ad,
      COALESCE(son12, 0)    AS son12,
      COALESCE(onceki12, 0) AS onceki12,
      COALESCE(say12, 0)    AS say12,
      ilk_tarih, toplam,
      CASE WHEN COALESCE(onceki12,0) > 0
           THEN round(((COALESCE(son12,0)::numeric / onceki12) - 1) * 100, 1)
           ELSE NULL END AS buyume
    FROM pencere
  )
  UPDATE public.yukleniciler y SET
    ciro_son_12ay    = h.son12,
    ciro_onceki_12ay = h.onceki12,
    buyume_yuzde     = h.buyume,
    seg_ilk_kez  = (h.ilk_tarih > (ref_tarih - INTERVAL '12 months')::date
                    AND h.toplam >= 100000),
    seg_150mn    = (h.toplam >= 150000000),
    -- 26-27 FIX: yalnız gerçek 2x büyüme (önceki_12ay > 0 baz). OR "ilk kez büyük"
    --            dalı KALDIRILDI → 0-taban first-timer'lar yalnız seg_ilk_kez'de.
    seg_parlayan = (h.son12 >= 5000000 AND h.onceki12 > 0 AND h.son12 >= h.onceki12 * 2),
    seg_sonen    = (h.onceki12 >= 5000000 AND h.son12 <= h.onceki12 * 0.3),
    segment_guncellendi = now()
  FROM hesap h
  WHERE y.normalize_ad = h.normalize_ad;

  GET DIAGNOSTICS guncellenen = ROW_COUNT;
  RETURN guncellenen;
END;
$$;

GRANT EXECUTE ON FUNCTION public.yuklenici_segment_yenile() TO service_role;

-- Hemen tazele (yoksa gece cron'da):
SELECT public.yuklenici_segment_yenile() AS guncellenen_firma;

\echo '--- Parlayan artık 0-taban içermemeli (hepsinin önceki_12ay>0): ---'
SELECT count(*) AS parlayan_toplam,
       count(*) FILTER (WHERE ciro_onceki_12ay > 0) AS onceki_pozitif
  FROM public.yukleniciler WHERE seg_parlayan;
