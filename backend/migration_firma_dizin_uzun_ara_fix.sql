-- ============================================================
-- firma_dizin_dt / firma_dizin_birlikte — UZUN ARAMA TERİMİ timeout fix (3 Ağu 2026)
-- ------------------------------------------------------------
-- SORUN: DT-only firmaya tıklayınca link TAM adı gönderiyor (?firma=<100+ karakter>). firma_dizin_dt
-- `firma_norm LIKE '%<tam ad>%'` → tam ad "…SANAYİ VE TİCARET LİMİTED ŞİRKETİ" gibi ÇOK YAYGIN
-- trigram'lar içerir → GIN devasa aday kümesi + 100-karakterlik LIKE recheck her satırda → >20s
-- statement timeout (57014). Kısa terim ("BELİZ GRUP") hızlı çünkü nadir trigram.
-- KANIT: curl tam-ad → HTTP 500 57014 @20s; kısa ad → 200 ~ms.
--
-- ÇÖZÜM: arama terimini LIKE'a sokmadan önce ilk 40 karaktere KIRP (firmanın ayırt edici kısmı
-- baştadır — brand adı; ortak sonekler sonda). left(normalize/tr_fold(p_ara),40). Doğruluğu bozmaz
-- (40-karakter önek firma_norm'un başında zaten var), pathojik uzun-desen GIN'i önler.
-- statement_timeout='20s' TANIMA GÖMÜLDÜ (CREATE OR REPLACE proconfig'i sıfırlar — [[statement-timeout-edge]]).
--
-- Çalıştır (superuser):
--   docker exec -i supabase-db psql -U supabase_admin -d postgres < backend/migration_firma_dizin_uzun_ara_fix.sql
-- ============================================================

CREATE OR REPLACE FUNCTION public.firma_dizin_dt(
  p_ara text DEFAULT NULL, p_limit int DEFAULT 100, p_offset int DEFAULT 0, p_sort text DEFAULT 'bedel',
  p_kamu_dahil boolean DEFAULT false)
RETURNS TABLE (id uuid, ad text, il text, toplam_sozlesme_sayisi bigint,
               toplam_ciro numeric, son_sozlesme_tarihi timestamptz, dt_bedel numeric)
LANGUAGE sql STABLE SECURITY DEFINER SET search_path = public SET statement_timeout = '20s' AS $$
  WITH top AS (
    SELECT firma_norm, ad, dt_sozlesme, dt_bedel
    FROM public.firma_dt_toplam
    WHERE (p_ara IS NULL OR firma_norm LIKE '%'||left(public.normalize_firma(p_ara),40)||'%')  -- KIRP: uzun-desen GIN pathojisi
      AND (p_kamu_dahil OR NOT public.firma_kurum_mu(ad))
    ORDER BY (CASE WHEN p_sort='sozlesme' THEN dt_sozlesme END) DESC NULLS LAST,
             dt_bedel DESC NULLS LAST
    LIMIT LEAST(GREATEST(p_limit,1),200) OFFSET GREATEST(p_offset,0)
  )
  SELECT y.id, t.ad, y.il, t.dt_sozlesme, t.dt_bedel, NULL::timestamptz, t.dt_bedel
  FROM top t LEFT JOIN public.yukleniciler y ON y.normalize_ad = t.firma_norm
  ORDER BY (CASE WHEN p_sort='sozlesme' THEN t.dt_sozlesme END) DESC NULLS LAST,
           t.dt_bedel DESC NULLS LAST;
$$;
REVOKE EXECUTE ON FUNCTION public.firma_dizin_dt(text,int,int,text,boolean) FROM public, anon;
GRANT  EXECUTE ON FUNCTION public.firma_dizin_dt(text,int,int,text,boolean) TO authenticated, service_role;

CREATE OR REPLACE FUNCTION public.firma_dizin_birlikte(
  p_ara text DEFAULT NULL, p_il text DEFAULT NULL, p_limit int DEFAULT 100, p_offset int DEFAULT 0,
  p_sort text DEFAULT 'bedel', p_kamu_dahil boolean DEFAULT false)
RETURNS TABLE (id uuid, ad text, il text, toplam_sozlesme_sayisi bigint,
               toplam_ciro numeric, son_sozlesme_tarihi timestamptz, dt_bedel numeric)
LANGUAGE sql STABLE SECURITY DEFINER SET search_path = public SET statement_timeout = '20s' AS $$
  SELECT y.id, y.ad, y.il,
         (COALESCE(y.toplam_sozlesme_sayisi,0) + COALESCE(d.dt_sozlesme,0))::bigint,
         (COALESCE(y.toplam_ciro,0) + COALESCE(d.dt_bedel,0))::numeric,
         y.son_sozlesme_tarihi, COALESCE(d.dt_bedel,0)
  FROM public.yukleniciler y
  LEFT JOIN public.firma_dt_toplam d ON d.firma_norm = y.normalize_ad
  WHERE (p_ara IS NULL OR y.arama_fold LIKE '%'||left(public.tr_fold(p_ara),40)||'%')  -- KIRP: uzun-desen GIN pathojisi
    AND (p_il  IS NULL OR y.il = p_il)
    AND (p_kamu_dahil OR NOT public.firma_kurum_mu(y.ad))
  ORDER BY
    (CASE WHEN p_sort='bedel'    THEN (COALESCE(y.toplam_ciro,0)+COALESCE(d.dt_bedel,0)) END) DESC NULLS LAST,
    (CASE WHEN p_sort='sozlesme' THEN (COALESCE(y.toplam_sozlesme_sayisi,0)+COALESCE(d.dt_sozlesme,0)) END) DESC NULLS LAST,
    (CASE WHEN p_sort='tarih'    THEN y.son_sozlesme_tarihi END) DESC NULLS LAST,
    (CASE WHEN p_sort='ad'       THEN y.ad END) ASC NULLS LAST,
    (COALESCE(y.toplam_ciro,0)+COALESCE(d.dt_bedel,0)) DESC NULLS LAST
  LIMIT LEAST(GREATEST(p_limit,1),200) OFFSET GREATEST(p_offset,0);
$$;
REVOKE EXECUTE ON FUNCTION public.firma_dizin_birlikte(text,text,int,int,text,boolean) FROM public, anon;
GRANT  EXECUTE ON FUNCTION public.firma_dizin_birlikte(text,text,int,int,text,boolean) TO authenticated, service_role;

NOTIFY pgrst, 'reload schema';

-- Kontrol (tam ad artık ~ms + veri dönmeli):
--   \timing on
--   SELECT ad FROM firma_dizin_dt('BELİZ GRUP REKLAM ORGANİZASYON MATBAACILIK YAYINCILIK KIRTASİYE ELEKTRİK ELEKTRONİK SANAYİ VE TİCARET LİMİTED ŞİRKETİ',5,0,'bedel',true);
