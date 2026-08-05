-- =============================================================================
-- migration_kategori_sayim_dt.sql — B7: sektörler sayfası DT kolonu
-- İKİ EVREN · 5 Ağu 2026
-- =============================================================================
-- kategori_sayim() ihale sektör sayımını döner (kategori_sayim_mv). Bu onun DT
-- AYNASI — dt_kategori_sayim_mv'den. İki evren AYRI kolon (toplanmaz).
-- SECURITY DEFINER: dt_kategori_sayim_mv anon'a KAPALI ama sektör SAYIMLARI hassas
-- değil (isim yok, salt agregat) → kategori_sayim ile aynı asimetri (anon'a EXECUTE).
--
-- Uygulama:
--   ssh ihale2 "docker exec -i supabase-db psql -U postgres -d postgres" < backend/migration_kategori_sayim_dt.sql
-- =============================================================================

CREATE OR REPLACE FUNCTION public.kategori_sayim_dt()
RETURNS TABLE(kategori text, toplam bigint, aktif bigint)
LANGUAGE sql STABLE SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
  SELECT kategori, toplam, aktif
  FROM public.dt_kategori_sayim_mv
  ORDER BY toplam DESC;
$$;

GRANT EXECUTE ON FUNCTION public.kategori_sayim_dt() TO anon, authenticated, service_role;

NOTIFY pgrst, 'reload schema';

-- DOĞRULAMA: SELECT * FROM kategori_sayim_dt() LIMIT 3;
