-- =============================================================================
-- migration_idare_ozet_mv_aktif_deadline.sql
-- =============================================================================
--
-- SORUN: idare_ozet_mv.aktif = COUNT(*) FILTER (durum='aktif'). Bu, son teklif
-- tarihi GECMIS ama durum'u hala 'aktif' kalmis (bayat) ilanlari da sayiyordu.
-- Sonuc: Idare Dizini "Aktif Ihale" = 14.143; oysa "Aktif Ihaleler" listesi
-- (v1-ihaleler, durum='aktif' AND son_teklif_tarihi >= now) = 5.435. Kullanici
-- tutarsizligi yakaladi. Olcum (01 Agu 2026):
--   durum=aktif toplam .................. 14.143
--   + son_teklif >= now (gercekten acik)   5.435  <- DOGRU tanim
--   + son_teklif < now (bayat/suresi gecti) 8.163
--   + son_teklif NULL ..................... 545
--
-- COZUM: MV'nin aktif tanimini listeyle AYNI yap:
--   durum='aktif' AND son_teklif_tarihi >= now()
-- now() MV icinde refresh aninda donar (gece tazelemesi -> o geceki acik sayisi).
-- Gun icinde ufak kayma olur (son teklifler gecer) ama liste/dashboard ile
-- kavramsal olarak ayni; 14K vs 5K ucurumu kapanir.
--
-- NOT: MV'de CREATE OR REPLACE yok -> DROP + CREATE. idare_dizin_json/idare_sayim
-- fonksiyonlari MV'yi ADIYLA okur (SQL govdesi pg_depend olusturmaz) -> CASCADE'siz
-- DROP guvenli, fonksiyonlar ayakta kalir, ayni islemde MV yeniden kurulur.
--
-- Uygulama:
--   docker exec -i supabase-db psql -U supabase_admin -d postgres < backend/migration_idare_ozet_mv_aktif_deadline.sql
-- =============================================================================

BEGIN;

DROP MATERIALIZED VIEW IF EXISTS public.idare_ozet_mv;

CREATE MATERIALIZED VIEW public.idare_ozet_mv AS
SELECT
  idare,
  COUNT(*)::bigint AS toplam,
  (COUNT(*) FILTER (WHERE durum = 'aktif' AND son_teklif_tarihi >= now()))::bigint AS aktif,
  MODE() WITHIN GROUP (ORDER BY il) AS en_yakin_il
FROM public.ilanlar
WHERE idare IS NOT NULL
GROUP BY idare;

CREATE UNIQUE INDEX idx_idare_ozet_mv_idare
  ON public.idare_ozet_mv (idare);

ANALYZE public.idare_ozet_mv;

GRANT SELECT ON public.idare_ozet_mv TO anon, authenticated;

COMMIT;

-- =============================================================================
-- DOGRULAMA (supabase_admin):
--   SELECT SUM(aktif) AS dizin_aktif FROM public.idare_ozet_mv;
--   -- beklenen: ~5.435 (liste ile ayni mertebe, 14.143 DEGIL)
--   SELECT COUNT(*) FROM public.ilanlar
--     WHERE durum='aktif' AND son_teklif_tarihi >= now() AND idare IS NOT NULL;
--   -- MV SUM(aktif) bu sayiya ~esit olmali (idare IS NOT NULL kismi)
-- =============================================================================
