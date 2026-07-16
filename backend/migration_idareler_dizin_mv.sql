-- ============================================================
-- İhaleGlobal — İdareler Dizini: materialized view + tek-istek JSON RPC
--
-- Kök neden (16 Tem): idareler.html, idare_sayim() RPC'sini PostgREST'in
-- 1000 satırlık db-max-rows sınırı yüzünden ~16 kez ardışık çağırıyordu ve
-- HER çağrıda 355K+ satırlık ilanlar üzerinde GROUP BY + MODE() BAŞTAN
-- çalışıyordu (ölçüm: sayfa başına ~4.2sn → toplam 60-70sn "İdare verileri
-- çekiliyor…" beklemesi).
--
-- Çözüm iki katman:
--   1) idare_ozet_mv: aynı aggregate, ÖNCEDEN hesaplanmış (materialized view).
--      Veri zaten yalnız scraper turlarında değiştiği için gece run_scraper.sh
--      sonunda REFRESH CONCURRENTLY yeterli — tazelik kaybı yok.
--   2) idare_dizin_json(): TÜM dizini TEK istekte jsonb döner. Yanıt tek
--      "satır" (json skaler) olduğu için db-max-rows=1000 sınırına takılmaz.
--      Payload'u küçük tutmak için satır formatı dizi: [idare, toplam, aktif, il].
--   Bonus: eski idare_sayim() da MV'den okuyacak şekilde değiştirildi —
--   cache'lenmiş eski HTML de anında hızlanır, canlı GROUP BY tamamen kalkar.
--
-- Additive/güvenli: IF NOT EXISTS + CREATE OR REPLACE (idempotent).
--
-- Çalıştırma: docker exec -i supabase-db psql -U postgres -d postgres < backend/migration_idareler_dizin_mv.sql
-- Gece tazeleme: run_scraper.sh sonunda REFRESH MATERIALIZED VIEW CONCURRENTLY (ayrı commit'te eklendi).
-- ============================================================

BEGIN;

-- 1) Önceden hesaplanmış özet (idare_sayim() ile birebir aynı sorgu)
CREATE MATERIALIZED VIEW IF NOT EXISTS public.idare_ozet_mv AS
SELECT
  idare,
  COUNT(*)::bigint AS toplam,
  (COUNT(*) FILTER (WHERE durum = 'aktif'))::bigint AS aktif,
  MODE() WITHIN GROUP (ORDER BY il) AS en_yakin_il
FROM public.ilanlar
WHERE idare IS NOT NULL
GROUP BY idare;

-- REFRESH ... CONCURRENTLY için zorunlu unique index (okumaları bloklamadan tazeleme)
CREATE UNIQUE INDEX IF NOT EXISTS idx_idare_ozet_mv_idare
  ON public.idare_ozet_mv (idare);

ANALYZE public.idare_ozet_mv;

GRANT SELECT ON public.idare_ozet_mv TO anon, authenticated;

-- 2) Tek istekte tüm dizin — json skaler döndüğü için 1000 satır sınırı işlemez.
--    Satır formatı: [idare, toplam, aktif, en_yakin_il] (kısa payload; ~15K satır).
CREATE OR REPLACE FUNCTION public.idare_dizin_json()
RETURNS jsonb AS $$
  SELECT COALESCE(
    jsonb_agg(jsonb_build_array(idare, toplam, aktif, en_yakin_il) ORDER BY toplam DESC),
    '[]'::jsonb
  )
  FROM public.idare_ozet_mv;
$$ LANGUAGE SQL STABLE;

-- MV okuması ~ms sürer ama 3s varsayılanın kenarında sürpriz yaşamamak için
-- (rekabet_ozet dersi) yine de pay bırak.
ALTER FUNCTION public.idare_dizin_json() SET statement_timeout = '20s';

GRANT EXECUTE ON FUNCTION public.idare_dizin_json() TO anon, authenticated;

-- 3) Eski RPC artık MV'den okur (imza aynı; grant'ler CREATE OR REPLACE'te korunur)
CREATE OR REPLACE FUNCTION public.idare_sayim()
RETURNS TABLE (
  idare TEXT,
  toplam BIGINT,
  aktif BIGINT,
  en_yakin_il TEXT
) AS $$
  SELECT idare, toplam, aktif, en_yakin_il
  FROM public.idare_ozet_mv
  ORDER BY toplam DESC;
$$ LANGUAGE SQL STABLE;

COMMIT;

NOTIFY pgrst, 'reload schema';

-- Kontrol
SELECT COUNT(*) AS idare_sayisi FROM public.idare_ozet_mv;
SELECT pg_size_pretty(length(public.idare_dizin_json()::text)::bigint) AS json_boyut;
SELECT * FROM public.idare_sayim() LIMIT 3;
