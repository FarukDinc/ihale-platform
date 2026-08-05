-- =============================================================================
-- migration_idare_dizin_detsis_fulljoin.sql — B4 + B2b (İKİ EVREN, kurum tarafı)
-- 5 Ağu 2026
-- =============================================================================
--
-- B4 (isim-anahtar): idare_dizin_json DT/harcama'yı İSİMLE join ediyordu → DT idare
--   adı ihale adından farklı yazılınca (BEL-PA vs BELPA) DT sessiz-0. ÇÖZÜM: detsis_no
--   ile join. dt_idare_ozet_mv'ye detsis_no eklendi.
-- B2b (tek-evren): idare_ozet-çıpalı LEFT JOIN → yalnız-DT kurumlar (ihalesi yok, DT'si
--   var) dizinde YOK. ÇÖZÜM: FULL OUTER JOIN.
--
-- KARTEZYEN TUZAĞI: idare_ozet_mv ve dt_idare_ozet_mv detsis başına ÇOK isim-varyantı
--   satırı taşır (BEL-PA 3 yazım). Ham detsis-FULL-OUTER = varyant×varyant çarpımı +
--   çift sayım. ÇÖZÜM: her tarafı join'DEN ÖNCE birleşik anahtara ÖN-TOPLA.
--   Birleşik anahtar k = COALESCE(detsis_no, 'n:'||idare): detsisli satırlar detsis'e,
--   detsissiz (NULL) satırlar ada gruplanır → detsis-dedup (B4) + isim-fallback tek boruhat.
--
-- Frontend uyumu: v1-kurumlar.detsisGrupla ve v1-kurum-analiz.izDetsisGrupla client'ta
--   detsis'e göre TOPLUYOR. Bu RPC artık detsis başına TEK satır döndürdüğü için o
--   gruplama no-op olur (tek satırın toplamı = kendisi) — çift sayım YOK. Şekil (length-10)
--   ve kolon sırası KORUNDU: [idare,toplam,aktif,en_yakin_il,dt_toplam,dt_aktif,
--   sozlesme_sayisi,toplam_harcama,detsis_no,detsis_ad].
--
-- Uygulama:
--   ssh ihale2 "docker exec -i supabase-db psql -U postgres -d postgres" < backend/migration_idare_dizin_detsis_fulljoin.sql
-- =============================================================================

BEGIN;

-- ── 1) dt_idare_ozet_mv'ye detsis_no ekle (rebuild) ─────────────────────────
-- Gece CONCURRENTLY refresh (run_scraper.sh:211) → unique index (idare) ŞART, owner postgres.
DROP MATERIALIZED VIEW IF EXISTS public.dt_idare_ozet_mv;
CREATE MATERIALIZED VIEW public.dt_idare_ozet_mv AS
  SELECT idare,
         count(*) AS toplam,
         count(*) FILTER (WHERE durum = ANY (ARRAY['Doğrudan Temin Duyurusu Yayımlanmış'::text,
                                                    'Teklifler Değerlendiriliyor'::text])) AS aktif,
         mode() WITHIN GROUP (ORDER BY il) AS en_yakin_il,
         max(detsis_no) AS detsis_no   -- İKİ EVREN kanonik anahtarı (idare_ozet_mv ile aynı desen)
  FROM public.dogrudan_temin_ilanlari
  WHERE idare IS NOT NULL
  GROUP BY idare;
CREATE UNIQUE INDEX idx_dt_idare_ozet_mv_idare ON public.dt_idare_ozet_mv (idare);
ALTER MATERIALIZED VIEW public.dt_idare_ozet_mv OWNER TO postgres;
REVOKE ALL ON public.dt_idare_ozet_mv FROM PUBLIC, anon;

-- ── 2) idare_dizin_json: detsis ön-toplama + FULL OUTER (B4 + B2b) ──────────
CREATE OR REPLACE FUNCTION public.idare_dizin_json()
RETURNS jsonb
LANGUAGE sql STABLE SECURITY DEFINER
SET search_path TO 'public'
SET statement_timeout TO '20s'
AS $function$
  WITH ih AS (   -- ihale: birleşik anahtara ön-topla (detsis varyantları birleşir)
    SELECT COALESCE(detsis_no, 'n:'||idare) AS k,
           max(detsis_no) AS detsis_no,
           (array_agg(idare ORDER BY toplam DESC NULLS LAST))[1] AS idare,   -- kanonik = en çok ihaleli yazım
           sum(toplam)::bigint AS toplam,
           sum(aktif)::bigint  AS aktif,
           (array_agg(en_yakin_il ORDER BY toplam DESC NULLS LAST))[1] AS en_yakin_il
    FROM public.idare_ozet_mv
    GROUP BY COALESCE(detsis_no, 'n:'||idare)
  ),
  dt AS (        -- DT: aynı birleşik anahtara ön-topla
    SELECT COALESCE(detsis_no, 'n:'||idare) AS k,
           max(detsis_no) AS detsis_no,
           (array_agg(idare ORDER BY toplam DESC NULLS LAST))[1] AS idare,
           sum(toplam)::bigint AS toplam,
           sum(aktif)::bigint  AS aktif
    FROM public.dt_idare_ozet_mv
    GROUP BY COALESCE(detsis_no, 'n:'||idare)
  ),
  hrc AS (       -- harcama (ihale-side, isim-keyed) → idare_ozet üzerinden aynı birleşik anahtara topla
    SELECT COALESCE(o.detsis_no, 'n:'||o.idare) AS k,
           sum(h.toplam_harcama)::numeric  AS harcama,
           sum(h.sozlesme_sayisi)::bigint  AS soz
    FROM public.idare_harcama_mv h
    JOIN public.idare_ozet_mv o ON o.idare = h.idare
    GROUP BY COALESCE(o.detsis_no, 'n:'||o.idare)
  )
  SELECT COALESCE(jsonb_agg(
    jsonb_build_array(
      COALESCE(ih.idare, dt.idare),
      COALESCE(ih.toplam, 0), COALESCE(ih.aktif, 0), COALESCE(ih.en_yakin_il, ''),
      COALESCE(dt.toplam, 0), COALESCE(dt.aktif, 0),
      COALESCE(hrc.soz, 0), COALESCE(hrc.harcama, 0),
      COALESCE(ih.detsis_no, dt.detsis_no),
      hi.ad
    ) ORDER BY COALESCE(ih.toplam, 0) DESC), '[]'::jsonb)
  FROM ih
  FULL OUTER JOIN dt  ON dt.k = ih.k                                   -- B2b: yalnız-DT kurumlar dahil
  LEFT JOIN hrc       ON hrc.k = COALESCE(ih.k, dt.k)
  LEFT JOIN public.idare_hiyerarsi hi ON hi.detsis_no = COALESCE(ih.detsis_no, dt.detsis_no);  -- [9] DETSİS resmi ad
$function$;
ALTER FUNCTION public.idare_dizin_json() SET statement_timeout = '20s';
GRANT EXECUTE ON FUNCTION public.idare_dizin_json() TO authenticated, service_role;

COMMIT;

NOTIFY pgrst, 'reload schema';

-- =============================================================================
-- DOĞRULAMA:
--   SELECT jsonb_array_length((idare_dizin_json())->0);            -- 10 olmalı
--   SELECT jsonb_array_length(idare_dizin_json());                 -- kurum sayısı (detsis-dedup)
--   -- BEL-PA tek satır mı: detsis 87767631 kaç kez geçiyor (1 olmalı)
--   -- Yalnız-DT kurum (ihale 0, dt>0) var mı: [1]=0 AND [4]>0 filtrele
-- GECE: dt_idare_ozet_mv CONCURRENTLY refresh zaten var (run_scraper.sh:211).
-- =============================================================================
