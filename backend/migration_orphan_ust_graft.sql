-- =============================================================================
-- migration_orphan_ust_graft.sql — Baglantisiz idareleri ust bakanliga greft
-- =============================================================================
-- AMAC: DETSIS agacina baglanamamis 38.614 idareyi (idare_bagsiz_mv) isim-kurali
--   (kaynak='kural', ~%96) + AI (kaynak='ai', residue) ile dogru ust bakanlik
--   dugumune baglar. Mekanizma: idare_tur.detsis_no'yu doldur -> ilan_detsis_esle()
--   ilan/DT satirlarina yayar -> "Baglantisiz Kurumlar" dali erir (%41 -> ~%0,4).
--
-- GERI ALINABILIR: her degisiklik idare_ust_graft_log'a yazilir; kaynak IN
--   ('kural','ai') + guven<=45 ile isaretli. Geri alma icin log'dan idare_norm'lari
--   alip idare_tur.detsis_no=NULL yap + ilan_detsis_esle tekrar (veya null'la).
--
-- ONKOSUL: public.graft_stg(idare_ad,hedef,kaynak) yuklu olmali (final_mapping.csv).
-- CALISTIRMA: docker exec -i supabase-db psql -U postgres -d postgres < bu_dosya
-- =============================================================================
\set ON_ERROR_STOP on
BEGIN;

-- 1) YENI KOK: YUKSEKOGRETIM KURUMLARI (YOK) — universiteler icin temiz kok yok
INSERT INTO public.idare_hiyerarsi(detsis_no, ad, ust_detsis_no, seviye)
VALUES ('YOK', 'YÜKSEKÖĞRETİM KURUMLARI (YÖK)', NULL, 0)
ON CONFLICT (detsis_no) DO NOTHING;

INSERT INTO public.idare_ata_torun(ata_no, torun_no, mesafe)
SELECT 'YOK', 'YOK', 0
WHERE NOT EXISTS (SELECT 1 FROM public.idare_ata_torun WHERE ata_no='YOK' AND torun_no='YOK');

-- 2) graft_map: norm basina TEK satir (kural, ai'dan onceliklidir); hedef normalize
DROP TABLE IF EXISTS public.graft_map;
CREATE TABLE public.graft_map AS
SELECT DISTINCT ON (public.idare_normalize(idare_ad))
       public.idare_normalize(idare_ad) AS idare_norm,
       idare_ad,
       CASE WHEN hedef IN ('YOK-YENI','YOK') THEN 'YOK' ELSE hedef END AS hedef,
       kaynak
FROM public.graft_stg
WHERE idare_ad IS NOT NULL AND btrim(idare_ad) <> ''
ORDER BY public.idare_normalize(idare_ad), (kaynak='kural') DESC;

CREATE INDEX ON public.graft_map(idare_norm);

-- 2b) GUVENLIK: tum hedefler gecerli agac dugumu mu? degilse ABORT
DO $$
DECLARE gecersiz int;
BEGIN
  SELECT count(*) INTO gecersiz
  FROM public.graft_map m
  WHERE NOT EXISTS (SELECT 1 FROM public.idare_hiyerarsi h WHERE h.detsis_no=m.hedef);
  IF gecersiz > 0 THEN
    RAISE EXCEPTION 'ABORT: % gecersiz hedef detsis_no (agacta yok)', gecersiz;
  END IF;
END $$;

-- 3) geri-alma log
DROP TABLE IF EXISTS public.idare_ust_graft_log;
CREATE TABLE public.idare_ust_graft_log(
  idare_norm text, eski_detsis text, yeni_detsis text,
  kaynak text, islem text, zaman timestamptz DEFAULT now());

-- 4a) UPDATE: idare_tur'da var, detsis NULL, otoriter DEGIL
WITH upd AS (
  UPDATE public.idare_tur t
     SET detsis_no  = m.hedef,
         kaynak     = m.kaynak,
         guven      = CASE WHEN m.kaynak='kural' THEN 45 ELSE 35 END,
         ust_kurum  = NULL,
         guncelleme = now()
    FROM public.graft_map m
   WHERE t.idare_norm = m.idare_norm
     AND t.detsis_no IS NULL
     AND t.kaynak <> 'ekap-detsis'
  RETURNING t.idare_norm, m.hedef, m.kaynak
)
INSERT INTO public.idare_ust_graft_log(idare_norm, eski_detsis, yeni_detsis, kaynak, islem)
SELECT idare_norm, NULL, hedef, kaynak, 'update' FROM upd;

-- 4b) INSERT: idare_tur'da hic yok
WITH ins AS (
  INSERT INTO public.idare_tur(idare_norm, idare_ad, tur, detsis_no, kaynak, guven)
  SELECT m.idare_norm, m.idare_ad, 'ust_kural', m.hedef, m.kaynak,
         CASE WHEN m.kaynak='kural' THEN 45 ELSE 35 END
    FROM public.graft_map m
   WHERE NOT EXISTS (SELECT 1 FROM public.idare_tur t WHERE t.idare_norm = m.idare_norm)
  RETURNING idare_norm, detsis_no, kaynak
)
INSERT INTO public.idare_ust_graft_log(idare_norm, eski_detsis, yeni_detsis, kaynak, islem)
SELECT idare_norm, NULL, detsis_no, kaynak, 'insert' FROM ins;

-- 5) OZET
SELECT 'graft_map tekil: '   || (SELECT count(*) FROM public.graft_map)      AS ozet
UNION ALL SELECT 'log update: '  || (SELECT count(*) FROM public.idare_ust_graft_log WHERE islem='update')
UNION ALL SELECT 'log insert: '  || (SELECT count(*) FROM public.idare_ust_graft_log WHERE islem='insert');

COMMIT;
