-- ============================================================
-- firma_dt_toplu(p_adlar[]) — liste/arama kartlarında firma başına DT sayısı+bedeli (B) — 3 Ağu 2026
-- ------------------------------------------------------------
-- İSTEK (kullanıcı): firma LİSTE/ARAMA ekranları yalnız ihale ciro/sözleşme gösteriyor; DT
-- (ÜNTES: 180 kayıt/34,99M — ihaleden büyük) görünmüyor → yanıltıcı. Detayda DT KPI zaten var;
-- eksik olan liste. Bu RPC, görünen firmaların (20-50 ad) DT toplamlarını TEK istekte döner →
-- frontend her satıra "⚡ N DT · ₺X" AYRI satır ekler (ihale ile TOPLAMADAN — ölçek farkı,
-- [[dt-kazanan-captcha]] "ihale cirosuna karıştırma" kararı).
--
-- normalize_firma(a) = firma_norm EŞİTLİK (firma_dt_toplam unique index) → LIKE yok, seq-scan yok,
-- parametreli-LIKE tuzağı YOK. Yalnız DT'si olan adlar döner (LEFT değil INNER join).
-- Çalıştır (superuser):
--   docker exec -i supabase-db psql -U supabase_admin -d postgres < backend/migration_firma_dt_toplu.sql
-- ============================================================
CREATE OR REPLACE FUNCTION public.firma_dt_toplu(p_adlar text[])
RETURNS TABLE (ad text, dt_sozlesme bigint, dt_bedel numeric)
LANGUAGE sql STABLE SECURITY DEFINER SET search_path = public AS $$
  SELECT a AS ad, t.dt_sozlesme, t.dt_bedel
  FROM unnest(COALESCE(p_adlar, ARRAY[]::text[])) AS a
  JOIN public.firma_dt_toplam t ON t.firma_norm = public.normalize_firma(a);
$$;
ALTER FUNCTION public.firma_dt_toplu(text[]) SET statement_timeout = '15s';
REVOKE EXECUTE ON FUNCTION public.firma_dt_toplu(text[]) FROM public, anon;   -- DT firma adı üyeye özel
GRANT  EXECUTE ON FUNCTION public.firma_dt_toplu(text[]) TO authenticated, service_role;

NOTIFY pgrst, 'reload schema';

-- Kontrol:
--   SELECT * FROM firma_dt_toplu(ARRAY['ÜNTES ISITMA KLİMA SOĞUTMA SANAYİ VE TİCARET ANONİM ŞİRKETİ']);
