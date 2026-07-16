-- ============================================================
-- Türkiye dış ticareti — HS6 (kalem-kalem) tablosu
--
-- ticaret-analiz.html detay drill-down'u için: bir ülkeye tıklayınca Türkiye'nin
-- o ülkeyle HS 6-hane bazında ihracat/ithalatı gelir (fasıl→başlık→6-hane).
-- Kaynak: UN Comtrade (keyless preview, ülke-başı AG6 top-500 by value).
-- Küçük partnerlerde tam; büyük partnerlerde en büyük ~500 kalem (değerin ~%95+'i).
--
-- Statik JS'e sığmaz (~200K satır) → DB tablosu + PostgREST public read (RPC gerekmez,
-- client .eq('ulke_iso3',X).order('deger_usd',desc) ile sayfalı/sıralı çeker).
--
-- Çalıştırma: docker exec -i supabase-db psql -U postgres -d postgres -f - < backend/migration_dis_ticaret_hs.sql
-- ============================================================

BEGIN;

CREATE TABLE IF NOT EXISTS public.dis_ticaret_hs (
  ulke_iso3 char(3)      NOT NULL,        -- harita ISO-A3 ile eşleşir
  hs6       varchar(6)   NOT NULL,        -- HS 6-hane kod
  yon       char(1)      NOT NULL,        -- 'X' ihracat (TR→ülke), 'M' ithalat (ülke→TR)
  yil       smallint     NOT NULL,
  deger_usd numeric      NOT NULL,
  PRIMARY KEY (ulke_iso3, hs6, yon, yil)
);

-- Ülke detayını değere göre sıralı çekmek için (drill-down sorgusu)
CREATE INDEX IF NOT EXISTS idx_dtc_ulke_yon_deger
  ON public.dis_ticaret_hs (ulke_iso3, yon, deger_usd DESC);
-- Tek kalemin tüm ülkelerini çekmek için (ihale ürünü → HS → hangi ülkeler, Faz 2)
CREATE INDEX IF NOT EXISTS idx_dtc_hs
  ON public.dis_ticaret_hs (hs6, yon, deger_usd DESC);

-- Salt-okunur public erişim (agregat/istatistik verisi, hassas değil)
ALTER TABLE public.dis_ticaret_hs ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS dtc_public_read ON public.dis_ticaret_hs;
CREATE POLICY dtc_public_read ON public.dis_ticaret_hs
  FOR SELECT TO anon, authenticated USING (true);
GRANT SELECT ON public.dis_ticaret_hs TO anon, authenticated;
-- Ingestion (ticaret_hs_cek.py) service_role ile yazar
GRANT SELECT, INSERT, UPDATE, DELETE ON public.dis_ticaret_hs TO service_role;

COMMIT;

NOTIFY pgrst, 'reload schema';

-- Kontrol
-- SELECT count(*) FROM dis_ticaret_hs;
-- SELECT hs6, deger_usd FROM dis_ticaret_hs WHERE ulke_iso3='DEU' AND yon='X' ORDER BY deger_usd DESC LIMIT 10;
