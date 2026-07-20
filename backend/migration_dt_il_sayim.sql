-- ============================================================================
-- migration_dt_il_sayim.sql — Anasayfa mini haritasına Doğrudan Temin katmanı (18 Tem 2026)
--
-- Kullanıcı talebi: dashboard.html'deki "Türkiye İhale Haritası" widget'ı yalnız `ilanlar`
-- (rekabetçi ihale) sayısını gösteriyordu. Artık il rengi İHALE+DT TOPLAMINA göre boyanacak,
-- hover'da ikisi AYRI gösterilecek (dünya ticaret haritasındaki ihracat/ithalat ayrımı gibi),
-- tıklayınca kullanıcı "İhaleler" ya da "Doğrudan Temin"den birine gitmeyi seçecek.
--
-- il_sayim() (migration_il_sayim_rpc.sql) zaten `ilanlar` için var; bu dosya aynı deseni
-- `dogrudan_temin_ilanlari` için ekliyor. O tablo 1.48M satır (ilanlar'ın 355K'sinden çok
-- daha büyük, "Statement Timeout Edge" eşiğinin epey üstünde) → il kolonuna indeks +
-- ALTER FUNCTION SET statement_timeout güvence payı (il_sektor_ozet ile aynı desen).
--
-- Çalıştır: docker exec -i supabase-db psql -U postgres -d postgres < backend/migration_dt_il_sayim.sql
-- Idempotent: IF NOT EXISTS / CREATE OR REPLACE. Tekrarı zararsız.
-- ============================================================================

CREATE INDEX IF NOT EXISTS idx_dogrudan_temin_ilanlari_il
  ON public.dogrudan_temin_ilanlari (il)
  WHERE il IS NOT NULL;

CREATE OR REPLACE FUNCTION public.dt_il_sayim()
RETURNS TABLE(il text, adet bigint)
LANGUAGE sql STABLE
AS $$
  SELECT il, count(*)::bigint AS adet
  FROM public.dogrudan_temin_ilanlari
  WHERE il IS NOT NULL AND il <> ''
  GROUP BY il;
$$;
ALTER FUNCTION public.dt_il_sayim() SET statement_timeout = '20s';
GRANT EXECUTE ON FUNCTION public.dt_il_sayim() TO anon, authenticated;

NOTIFY pgrst, 'reload schema';

-- Doğrulama (elle):
--   SELECT * FROM dt_il_sayim() ORDER BY adet DESC LIMIT 5;
--   EXPLAIN ANALYZE SELECT * FROM dt_il_sayim();  -- indeks kullanılmalı, saniyeler içinde bitmeli
