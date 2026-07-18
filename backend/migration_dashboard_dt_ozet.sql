-- ============================================================================
-- migration_dashboard_dt_ozet.sql — Anasayfa TEK mod-seçici için DT altyapısı (18 Tem 2026)
--
-- Kullanıcı talebi: dashboard.html'deki her widget kendi Tümü/İhaleler/DT düğmesini
-- tekrar tekrar sormasın — "Merhaba, X" başlığının altında TEK bir global seçici olsun,
-- KPI'lar/trend/kategori/kurumlar/harita hepsi ona göre değişsin.
--
-- kategori_sayim()/idare_sayim() ZATEN materialized view'dan okuyor (migration_ozet_mv_paketi.sql
-- / migration_idareler_dizin_mv.sql — canlı GROUP BY 350K+ satırda yavaş/timeout riskliydi).
-- DT tablosu (1.48M satır, ihale'nin 4 katı) için AYNI deseni birebir tekrarlıyoruz.
--
-- idare_ozet_mv ANON'A KAPALI (idare = kimlik-benzeri, misafir maskeleme ilkesi) —
-- dt_idare_ozet_mv de aynı kurala tabi. kategori_sayim anon'a AÇIK (sayı/kategori teaser) —
-- dt_kategori_sayim de öyle.
--
-- Trend/KPI-sayaç/son-eklenen widget'ları MV GEREKTİRMEZ: ilanlar tarafında da bunlar canlı,
-- indeksli count()/select().limit() ile çalışıyor (dashboard.html js) — dogrudan_temin_ilanlari'nda
-- da aynı indeksler var (durum: migration_dt_kazanan.sql, tarih: migration_dogrudan_temin.sql).
--
-- Çalıştır: docker exec -i supabase-db psql -U postgres -d postgres < backend/migration_dashboard_dt_ozet.sql
-- Idempotent: IF NOT EXISTS / CREATE OR REPLACE. Tekrarı zararsız.
-- ============================================================================

BEGIN;

-- 1) dt_kategori_sayim — kategori_sayim_mv ile birebir aynı desen. "aktif" = DT'nin
--    açık-durum grubu (dogrudan-temin.html DURUM_GRUP.acik ile BİREBİR).
CREATE MATERIALIZED VIEW IF NOT EXISTS public.dt_kategori_sayim_mv AS
SELECT COALESCE(kategori, 'Diğer') AS kategori,
       count(*)::bigint AS toplam,
       (count(*) FILTER (WHERE durum IN ('Doğrudan Temin Duyurusu Yayımlanmış', 'Teklifler Değerlendiriliyor')))::bigint AS aktif
FROM public.dogrudan_temin_ilanlari
GROUP BY COALESCE(kategori, 'Diğer');
CREATE UNIQUE INDEX IF NOT EXISTS idx_dt_kategori_sayim_mv_pk ON public.dt_kategori_sayim_mv (kategori);
GRANT SELECT ON public.dt_kategori_sayim_mv TO anon, authenticated, service_role;

CREATE OR REPLACE FUNCTION public.dt_kategori_sayim()
RETURNS TABLE (kategori TEXT, toplam BIGINT, aktif BIGINT)
LANGUAGE sql STABLE
AS $$ SELECT kategori, toplam, aktif FROM public.dt_kategori_sayim_mv ORDER BY toplam DESC; $$;
GRANT EXECUTE ON FUNCTION public.dt_kategori_sayim() TO anon, authenticated, service_role;

-- 2) dt_idare_sayim — idare_ozet_mv ile birebir aynı desen, AYNI anon-kapalı kural (idare kimlik verisi).
CREATE MATERIALIZED VIEW IF NOT EXISTS public.dt_idare_ozet_mv AS
SELECT idare,
       count(*)::bigint AS toplam,
       (count(*) FILTER (WHERE durum IN ('Doğrudan Temin Duyurusu Yayımlanmış', 'Teklifler Değerlendiriliyor')))::bigint AS aktif,
       MODE() WITHIN GROUP (ORDER BY il) AS en_yakin_il
FROM public.dogrudan_temin_ilanlari
WHERE idare IS NOT NULL
GROUP BY idare;
CREATE UNIQUE INDEX IF NOT EXISTS idx_dt_idare_ozet_mv_idare ON public.dt_idare_ozet_mv (idare);
-- anon'a GRANT YOK (bilinçli) — idare_ozet_mv ile aynı maskeleme.
-- "GRANT yazmamak" YETMEZ: MV'ler de ALTER DEFAULT PRIVILEGES üzerinden doğuştan
-- tablo-geneli anon SELECT alır. Açıkça REVOKE edilmezse anon MV'yi doğrudan okuyup
-- kapalı dt_idare_sayim() RPC'sini baypas eder. (İlk sürümde unutuldu → migration_dt_anon_fix.sql)
REVOKE SELECT ON public.dt_idare_ozet_mv FROM anon;
GRANT SELECT ON public.dt_idare_ozet_mv TO authenticated, service_role;

CREATE OR REPLACE FUNCTION public.dt_idare_sayim()
RETURNS TABLE (idare TEXT, toplam BIGINT, aktif BIGINT, en_yakin_il TEXT)
LANGUAGE sql STABLE
AS $$ SELECT idare, toplam, aktif, en_yakin_il FROM public.dt_idare_ozet_mv ORDER BY toplam DESC; $$;
REVOKE EXECUTE ON FUNCTION public.dt_idare_sayim() FROM PUBLIC, anon;
GRANT EXECUTE ON FUNCTION public.dt_idare_sayim() TO authenticated, service_role;

ANALYZE public.dt_kategori_sayim_mv, public.dt_idare_ozet_mv;

-- 3) dt_takipler — DT-takip AYRI tablo (takipler.ilan_id muhtemelen ilanlar(id) FK'li;
--    karıştırmak yerine ihale_sonuclari/dogrudan_temin_sonuclari ayrımıyla AYNI ilke:
--    ayrı kaynak, ayrı tablo). js/takip.js'teki Takip nesnesiyle AYNI şekil (localStorage
--    birincil + login'liyse DB senkron) — window.TakipDT olarak eklenir, mevcut Takip
--    API'sinin imzası (tek-argümanlı toggle/var) hiçbir çağıran yerde bozulmasın diye
--    DEĞİŞTİRİLMEDİ, yeni paralel nesne.
CREATE TABLE IF NOT EXISTS public.dt_takipler (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  kullanici_id UUID NOT NULL,
  dt_no        TEXT NOT NULL,
  olusturulma  TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (kullanici_id, dt_no)
);
CREATE INDEX IF NOT EXISTS idx_dt_takipler_kullanici ON public.dt_takipler (kullanici_id);

ALTER TABLE public.dt_takipler ENABLE ROW LEVEL SECURITY;
DROP POLICY IF EXISTS "dt_takipler_kendi_okur" ON public.dt_takipler;
CREATE POLICY "dt_takipler_kendi_okur" ON public.dt_takipler
  FOR SELECT USING (auth.uid() = kullanici_id);
DROP POLICY IF EXISTS "dt_takipler_kendi_yazar" ON public.dt_takipler;
CREATE POLICY "dt_takipler_kendi_yazar" ON public.dt_takipler
  FOR INSERT WITH CHECK (auth.uid() = kullanici_id);
DROP POLICY IF EXISTS "dt_takipler_kendi_siler" ON public.dt_takipler;
CREATE POLICY "dt_takipler_kendi_siler" ON public.dt_takipler
  FOR DELETE USING (auth.uid() = kullanici_id);

-- REVOKE ŞART (derinlemesine savunma): RLS anon'u satır bazında zaten durduruyor ama
-- tablo-geneli yetki varsayılan ayrıcalıklardan doğuştan geliyor; bırakılmamalı.
REVOKE ALL ON public.dt_takipler FROM anon;
GRANT SELECT, INSERT, DELETE ON public.dt_takipler TO authenticated;
GRANT SELECT, INSERT, DELETE, UPDATE ON public.dt_takipler TO service_role;
-- anon'a HİÇ grant yok — misafir takip edemez (mevcut Takip.js zaten girişsiz yalnız
-- localStorage kullanır, DB'ye hiç yazmaz; bu tablo yalnız login'li kullanıcı için).

COMMIT;

NOTIFY pgrst, 'reload schema';

-- Doğrulama (elle):
--   SELECT * FROM dt_kategori_sayim() ORDER BY toplam DESC LIMIT 5;
--   SET ROLE authenticated; SELECT * FROM dt_idare_sayim() LIMIT 3; RESET ROLE;
--   SET ROLE anon; SELECT * FROM dt_idare_sayim();  -- 42501 (insufficient_privilege) beklenir
--   RESET ROLE;
