-- ============================================================
-- firma_dt_liste — teklif aralığı (en düşük / en yüksek) ekle (31 Tem 2026)
-- ------------------------------------------------------------
-- "Katıldığı İhaleler" kartlarında teklif aralığını gösteriyoruz; "Katıldığı Doğrudan
-- Teminler" sekmesinde de aynı rekabet bilgisini verelim. dogrudan_temin_sonuclari'nda
-- en_dusuk_teklif / en_yuksek_teklif KOLONLARI VAR (v1-dt-detay zaten okuyor) → firma_dt_liste
-- dönüşüne eklenir. RETURNS TABLE değiştiği için DROP + CREATE.
--
-- Çalıştır (superuser):
--   docker exec -i supabase-db psql -U supabase_admin -d postgres < backend/migration_firma_dt_liste_teklif.sql
-- ============================================================

DROP FUNCTION IF EXISTS public.firma_dt_liste(text, int, int);
CREATE OR REPLACE FUNCTION public.firma_dt_liste(
  p_firma_ad text, p_limit int DEFAULT 20, p_offset int DEFAULT 0)
RETURNS TABLE(dt_no text, baslik text, il text, kategori text, tur text,
              tarih date, kazanan_bedel numeric, idare text,
              en_dusuk_teklif numeric, en_yuksek_teklif numeric)
LANGUAGE sql STABLE SECURITY DEFINER SET search_path = public AS $$
  SELECT s.dt_no, i.baslik, i.il, i.kategori, i.tur, i.tarih, s.kazanan_bedel, i.idare,
         s.en_dusuk_teklif, s.en_yuksek_teklif
  FROM public.dogrudan_temin_sonuclari s
  JOIN public.dogrudan_temin_ilanlari i ON i.dt_no = s.dt_no
  WHERE s.kazanan_firma IS NOT NULL
    AND public.tr_fold(s.kazanan_firma) = public.tr_fold(p_firma_ad)
  ORDER BY i.tarih DESC NULLS LAST, s.kazanan_bedel DESC NULLS LAST
  LIMIT LEAST(GREATEST(p_limit, 1), 100) OFFSET GREATEST(p_offset, 0);
$$;
ALTER FUNCTION public.firma_dt_liste(text, int, int) SET statement_timeout = '15s';
REVOKE EXECUTE ON FUNCTION public.firma_dt_liste(text, int, int) FROM public, anon;
GRANT  EXECUTE ON FUNCTION public.firma_dt_liste(text, int, int) TO authenticated, service_role;

NOTIFY pgrst, 'reload schema';
