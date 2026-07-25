-- ============================================================
-- YASAKLI FİRMALAR — İhalelere katılmaktan yasaklananlar (25 Tem 2026)
-- Kaynak: EKAP Yasaklı Sorgulama + Resmî Gazete yasaklama kararları (~17.055 kayıt).
-- Şema alanları: Firma Adı · Karar Veren Kurum · Başlangıç · Bitiş · Süre · Kanun md.
--
-- ⚠️ VERİ: Bu migration ŞEMA+RPC+indeks kurar. Asıl liste EKAP korumalı endpoint'inden
-- kazınır (bkz. [[ekap-crypto-headers]]) — proxy-yoğun; sonuç backfill bitip bir havuz
-- boşalınca backend/yasakli_scraper.py ile doldurulur. Yasaklılar KANUNEN KAMUYA AÇIK
-- (Resmî Gazete) ama liste yine de login-gated (bulk veri kuralı, veri-disa-aktarim-yasagi);
-- firma-analiz'de per-firma rozet olarak da okunur.
-- ============================================================

BEGIN;

CREATE TABLE IF NOT EXISTS public.yasakli_firmalar (
  id                uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  firma_ad          text NOT NULL,
  normalize_ad      text,                    -- normalize_firma() ile — firma-analiz join'i
  karar_veren_kurum text,
  yasak_baslangic   date,
  yasak_bitis       date,
  yasak_suresi      text,                    -- "1 yıl", "2 yıl" vb. (ham metin)
  tc_vergi_no       text,
  kanun_madde       text,                    -- yasaklanan kanun maddesi (4734/58 vb.)
  uyruk             text,
  il                text,
  kaynak            text DEFAULT 'ekap',     -- ekap | resmi_gazete
  resmi_gazete_tarih date,
  aktif             boolean,                 -- yasak_bitis > now() → hâlâ yasaklı
  olusturulma       timestamptz DEFAULT now(),
  guncellenme       timestamptz DEFAULT now()
);

-- Aynı firma+başlangıç+kurum kaydını tekrar yazma (idempotent scrape)
CREATE UNIQUE INDEX IF NOT EXISTS ux_yasakli_dedup
  ON public.yasakli_firmalar (firma_ad, yasak_baslangic, COALESCE(karar_veren_kurum,''));
CREATE INDEX IF NOT EXISTS ix_yasakli_normalize ON public.yasakli_firmalar (normalize_ad);
CREATE INDEX IF NOT EXISTS ix_yasakli_aktif     ON public.yasakli_firmalar (aktif) WHERE aktif;
CREATE INDEX IF NOT EXISTS ix_yasakli_baslangic ON public.yasakli_firmalar (yasak_baslangic DESC);

-- aktif bayrağını tazele (gece cron)
CREATE OR REPLACE FUNCTION public.yasakli_aktif_tazele()
RETURNS integer LANGUAGE plpgsql AS $$
DECLARE n integer;
BEGIN
  UPDATE public.yasakli_firmalar
    SET aktif = (yasak_bitis IS NULL OR yasak_bitis >= current_date),
        guncellenme = now()
    WHERE aktif IS DISTINCT FROM (yasak_bitis IS NULL OR yasak_bitis >= current_date);
  GET DIAGNOSTICS n = ROW_COUNT; RETURN n;
END; $$;

-- Liste RPC (login-gated, sayfalı, jsonb) — arama + yalnız-aktif filtresi
CREATE OR REPLACE FUNCTION public.yasakli_listesi(
  p_ara text DEFAULT NULL, p_yalniz_aktif boolean DEFAULT true,
  p_limit int DEFAULT 50, p_offset int DEFAULT 0)
RETURNS jsonb LANGUAGE sql STABLE AS $$
  WITH kaynak AS (
    SELECT id, firma_ad, karar_veren_kurum, yasak_baslangic, yasak_bitis,
           yasak_suresi, kanun_madde, il, aktif
    FROM public.yasakli_firmalar
    WHERE (NOT p_yalniz_aktif OR aktif)
      AND (p_ara IS NULL OR firma_ad ILIKE '%'||p_ara||'%')
  ),
  say AS (SELECT count(*) AS toplam FROM kaynak)
  SELECT jsonb_build_object(
    'toplam', (SELECT toplam FROM say),
    'kayitlar', COALESCE(jsonb_agg(to_jsonb(k) ORDER BY k.yasak_baslangic DESC NULLS LAST), '[]'::jsonb)
  )
  FROM (SELECT * FROM kaynak ORDER BY yasak_baslangic DESC NULLS LAST LIMIT p_limit OFFSET p_offset) k;
$$;

-- Per-firma yasaklılık kontrolü (firma-analiz rozeti için) — normalize eşleşme
CREATE OR REPLACE FUNCTION public.firma_yasakli_mi(p_firma text)
RETURNS jsonb LANGUAGE sql STABLE AS $$
  SELECT COALESCE(jsonb_agg(to_jsonb(y)), '[]'::jsonb)
  FROM (
    SELECT firma_ad, karar_veren_kurum, yasak_baslangic, yasak_bitis, yasak_suresi, aktif
    FROM public.yasakli_firmalar
    WHERE normalize_ad = public.normalize_firma(p_firma)
    ORDER BY yasak_baslangic DESC NULLS LAST
  ) y;
$$;

GRANT SELECT ON public.yasakli_firmalar TO authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.yasakli_aktif_tazele()                      TO service_role;
GRANT EXECUTE ON FUNCTION public.yasakli_listesi(text, boolean, int, int)    TO authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.firma_yasakli_mi(text)                      TO authenticated, service_role;
-- anon KASITLI dışarıda (bulk firma verisi login gerektirir)

COMMIT;

NOTIFY pgrst, 'reload schema';
