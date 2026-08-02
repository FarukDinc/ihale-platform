-- ============================================================================
-- migration_idare_dizin_dt.sql — Kurumlar dizinine Doğrudan Temin sayıları
--   (2 Ağu 2026). v1-kurumlar listesi yalnız İhale sayısı gösteriyordu; kullanıcı
--   Toplam DT + Aktif DT de istiyor. idare_dizin_json() satır formatına DT eklenir:
--     [idare, toplam_ihale, aktif_ihale, il, toplam_dt, aktif_dt]  (geriye uyumlu — sona eklendi)
--   dt_idare_ozet_mv (idare bazında DT toplam/aktif) LEFT JOIN ile birleştirilir.
--   dt_idare_ozet_mv anon'a KAPALI → fonksiyon SECURITY DEFINER yapılır (yalnız AGGREGATE
--   sayı döner, satır sızdırmaz; idare+sayılar zaten idare_ozet_mv üzerinden anon'a açık).
--
-- Çalıştırma:
--   docker exec -i supabase-db psql -U supabase_admin -d postgres < backend/migration_idare_dizin_dt.sql
-- Idempotent (CREATE OR REPLACE).
-- ============================================================================
CREATE OR REPLACE FUNCTION public.idare_dizin_json()
RETURNS jsonb
LANGUAGE sql STABLE SECURITY DEFINER SET search_path = public AS $$
  SELECT COALESCE(
    jsonb_agg(
      jsonb_build_array(i.idare, i.toplam, i.aktif, i.en_yakin_il,
                        COALESCE(d.toplam, 0), COALESCE(d.aktif, 0))
      ORDER BY i.toplam DESC),
    '[]'::jsonb)
  FROM public.idare_ozet_mv i
  LEFT JOIN public.dt_idare_ozet_mv d ON d.idare = i.idare;
$$;
ALTER FUNCTION public.idare_dizin_json() SET statement_timeout = '20s';
GRANT EXECUTE ON FUNCTION public.idare_dizin_json() TO anon, authenticated;

NOTIFY pgrst, 'reload schema';

-- Kontrol: ilk satırda 6 eleman olmalı (…,toplam_dt,aktif_dt)
SELECT public.idare_dizin_json()->0 AS ilk_satir;
