-- =============================================================================
-- migration_firma_birlikte_iki_evren.sql — B1 (toplama) + B2 (DT-only kaybı)
-- İKİ EVREN dikiş-hatası düzeltmesi · 5 Ağu 2026
-- =============================================================================
--
-- SORUN (İKI_EVREN_BULGULAR.md):
--   B1 TOPLAMA: "İkisi/Birlikte" görünümü ihale cirosu (milyon) + DT bedeli
--     (~₺37K medyan) TEK "Toplam Ciro"ya topluyordu → yanıltıcı (Kural 3 ihlali).
--   B2 DT-ONLY KAYBOLUYOR: firma_dizin_birlikte LEFT JOIN firma_dt_toplam
--     (ihale-çıpalı) → yalnız-DT firmalar (213.340 / 280.294 = %76!) listede YOK.
--
-- ÇÖZÜM:
--   1) firma_ozet_birlikte + firma_dizin_birlikte: ihale ciro/sözleşme AYRI alan,
--      DT bedel/sözleşme AYRI alan — HİÇBİR yerde toplanmaz (B1).
--   2) LEFT JOIN → FULL OUTER JOIN: yalnız-DT firmalar da görünür (B2).
--
-- PERF (kritik): eski firma_dizin_birlikte `NOT firma_kurum_mu(ad)` filtresini
--   220K satırda satır-satır çağırıyordu → ~19,3 s (20 s timeout KENARINDA, zaten
--   kırılgandı). FULL OUTER ile ~490K satır olunca 22 s (TIMEOUT). firma_kurum_mu
--   IMMUTABLE + saf isim-tabanlı ve kurum-firma kümesi MİNİK (2.479) → küçük bir
--   MV'ye (firma_kurum_norm) materyalize edip ANTI-JOIN yapıyoruz: 19,3 s → 0,38 s.
--   Bu hem B1/B2'yi çözer hem önceki kırılganlığı giderir (tablo/MV rebuild YOK).
--
-- ŞEKİL DEĞİŞİMİ (geriye-uyum): toplam_ciro / toplam_sozlesme(_sayisi) KOLONLARI
--   KORUNDU ama artık İHALE-ONLY (eskiden ihale+DT toplamı). Eski tüketiciler
--   (index.html .toplam, v1-benim-sayfam .toplam, v1-firma-analiz .toplam_ciro)
--   KIRILMAZ — yalnız yanıltıcı toplam → doğru ihale-only olur. DT için AYRI
--   kolonlar eklendi (dt_sozlesme, dt_bedel, dt_sozlesme_sayisi).
--
-- Uygulama:
--   ssh ihale2 "docker exec -i supabase-db psql -U postgres -d postgres" < backend/migration_firma_birlikte_iki_evren.sql
-- =============================================================================

BEGIN;

-- ── 1) Kurum-firma anahtar kümesi (anti-join için) ──────────────────────────
-- firma_kurum_mu() IMMUTABLE + isim-tabanlı; eşleşen küme minik (~2.5K). Satır-
-- satır fonksiyon yerine bu MV'ye NOT IN → 50× hız. Gece firma_dt_toplam
-- tazelendikten SONRA tazelenmeli (bkz. gece refresh cron).
DROP MATERIALIZED VIEW IF EXISTS public.firma_kurum_norm;
CREATE MATERIALIZED VIEW public.firma_kurum_norm AS
  SELECT fn FROM (
    SELECT normalize_ad AS fn FROM public.yukleniciler   WHERE public.firma_kurum_mu(ad)
    UNION
    SELECT firma_norm  AS fn FROM public.firma_dt_toplam WHERE public.firma_kurum_mu(ad)
  ) u WHERE fn IS NOT NULL;
CREATE UNIQUE INDEX firma_kurum_norm_pk ON public.firma_kurum_norm(fn);
ALTER MATERIALIZED VIEW public.firma_kurum_norm OWNER TO postgres;   -- gece REFRESH -U postgres
REVOKE ALL ON public.firma_kurum_norm FROM PUBLIC, anon;             -- yeni MV → REVOKE ŞART
GRANT SELECT ON public.firma_kurum_norm TO authenticated, service_role;

-- ── 2) firma_ozet_birlikte() — KPI (anon'a AÇIK; homepage sayacı) ───────────
-- toplam = union firma sayısı (DEĞİŞMEDİ). toplam_sozlesme/toplam_ciro artık
-- İHALE-ONLY. dt_sozlesme/dt_bedel AYRI. Toplama YOK.
DROP FUNCTION IF EXISTS public.firma_ozet_birlikte();
CREATE FUNCTION public.firma_ozet_birlikte()
RETURNS TABLE(toplam bigint, toplam_sozlesme bigint, toplam_ciro numeric,
              ortak_sayisi bigint, dt_sozlesme bigint, dt_bedel numeric)
LANGUAGE sql STABLE SECURITY DEFINER
SET search_path TO 'public'
AS $function$
  WITH ih AS (SELECT toplam_sozlesme, toplam_ciro, ortak_sayisi FROM public.yuklenici_ozet_mv),
       dt AS (SELECT COALESCE(sum(dt_sozlesme),0) s, COALESCE(sum(dt_bedel),0) b
                FROM public.firma_dt_toplam),
       birlesik AS (SELECT count(*) n FROM (
                     SELECT normalize_ad AS x FROM public.yukleniciler WHERE normalize_ad IS NOT NULL
                     UNION
                     SELECT firma_norm FROM public.firma_dt_toplam) u)
  SELECT (SELECT n FROM birlesik)::bigint,
         (SELECT toplam_sozlesme FROM ih)::bigint,   -- İHALE-only (DT ile TOPLANMAZ)
         (SELECT toplam_ciro     FROM ih)::numeric,   -- İHALE-only
         (SELECT ortak_sayisi    FROM ih)::bigint,    -- İHALE-only
         (SELECT s FROM dt)::bigint,                   -- DT sözleşme sayısı (AYRI)
         (SELECT b FROM dt)::numeric;                  -- DT bedel (AYRI)
$function$;
GRANT EXECUTE ON FUNCTION public.firma_ozet_birlikte() TO anon, authenticated, service_role;

-- ── 3) firma_dizin_birlikte() — liste (firma adı → anon'a KAPALI) ───────────
-- FULL OUTER JOIN (yalnız-DT firmalar görünür). ihale ciro/sözleşme AYRI,
-- DT bedel/sözleşme AYRI. Sıralama: GREATEST(ihale, dt) — evrenler TOPLANMAZ,
-- her firma en büyük olduğu evrene göre sıralanır. Kurum filtresi anti-join.
DROP FUNCTION IF EXISTS public.firma_dizin_birlikte(text,text,integer,integer,text,boolean);
CREATE FUNCTION public.firma_dizin_birlikte(
  p_ara text DEFAULT NULL, p_il text DEFAULT NULL,
  p_limit integer DEFAULT 100, p_offset integer DEFAULT 0,
  p_sort text DEFAULT 'bedel', p_kamu_dahil boolean DEFAULT false)
RETURNS TABLE(id uuid, ad text, il text,
              toplam_sozlesme_sayisi bigint, toplam_ciro numeric,
              son_sozlesme_tarihi timestamptz, dt_bedel numeric, dt_sozlesme_sayisi bigint)
LANGUAGE plpgsql STABLE SECURITY DEFINER
SET search_path TO 'public'
SET statement_timeout TO '20s'
AS $function$
DECLARE
  v_like text := NULL;
BEGIN
  IF p_ara IS NOT NULL AND btrim(p_ara) <> '' THEN
    v_like := '%' || replace(replace(left(public.tr_fold(p_ara), 40), '%', ''), '_', '') || '%';
  END IF;
  RETURN QUERY EXECUTE format($q$
    SELECT y.id, COALESCE(y.ad, d.ad), y.il,
           COALESCE(y.toplam_sozlesme_sayisi,0)::bigint,   -- İHALE-only
           COALESCE(y.toplam_ciro,0)::numeric,             -- İHALE-only
           y.son_sozlesme_tarihi,
           COALESCE(d.dt_bedel,0)::numeric,                -- DT (AYRI)
           COALESCE(d.dt_sozlesme,0)::bigint               -- DT sözleşme (AYRI)
    FROM public.yukleniciler y
    FULL OUTER JOIN public.firma_dt_toplam d ON d.firma_norm = y.normalize_ad
    WHERE (%L::text IS NULL OR COALESCE(y.arama_fold, public.tr_fold(d.ad)) LIKE %L)
      AND (%L::text IS NULL OR y.il = %L)   -- DT-only'de il yok → il filtresi verilince ihale-çıpalı
      AND (%L::boolean OR COALESCE(y.normalize_ad, d.firma_norm) NOT IN (SELECT fn FROM public.firma_kurum_norm))
    ORDER BY
      (CASE WHEN %L='bedel'    THEN GREATEST(COALESCE(y.toplam_ciro,0), COALESCE(d.dt_bedel,0)) END) DESC NULLS LAST,
      (CASE WHEN %L='sozlesme' THEN GREATEST(COALESCE(y.toplam_sozlesme_sayisi,0), COALESCE(d.dt_sozlesme,0)) END) DESC NULLS LAST,
      (CASE WHEN %L='tarih'    THEN y.son_sozlesme_tarihi END) DESC NULLS LAST,
      (CASE WHEN %L='ad'       THEN COALESCE(y.ad, d.ad) END) ASC NULLS LAST,
      GREATEST(COALESCE(y.toplam_ciro,0), COALESCE(d.dt_bedel,0)) DESC NULLS LAST
    LIMIT %s OFFSET %s
  $q$, v_like, v_like, p_il, p_il, p_kamu_dahil, p_sort, p_sort, p_sort, p_sort,
       LEAST(GREATEST(p_limit,1),200), GREATEST(p_offset,0));
END;
$function$;
REVOKE EXECUTE ON FUNCTION public.firma_dizin_birlikte(text,text,integer,integer,text,boolean) FROM PUBLIC, anon;
GRANT  EXECUTE ON FUNCTION public.firma_dizin_birlikte(text,text,integer,integer,text,boolean) TO authenticated, service_role;

COMMIT;

NOTIFY pgrst, 'reload schema';

-- =============================================================================
-- DOĞRULAMA:
--   SELECT * FROM firma_ozet_birlikte();  -- toplam_ciro (ihale) << toplam? dt_bedel ayrı
--   SELECT count(*) FROM firma_dizin_birlikte(NULL,NULL,25,0,'bedel',false);  -- < 1s
--   -- DT-only firma görünüyor mu (ihale ciro 0, dt_bedel > 0):
--   SELECT ad, toplam_ciro, dt_bedel FROM firma_dizin_birlikte(NULL,NULL,200,0,'bedel',false)
--     WHERE toplam_ciro=0 AND dt_bedel>0 LIMIT 5;
-- GECE: firma_kurum_norm'u firma_dt_toplam REFRESH'inden SONRA tazele.
-- =============================================================================
