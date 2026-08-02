-- ============================================================
-- firma_dizin_dt → DİNAMİK SQL (trigram indeksini KESİN kullan) — 3 Ağu 2026
-- ------------------------------------------------------------
-- KÖK NEDEN (EXPLAIN + \timing ile kanıtlandı): fonksiyon içindeki `firma_norm LIKE
-- '%'||left(normalize_firma(p_ara),40)||'%'` deseni PARAMETRE bağımlı → planner trigram GIN'i
-- kullanamıyor (desen opak; normalize_firma IMMUTABLE olmadığı için custom-plan da foldlamıyor)
-- → firma_dt_toplam (256.979) SEQ-SCAN → tam ad 24.8s, kısa ad 11.6s. İzole literal WHERE = 50ms.
-- REST'te authenticated statement_timeout → 57014 (DT firma araması "bulunamadı" görünüyordu).
--
-- ÇÖZÜM: deseni plpgsql'de HESAPLA, EXECUTE ile LİTERAL olarak göm → çalıştırılan sorguda sabit
-- desen → planner trigram GIN'i kullanır (~ms). % ve _ joker'leri temizlenir (firma adında olmaz
-- ama güvence). Diğer parametreler de literal (%L/%s) — enjeksiyon yok (format quote'lar).
--
-- Çalıştır (superuser):
--   docker exec -i supabase-db psql -U supabase_admin -d postgres < backend/migration_firma_dizin_dt_dinamik.sql
-- ============================================================

CREATE OR REPLACE FUNCTION public.firma_dizin_dt(
  p_ara text DEFAULT NULL, p_limit int DEFAULT 100, p_offset int DEFAULT 0, p_sort text DEFAULT 'bedel',
  p_kamu_dahil boolean DEFAULT false)
RETURNS TABLE (id uuid, ad text, il text, toplam_sozlesme_sayisi bigint,
               toplam_ciro numeric, son_sozlesme_tarihi timestamptz, dt_bedel numeric)
LANGUAGE plpgsql STABLE SECURITY DEFINER SET search_path = public SET statement_timeout = '20s' AS $$
DECLARE
  v_like text := NULL;
BEGIN
  IF p_ara IS NOT NULL AND btrim(p_ara) <> '' THEN
    -- ayırt edici kısım baştadır → ilk 40 karakter yeter; % _ joker temizle
    v_like := '%' || replace(replace(left(public.normalize_firma(p_ara), 40), '%', ''), '_', '') || '%';
  END IF;
  RETURN QUERY EXECUTE format($q$
    WITH top AS (
      SELECT firma_norm, ad, dt_sozlesme, dt_bedel
      FROM public.firma_dt_toplam
      WHERE (%L::text IS NULL OR firma_norm LIKE %L)
        AND (%L::boolean OR NOT public.firma_kurum_mu(ad))
      ORDER BY (CASE WHEN %L = 'sozlesme' THEN dt_sozlesme END) DESC NULLS LAST, dt_bedel DESC NULLS LAST
      LIMIT %s OFFSET %s
    )
    SELECT y.id, t.ad, y.il, t.dt_sozlesme, t.dt_bedel, NULL::timestamptz, t.dt_bedel
    FROM top t LEFT JOIN public.yukleniciler y ON y.normalize_ad = t.firma_norm
    ORDER BY (CASE WHEN %L = 'sozlesme' THEN t.dt_sozlesme END) DESC NULLS LAST, t.dt_bedel DESC NULLS LAST
  $q$, v_like, v_like, p_kamu_dahil, p_sort,
       LEAST(GREATEST(p_limit,1),200), GREATEST(p_offset,0), p_sort);
END;
$$;
REVOKE EXECUTE ON FUNCTION public.firma_dizin_dt(text,int,int,text,boolean) FROM public, anon;
GRANT  EXECUTE ON FUNCTION public.firma_dizin_dt(text,int,int,text,boolean) TO authenticated, service_role;

NOTIFY pgrst, 'reload schema';

-- Kontrol (artık ~ms olmalı):
--   \timing on
--   SELECT count(*) FROM firma_dizin_dt('BELİZ GRUP REKLAM ORGANİZASYON MATBAACILIK YAYINCILIK KIRTASİYE ELEKTRİK ELEKTRONİK SANAYİ VE TİCARET LİMİTED ŞİRKETİ',5,0,'bedel',true);
