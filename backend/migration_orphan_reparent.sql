-- =============================================================================
-- migration_orphan_reparent.sql — Sentetik "Baglantisiz" dugumlerini re-parent
-- =============================================================================
-- AMAC: idare_hiyerarsi'de ust_detsis_no='-999999' (Baglantisiz Kurumlar) altinda
--   asili 17.326 sentetik yaprak dugumun ~17.230'unu, adlarinda GOMULU bakanliktan
--   (isim-kurali + AI ile) dogru ust bakanlik KOKUNE tasir. "Baglantisiz Kurumlar"
--   dali 215K ihale -> ~0'a iner; bakanliklar altinda gorunur.
--
-- DURABILITE: idare_hiyerarsi.ust_detsis_no gece DEGISMIYOR; idare_kapanis_uret()
--   closure'i BUNDAN turetiyor -> re-parent gece korunur (bkz. run_scraper.sh).
-- CLOSURE: TRUNCATE'siz HEDEFLI guncelleme (dugumler YAPRAK; hedefler KOK) -> canli
--   site kilidi yok. Gece kapanis_uret() zaten tam tutarli yeniden kurar.
-- GERI ALINABILIR: idare_reparent_log (detsis, eski_ust, yeni_ust).
--
-- ONKOSUL: public.sent_stg(detsis,hedef,kaynak) yuklu (sentetik_final.csv).
-- CALISTIRMA: docker exec -i supabase-db psql -U postgres -d postgres < bu_dosya
-- =============================================================================
\set ON_ERROR_STOP on
BEGIN;

-- 0) GUVENLIK: tum hedefler gecerli KOK dugum mu?
DO $$
DECLARE bad int;
BEGIN
  SELECT count(*) INTO bad FROM public.sent_stg s
   WHERE NOT EXISTS (SELECT 1 FROM public.idare_hiyerarsi h WHERE h.detsis_no=s.hedef AND h.ust_detsis_no IS NULL);
  IF bad > 0 THEN RAISE EXCEPTION 'ABORT: % hedef gecerli kok degil', bad; END IF;
END $$;

-- 1) geri-alma log (yalniz -999999 altindaki hedeflenen dugumler)
DROP TABLE IF EXISTS public.idare_reparent_log;
CREATE TABLE public.idare_reparent_log(
  detsis text, eski_ust text, yeni_ust text, kaynak text, zaman timestamptz DEFAULT now());
INSERT INTO public.idare_reparent_log(detsis, eski_ust, yeni_ust, kaynak)
SELECT h.detsis_no, h.ust_detsis_no, s.hedef, s.kaynak
  FROM public.idare_hiyerarsi h
  JOIN public.sent_stg s ON s.detsis = h.detsis_no
 WHERE h.ust_detsis_no = '-999999';

-- 2) re-parent: ust_detsis_no -> hedef bakanlik koku
UPDATE public.idare_hiyerarsi h
   SET ust_detsis_no = s.hedef, guncelleme = now()
  FROM public.sent_stg s
 WHERE h.detsis_no = s.detsis
   AND h.ust_detsis_no = '-999999';

-- 3) CLOSURE hedefli guncelleme (yaprak dugum -> kok, mesafe 1)
--    eski -999999 ata baglarini sil
DELETE FROM public.idare_ata_torun a
 USING public.idare_reparent_log g
 WHERE a.torun_no = g.detsis AND a.ata_no = '-999999';
--    yeni bakanlik ata bagini ekle (kendi (detsis,detsis,0) zaten duruyor)
INSERT INTO public.idare_ata_torun(ata_no, torun_no, mesafe)
SELECT g.yeni_ust, g.detsis, 1 FROM public.idare_reparent_log g
ON CONFLICT (ata_no, torun_no) DO NOTHING;

-- 4) ozet
SELECT 'reparent edilen dugum: ' || (SELECT count(*) FROM public.idare_reparent_log) AS ozet
UNION ALL SELECT 'hala -999999 altinda kalan: '
  || (SELECT count(*) FROM public.idare_hiyerarsi WHERE ust_detsis_no='-999999');

COMMIT;
