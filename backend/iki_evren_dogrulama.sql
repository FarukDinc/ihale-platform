-- =============================================================================
-- iki_evren_dogrulama.sql — İKİ EVREN otomatik regresyon testi (5 Ağu 2026)
-- =============================================================================
-- Her bug düzeltmesi için DEĞİŞMEZLİK (invariant) kontrolü. Sabit sayı yerine ilişki
-- kullanır (veri gece büyür) → yıllarca geçerli. Herhangi bir FAIL = regresyon.
--
--   ssh ihale2 "docker exec -i supabase-db psql -U postgres -d postgres" < backend/iki_evren_dogrulama.sql
--   (veya: bash backend/iki_evren_test.sh)
-- =============================================================================
\pset format aligned
\pset border 2
\timing off

WITH
  -- Ortak hesap: idare_dizin_json bir kez çöz, toplamlarını çıkar
  dj AS (SELECT public.idare_dizin_json() AS a),
  djx AS (
    SELECT jsonb_array_length((SELECT a FROM dj))                                        AS kurum_sayisi,
           jsonb_array_length(((SELECT a FROM dj))->0)                                   AS uzunluk,
           (SELECT sum((e->>1)::bigint)  FROM jsonb_array_elements((SELECT a FROM dj)) e) AS ihale_top,
           (SELECT sum((e->>4)::bigint)  FROM jsonb_array_elements((SELECT a FROM dj)) e) AS dt_top,
           (SELECT sum((e->>7)::numeric) FROM jsonb_array_elements((SELECT a FROM dj)) e) AS harcama,
           (SELECT count(*) FROM jsonb_array_elements((SELECT a FROM dj)) e WHERE e->>8='87767631')                        AS belpa_satir,
           (SELECT count(*) FROM jsonb_array_elements((SELECT a FROM dj)) e WHERE (e->>1)::bigint=0 AND (e->>4)::bigint>0) AS dt_only_kurum
  ),
  fob AS (SELECT * FROM public.firma_ozet_birlikte()),
  r(no, ad, gecti, detay) AS (
    VALUES
    -- ── B1: firma birlikte ihale/DT AYRI (toplanmaz) ──────────────────────
    ( 1, 'B1 firma_ozet_birlikte ayri dt_bedel (toplama yok)',
      (SELECT dt_bedel > 0 AND toplam_ciro > dt_bedel FROM fob),
      (SELECT 'ihale_ciro='||round(toplam_ciro/1e9)||'Mr dt_bedel='||round(dt_bedel/1e9)||'Mr' FROM fob) ),

    -- ── B2: DT-only FIRMALAR görünür (FULL OUTER) ─────────────────────────
    ( 2, 'B2 firma_dizin_birlikte DT-only firma iceriyor',
      EXISTS (SELECT 1 FROM public.firma_dizin_birlikte(NULL,NULL,300,0,'bedel',false) WHERE toplam_ciro=0 AND dt_bedel>0),
      'ihale ciro=0 & dt_bedel>0 satiri var mi' ),

    -- ── B4: kurum dizin DT TAM (isimle kayip yok) ─────────────────────────
    ( 4, 'B4 idare_dizin_json DT toplam = tum dt_idare_ozet_mv (kayip yok)',
      (SELECT dt_top FROM djx) = (SELECT COALESCE(sum(toplam),0) FROM public.dt_idare_ozet_mv),
      (SELECT 'dizin_dt='||dt_top||' mv_dt='||(SELECT sum(toplam) FROM public.dt_idare_ozet_mv) FROM djx) ),

    -- ── B4 regresyon: ihale toplami dedup sonrasi DEGISMEDI ───────────────
    ( 5, 'B4 regresyon: ihale toplam = idare_ozet_mv toplam (dedup korudu)',
      (SELECT ihale_top FROM djx) = (SELECT COALESCE(sum(toplam),0) FROM public.idare_ozet_mv),
      (SELECT 'dizin_ihale='||ihale_top FROM djx) ),

    -- ── Harcama regresyon: dizin harcama = idare_harcama_mv (kayip/sisme yok) + sane aralik
    ( 6, 'Harcama regresyon: dizin = idare_harcama_mv toplam & sane aralik',
      (SELECT harcama FROM djx) = (SELECT COALESCE(sum(toplam_harcama),0) FROM public.idare_harcama_mv)
        AND (SELECT harcama FROM djx) BETWEEN 9e12 AND 12e12,
      (SELECT 'harcama='||round(harcama/1e9)||'Mr (9-12tn araligi)' FROM djx) ),

    -- ── B4 dedup: BEL-PA (detsis 87767631) TEK satir ─────────────────────
    ( 7, 'B4 dedup: BEL-PA detsis 87767631 tek satir',
      (SELECT belpa_satir FROM djx) = 1,
      (SELECT 'belpa_satir='||belpa_satir FROM djx) ),

    -- ── B2b: DT-only KURUMLAR görünür ────────────────────────────────────
    ( 8, 'B2b idare_dizin_json DT-only kurum iceriyor',
      (SELECT dt_only_kurum FROM djx) > 0,
      (SELECT 'dt_only_kurum='||dt_only_kurum FROM djx) ),

    -- ── Sekil: idare_dizin_json length-10 ────────────────────────────────
    ( 9, 'Sekil: idare_dizin_json satiri 10 elemanli',
      (SELECT uzunluk FROM djx) = 10,
      (SELECT 'uzunluk='||uzunluk FROM djx) ),

    -- ── B8: ihaleye_uygun_firmalar varyant bolunmesi yok ─────────────────
    (10, 'B8 uygun_firmalar: normalize dedup (0 cift)',
      (SELECT count(*)=count(DISTINCT public.normalize_firma(kazanan_firma))
       FROM public.ihaleye_uygun_firmalar(NULL,'ANKARA',809000,30,'10 KISIM 13 KALEM GIDA MADDESI')),
      'ayni normalize iki satirda cikmamali' ),

    -- ── B10: kurum_dt_ozet kazanan normalize dedup ───────────────────────
    (11, 'B10 kurum_dt_ozet kazanan normalize dedup',
      (SELECT jsonb_array_length(COALESCE(public.kurum_dt_ozet(NULL,'87767631')->'kazanan','[]'::jsonb)) =
              (SELECT count(DISTINCT public.normalize_firma(x->>'grup_deger'))
               FROM jsonb_array_elements(COALESCE(public.kurum_dt_ozet(NULL,'87767631')->'kazanan','[]'::jsonb)) x)),
      'top kazananlarda normalize tekrari yok' ),

    -- ── B7: kategori_sayim_dt calisiyor ──────────────────────────────────
    (12, 'B7 kategori_sayim_dt veri donduruyor',
      (SELECT count(*) > 10 FROM public.kategori_sayim_dt()),
      'DT sektor sayimi dolu' ),

    -- ── B6: il_sektor_ozet_dt calisiyor ──────────────────────────────────
    (13, 'B6 il_sektor_ozet_dt veri donduruyor',
      jsonb_array_length(public.il_sektor_ozet_dt()) > 100,
      'harita DT sektor yogunlugu dolu' ),

    -- ── Harcama guard AŞILDI: MV tanimi >50x filtresi TASIMAMALI ─────────
    (14, 'Harcama: >50x guard YENIDEN eklenmemis (asilmis yaklasim)',
      pg_get_viewdef('public.idare_harcama_mv'::regclass) NOT LIKE '%50 * %'
        AND pg_get_viewdef('public.idare_harcama_mv'::regclass) NOT LIKE '%50*%',
      'ham-temizlik yaklasimi korunuyor (guard yok)' ),

    -- ── Perf: firma_kurum_norm anti-join MV dolu ─────────────────────────
    (15, 'Perf: firma_kurum_norm MV dolu (anti-join hazir)',
      (SELECT count(*) > 100 FROM public.firma_kurum_norm),
      (SELECT 'kurum_norm='||count(*) FROM public.firma_kurum_norm) ),

    -- ── GÜVENLİK: firma-adli RPC/MV anon'a KAPALI ────────────────────────
    (16, 'Guvenlik: firma_dizin_birlikte anon-a KAPALI',
      NOT has_function_privilege('anon','public.firma_dizin_birlikte(text,text,integer,integer,text,boolean)','EXECUTE'),
      'firma adi maskesi' ),
    (17, 'Guvenlik: idare_dizin_json anon-a KAPALI',
      NOT has_function_privilege('anon','public.idare_dizin_json()','EXECUTE'),
      'idare adi maskesi' ),
    (18, 'Guvenlik: firma_dt_toplam MV anon-a KAPALI',
      NOT has_table_privilege('anon','public.firma_dt_toplam','SELECT'),
      'firma adli MV maske' ),
    (19, 'Guvenlik: dt_idare_ozet_mv anon-a KAPALI',
      NOT has_table_privilege('anon','public.dt_idare_ozet_mv','SELECT'),
      'idare adli MV maske' ),

    -- ── AÇIKLIK: sayim RPC-leri anon-a ACIK (KPI/sektor, isimsiz agregat) ─
    (20, 'Aciklik: firma_ozet_birlikte + kategori_sayim_dt anon-a ACIK',
      has_function_privilege('anon','public.firma_ozet_birlikte()','EXECUTE')
        AND has_function_privilege('anon','public.kategori_sayim_dt()','EXECUTE'),
      'isimsiz agregatlar misafire acik' )
  )
SELECT no AS "#", ad AS test,
       CASE WHEN gecti THEN '✅ PASS' ELSE '❌ FAIL' END AS sonuc,
       detay
FROM r ORDER BY no;

-- ÖZET satırı (bash wrapper bunu grep'ler)
WITH
  dj AS (SELECT public.idare_dizin_json() AS a),
  djx AS (SELECT
    (SELECT sum((e->>4)::bigint) FROM jsonb_array_elements((SELECT a FROM dj)) e) dt_top,
    (SELECT sum((e->>1)::bigint) FROM jsonb_array_elements((SELECT a FROM dj)) e) ihale_top,
    (SELECT sum((e->>7)::numeric) FROM jsonb_array_elements((SELECT a FROM dj)) e) harcama,
    (SELECT count(*) FROM jsonb_array_elements((SELECT a FROM dj)) e WHERE e->>8='87767631') belpa,
    (SELECT count(*) FROM jsonb_array_elements((SELECT a FROM dj)) e WHERE (e->>1)::bigint=0 AND (e->>4)::bigint>0) dtonly),
  fob AS (SELECT * FROM public.firma_ozet_birlikte()),
  r(gecti) AS ( VALUES
    ((SELECT dt_bedel>0 AND toplam_ciro>dt_bedel FROM fob)),
    (EXISTS (SELECT 1 FROM public.firma_dizin_birlikte(NULL,NULL,300,0,'bedel',false) WHERE toplam_ciro=0 AND dt_bedel>0)),
    ((SELECT dt_top FROM djx)=(SELECT COALESCE(sum(toplam),0) FROM public.dt_idare_ozet_mv)),
    ((SELECT ihale_top FROM djx)=(SELECT COALESCE(sum(toplam),0) FROM public.idare_ozet_mv)),
    ((SELECT harcama FROM djx)=(SELECT COALESCE(sum(toplam_harcama),0) FROM public.idare_harcama_mv) AND (SELECT harcama FROM djx) BETWEEN 9e12 AND 12e12),
    ((SELECT belpa FROM djx)=1),
    ((SELECT dtonly FROM djx)>0),
    (jsonb_array_length(((SELECT a FROM dj))->0)=10),
    ((SELECT count(*)=count(DISTINCT public.normalize_firma(kazanan_firma)) FROM public.ihaleye_uygun_firmalar(NULL,'ANKARA',809000,30,'10 KISIM 13 KALEM GIDA MADDESI'))),
    ((SELECT jsonb_array_length(COALESCE(public.kurum_dt_ozet(NULL,'87767631')->'kazanan','[]'::jsonb))=(SELECT count(DISTINCT public.normalize_firma(x->>'grup_deger')) FROM jsonb_array_elements(COALESCE(public.kurum_dt_ozet(NULL,'87767631')->'kazanan','[]'::jsonb)) x))),
    ((SELECT count(*)>10 FROM public.kategori_sayim_dt())),
    (jsonb_array_length(public.il_sektor_ozet_dt())>100),
    (pg_get_viewdef('public.idare_harcama_mv'::regclass) NOT LIKE '%50 * %' AND pg_get_viewdef('public.idare_harcama_mv'::regclass) NOT LIKE '%50*%'),
    ((SELECT count(*)>100 FROM public.firma_kurum_norm)),
    (NOT has_function_privilege('anon','public.firma_dizin_birlikte(text,text,integer,integer,text,boolean)','EXECUTE')),
    (NOT has_function_privilege('anon','public.idare_dizin_json()','EXECUTE')),
    (NOT has_table_privilege('anon','public.firma_dt_toplam','SELECT')),
    (NOT has_table_privilege('anon','public.dt_idare_ozet_mv','SELECT')),
    (has_function_privilege('anon','public.firma_ozet_birlikte()','EXECUTE') AND has_function_privilege('anon','public.kategori_sayim_dt()','EXECUTE'))
  )
SELECT 'OZET: gecen='||count(*) FILTER (WHERE gecti)||'/'||count(*)||' kalan_FAIL='||count(*) FILTER (WHERE NOT gecti) AS ozet
FROM r;
