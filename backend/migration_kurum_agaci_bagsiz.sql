-- =============================================================================
-- migration_kurum_agaci_bagsiz.sql — Kurum Ağacı: "Bağlantısız Kurumlar" dalı
-- =============================================================================
--
-- AMAÇ (YAPILACAKLAR #3): kurum-analiz.html'deki yeni Kurum Ağacı sekmesi,
-- DETSİS ağacına BAĞLANAMAYAN (ilanlar/DT satırında detsis_no IS NULL kalan)
-- idareleri AYRI BİR DAL olarak göstermek zorunda — gizlenirse kullanıcı
-- toplamların eksik olduğunu sanır. Mevcut 4 ağaç RPC'si
-- (migration_idare_agac_rpc.sql) yalnız ağaca bağlı düğümleri döner; bu dosya
-- bağlantısız tarafı ve kapsama oranını sağlar.
--
-- ÖNKOŞUL: migration_idare_agac_rpc.sql (ilanlar.detsis_no + DT.detsis_no
-- kolonları ve partial indeksleri kurulmuş olmalı).
--
-- NEDEN MV: bağlantısız kurum listesi "ilanlar WHERE detsis_no IS NULL GROUP BY
-- idare" demek — partial indeks (WHERE detsis_no IS NOT NULL) bu sorguya
-- YARDIM ETMEZ, 356K ilan + 1,49M DT satırında canlı GROUP BY her açılışta
-- seq-scan olurdu (bkz. hafıza statement-timeout-edge). Veri yalnız gece
-- scraper turunda değiştiği için MV + gece REFRESH yeterli.
--
-- ANON'A KAPALI: idare adı bu projede kimlik verisi (migration_anon_maske.sql).
-- Self-hosted Supabase'de yeni MV/fonksiyon varsayılan ayrıcalıkla DOĞUŞTAN
-- açık gelir → REVOKE'lar AÇIKÇA yazıldı (18 Tem dersi, migration_dt_anon_fix.sql).
--
-- Uygulama:
--   docker exec -i supabase-db psql -U postgres -d postgres < backend/migration_kurum_agaci_bagsiz.sql
-- =============================================================================

BEGIN;

-- ---------------------------------------------------------------------------
-- 1) idare_bagsiz_mv — DETSİS ağacına eşlenemeyen idareler + ihale/DT sayıları
--    FULL JOIN: kimi idare yalnız ihalede, kimi yalnız DT'de görünür.
-- ---------------------------------------------------------------------------
DROP MATERIALIZED VIEW IF EXISTS public.idare_bagsiz_mv;
CREATE MATERIALIZED VIEW public.idare_bagsiz_mv AS
WITH ih AS (
  SELECT i.idare, count(*)::bigint AS ihale_sayisi
    FROM public.ilanlar i
   WHERE i.detsis_no IS NULL AND i.idare IS NOT NULL
   GROUP BY i.idare
),
dt AS (
  SELECT d.idare, count(*)::bigint AS dt_sayisi
    FROM public.dogrudan_temin_ilanlari d
   WHERE d.detsis_no IS NULL AND d.idare IS NOT NULL
   GROUP BY d.idare
)
SELECT COALESCE(ih.idare, dt.idare)        AS idare,
       COALESCE(ih.ihale_sayisi, 0)::bigint AS ihale_sayisi,
       COALESCE(dt.dt_sayisi, 0)::bigint    AS dt_sayisi
  FROM ih
  FULL JOIN dt ON dt.idare = ih.idare;

-- REFRESH ... CONCURRENTLY için zorunlu benzersiz indeks
CREATE UNIQUE INDEX idx_idare_bagsiz_mv_idare
  ON public.idare_bagsiz_mv (idare);
CREATE INDEX idx_idare_bagsiz_mv_sirala
  ON public.idare_bagsiz_mv (ihale_sayisi DESC, dt_sayisi DESC);

ANALYZE public.idare_bagsiz_mv;

-- Önce REVOKE, sonra dar GRANT (yeni MV doğuştan anon-açık gelebilir)
REVOKE ALL   ON public.idare_bagsiz_mv FROM PUBLIC, anon;
GRANT SELECT ON public.idare_bagsiz_mv TO authenticated, service_role;

-- ---------------------------------------------------------------------------
-- 2) idare_agac_bagsiz_ozet() — kapsama şeridi + "Bağlantısız Kurumlar" kök
--    düğümünün sayıları. Ağaç sekmesi açılışında BİR KEZ çağrılır (istemci
--    30 dk sessionStorage önbelleği tutar).
--
--    bagsiz = tum - esli olarak hesaplanır: "detsis_no IS NOT NULL" sayımı
--    partial indeksle (idx_ilanlar_detsis / idx_dt_ilanlari_detsis) index-only
--    gider; "IS NULL" sayımı ise seq-scan gerektirirdi.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION public.idare_agac_bagsiz_ozet()
RETURNS jsonb
LANGUAGE sql STABLE
AS $$
  WITH s AS (
    SELECT (SELECT count(*) FROM public.ilanlar)                                          AS tum_ihale,
           (SELECT count(*) FROM public.ilanlar WHERE detsis_no IS NOT NULL)              AS esli_ihale,
           (SELECT count(*) FROM public.dogrudan_temin_ilanlari)                          AS tum_dt,
           (SELECT count(*) FROM public.dogrudan_temin_ilanlari WHERE detsis_no IS NOT NULL) AS esli_dt,
           (SELECT count(*) FROM public.idare_bagsiz_mv)                                  AS kurum_sayisi
  )
  SELECT jsonb_build_object(
    'kurum_sayisi', kurum_sayisi,
    'tum_ihale',    tum_ihale,
    'esli_ihale',   esli_ihale,
    'bagsiz_ihale', tum_ihale - esli_ihale,
    'tum_dt',       tum_dt,
    'esli_dt',      esli_dt,
    'bagsiz_dt',    tum_dt - esli_dt
  ) FROM s;
$$;

-- count(*) 1,49M DT satırında birkaç yüz ms; 3s varsayılanın kenarında sürpriz
-- yaşamamak için pay bırak (idare_dizin_json ile aynı desen).
ALTER FUNCTION public.idare_agac_bagsiz_ozet() SET statement_timeout = '15s';

-- ---------------------------------------------------------------------------
-- 3) idare_agac_bagsiz_liste(q, limit, offset) — bağlantısız dalın "çocukları"
--    Tembel açılım: dala tıklanınca 50'şerli sayfalarla iner; arama kutusu da
--    aynı RPC'yi p_q ile kullanır (ağaç aramasının bağlantısız ayağı).
--    tr_fold: Türkçe İ/ı ikilisi ilike'ta sessizce 0 döndürüyor
--    (bkz. hafıza ilike-tr-locale-tuzagi).
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION public.idare_agac_bagsiz_liste(
  p_q text DEFAULT NULL, p_limit integer DEFAULT 50, p_offset integer DEFAULT 0
)
RETURNS TABLE (idare text, ihale_sayisi bigint, dt_sayisi bigint)
LANGUAGE sql STABLE
AS $$
  SELECT b.idare, b.ihale_sayisi, b.dt_sayisi
    FROM public.idare_bagsiz_mv b
   WHERE p_q IS NULL OR length(btrim(p_q)) < 2
      OR public.tr_fold(b.idare) LIKE '%' || public.tr_fold(btrim(p_q)) || '%'
   ORDER BY b.ihale_sayisi DESC, b.dt_sayisi DESC, b.idare
   LIMIT  LEAST(COALESCE(p_limit, 50), 200)
  OFFSET GREATEST(COALESCE(p_offset, 0), 0);
$$;

-- ---------------------------------------------------------------------------
-- 4) YETKİLER — ağaç RPC'leriyle aynı: giriş şartlı
-- ---------------------------------------------------------------------------
REVOKE EXECUTE ON FUNCTION public.idare_agac_bagsiz_ozet()                        FROM PUBLIC, anon;
REVOKE EXECUTE ON FUNCTION public.idare_agac_bagsiz_liste(text, integer, integer) FROM PUBLIC, anon;

GRANT EXECUTE ON FUNCTION public.idare_agac_bagsiz_ozet()                        TO authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.idare_agac_bagsiz_liste(text, integer, integer) TO authenticated, service_role;

COMMIT;

NOTIFY pgrst, 'reload schema';

-- =============================================================================
-- KURULUM SONRASI
-- =============================================================================
-- Gece zinciri: run_scraper.sh'te ilan_detsis_esle + sayim_mv REFRESH'inin
-- HEMEN ARKASINA eklendi (aynı commit):
--   REFRESH MATERIALIZED VIEW CONCURRENTLY public.idare_bagsiz_mv;
--
-- DOĞRULAMA (psql, service_role/superuser):
--   SELECT public.idare_agac_bagsiz_ozet();
--   -- bagsiz_ihale + esli_ihale = tum_ihale OLMALI
--   SELECT * FROM public.idare_agac_bagsiz_liste(NULL, 5, 0);
--   SELECT * FROM public.idare_agac_bagsiz_liste('belediye', 5, 0);
--
-- ANON DOĞRULAMASI (deploy sonrası ŞART — bkz. hafıza anon-maske):
--   curl -s -o /dev/null -w '%{http_code}\n' \
--     -H "apikey: $ANON" -H "Authorization: Bearer $ANON" \
--     -X POST https://ihaleglobal.com/rest/v1/rpc/idare_agac_bagsiz_liste \
--     -H 'Content-Type: application/json' -d '{}'
--   -- beklenen: 401/403/404 (200 DÖNMEMELİ)
--   curl -s -o /dev/null -w '%{http_code}\n' \
--     -H "apikey: $ANON" -H "Authorization: Bearer $ANON" \
--     "https://ihaleglobal.com/rest/v1/idare_bagsiz_mv?select=idare&limit=1"
--   -- beklenen: 401/403/404 (200 DÖNMEMELİ)
