-- =============================================================================
-- migration_orphan_junkroot.sql — Kok'e cikmis alt-birimleri bakanliga bagla
-- =============================================================================
-- AMAC: DETSIS yuklemesinde ust_detsis_no NULL kalmis (yanlislikla ROOT olmus)
--   ~40 alt-birimi (cogu askeri: komutanlik/gazino/orduevi/TCG + Et-Sut, BOTAS,
--   jandarma, sosyal hizmetler) dogru ust bakanliga tasir. Bunlar -999999 altinda
--   DEGIL; dogrudan hatali kok. 3 bare belirsiz (LOJISTIK/SATIN ALMA SUBE, 0 ihale)
--   dokunulmadan birakildi.
-- CLOSURE: TRUNCATE'siz hedefli — junk kok YAPRAK degilse (cocuklu) diye kok'un
--   KENDISI + TUM torunlari icin (hedef, torun, mesafe+1) eklenir.
-- DURABILITE: ust_detsis_no gece degismez; kapanis_uret closure'i bundan turetir.
-- GERI ALINABILIR: idare_junkroot_log.
-- ONKOSUL: public.junk_stg(detsis,hedef) yuklu (junk_map.csv).
-- =============================================================================
\set ON_ERROR_STOP on
BEGIN;

-- 0a) hedefler gecerli KOK mu?
DO $$ DECLARE bad int; BEGIN
  SELECT count(*) INTO bad FROM public.junk_stg s
   WHERE NOT EXISTS (SELECT 1 FROM public.idare_hiyerarsi h WHERE h.detsis_no=s.hedef AND h.ust_detsis_no IS NULL);
  IF bad>0 THEN RAISE EXCEPTION 'ABORT: % hedef gecerli kok degil', bad; END IF;
END $$;
-- 0b) kaynaklar SU AN kok mu? (yanlislikla baskasini tasima)
DO $$ DECLARE bad int; BEGIN
  SELECT count(*) INTO bad FROM public.junk_stg s
   JOIN public.idare_hiyerarsi h ON h.detsis_no=s.detsis WHERE h.ust_detsis_no IS NOT NULL;
  IF bad>0 THEN RAISE EXCEPTION 'ABORT: % kaynak zaten kok degil', bad; END IF;
END $$;

-- 1) geri-alma log
DROP TABLE IF EXISTS public.idare_junkroot_log;
CREATE TABLE public.idare_junkroot_log(detsis text, eski_ust text, yeni_ust text, zaman timestamptz DEFAULT now());
INSERT INTO public.idare_junkroot_log(detsis, eski_ust, yeni_ust)
SELECT s.detsis, NULL, s.hedef FROM public.junk_stg s;

-- 2) re-parent
UPDATE public.idare_hiyerarsi h
   SET ust_detsis_no = s.hedef, guncelleme = now()
  FROM public.junk_stg s WHERE h.detsis_no = s.detsis;

-- 3) closure hedefli: hedef -> (junk kok + tum torunlari), mesafe+1
INSERT INTO public.idare_ata_torun(ata_no, torun_no, mesafe)
SELECT s.hedef, at.torun_no, at.mesafe + 1
  FROM public.junk_stg s
  JOIN public.idare_ata_torun at ON at.ata_no = s.detsis
ON CONFLICT (ata_no, torun_no) DO NOTHING;

-- 4) ozet
SELECT 'reparent edilen: ' || (SELECT count(*) FROM public.idare_junkroot_log) AS ozet
UNION ALL SELECT 'kalan pozitif kok (bakanlik+yuksek yargi+3 belirsiz): ' || (
  SELECT count(*) FROM public.idare_hiyerarsi WHERE ust_detsis_no IS NULL AND detsis_no !~ '^-' AND detsis_no<>'YOK');

COMMIT;
