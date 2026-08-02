-- ============================================================
-- firma_dt_toplam.firma_norm trigram GIN — firma_dizin_dt REST 57014 timeout fix (2 Ağu 2026)
-- ------------------------------------------------------------
-- SORUN: #2 (DT firma araması) canlıda "Sonuç bulunamadı" dönüyordu. Teşhis: RPC psql'de
-- çalışıyor (supabase_admin/authenticated), AMA /rest/v1/rpc/firma_dizin_dt → HTTP 500
-- {"code":"57014","message":"canceling statement due to statement timeout"}. Neden:
-- firma_dizin_dt, firma_dt_toplam'da `firma_norm LIKE '%'||normalize_firma(p_ara)||'%'`
-- (BAŞTAN-JOKER) → seq-scan; REST rolünün kısa statement_timeout'unu aşıyor (psql'de timeout
-- yok o yüzden orada hızlı görünüyordu). [[statement-timeout-edge]] deseni.
--
-- ÇÖZÜM: pg_trgm GIN indeksi → LIKE '%x%' indeks kullanır (idx_ilanlar_arama_fold_trgm ile aynı
-- mantık). Ayrıca fonksiyona 20s statement_timeout tamponu (proconfig, top-level RPC'de geçerli;
-- dt_analiz_ozet'te kanıtlı). firma_dt_toplam MV; GIN indeks REFRESH CONCURRENTLY ile korunur.
--
-- ⚠️ CONCURRENTLY → transaction bloğu YOK; psql < file her ifadeyi ayrı auto-commit'ler.
-- Çalıştır (superuser):
--   docker exec -i supabase-db psql -U supabase_admin -d postgres < backend/migration_firma_dt_toplam_trgm.sql
-- ============================================================
CREATE EXTENSION IF NOT EXISTS pg_trgm;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_firma_dt_toplam_firma_norm_trgm
  ON public.firma_dt_toplam USING gin (firma_norm gin_trgm_ops);

-- Tampon: REST rolünün kısa timeout'u yerine fonksiyon 20s'ye kadar çalışabilsin (indeksle
-- zaten ~ms sürecek; bu yalnız kenar durumlar için güvence).
ALTER FUNCTION public.firma_dizin_dt(text,int,int,text,boolean) SET statement_timeout = '20s';
ALTER FUNCTION public.firma_dizin_birlikte(text,text,int,int,text,boolean) SET statement_timeout = '20s';

NOTIFY pgrst, 'reload schema';

-- Kontrol (REST'te artık 200 + veri dönmeli):
--   \timing on
--   SELECT count(*) FROM firma_dizin_dt('BELİZ GRUP',20,0,'bedel',true);
