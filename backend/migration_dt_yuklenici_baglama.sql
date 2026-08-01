-- ============================================================
-- DT kazanan → yukleniciler.id bağlama (MADDE 16 part-2, 1 Ağu 2026)
-- ------------------------------------------------------------
-- SORUN: dogrudan_temin_sonuclari.yuklenici_id BOŞTU (2.008.216/2.008.216 NULL) — dt_kazanan_scraper
--   "yuklenici_id linkleme ileride" bırakmıştı. ihale_sonuclari tarafı yuklenici_yenile() içinde ZATEN
--   normalize_firma(kazanan_firma)=normalize_ad ile dolduruluyor; DT için AYNI kesin isim-eşitliğini
--   uygulayan eş fonksiyon budur.
--
-- SAHTE-POZİTİF: yukleniciler.normalize_ad BENZERSIZ (220.181/220.181, 0 belirsiz grup — denetlendi)
--   → her DT adı EN FAZLA TEK firmaya bağlanır. Kalan risk (iki farklı gerçek firmanın aynı normalize'a
--   düşmesi) "birlikte" modunun ZATEN kabul ettiğiyle aynı; yeni risk EKLEMEZ. yukleniciler İHALE
--   evreninden üretildiği için yalnız ihale de kazanmış DT firmaları eşleşir; kalan yuklenici_id NULL
--   = DOĞRU (uydurmuyoruz).
--
-- id SABİT: yuklenici_yenile ON CONFLICT(normalize_ad) DO UPDATE (upsert) → id değişmez, bağ KALICI.
--
-- GÜVENLİK/SAHİPLİK: fonksiyon postgres sahipli + SECURITY INVOKER (yuklenici_yenile ile AYNI model)
--   → gece cron `-U postgres` çağırabilir; normalize_firma EXECUTE + tablo UPDATE yetkisi postgres'te
--   MEVCUT (denetlendi) → owner-devri/grant tuzağı YOK (bkz. migration_mv_owner_fix dersi).
--
-- Çalıştır:
--   docker exec -i supabase-db psql -U supabase_admin -d postgres < backend/migration_dt_yuklenici_baglama.sql
--   sonra BİR KEZ backfill:  SELECT public.dt_yuklenici_baglama();   -- ilk koşu ~2M tarar (dakikalar)
-- Gece tazeleme: run_scraper.sh yuklenici_yenile()'den HEMEN SONRA SELECT public.dt_yuklenici_baglama();
-- ============================================================

CREATE OR REPLACE FUNCTION public.dt_yuklenici_baglama()
RETURNS integer
LANGUAGE plpgsql
SET statement_timeout TO '1800000'   -- 30 dk: ilk backfill 2M satır tarar; gece incremental (guard'lı)
AS $function$
DECLARE
  baglanan INTEGER;
BEGIN
  -- Kesin isim-eşitliği (normalize_firma = normalize_ad). IS DISTINCT FROM guard'ı sayesinde:
  -- ilk koşu = tam backfill (tüm eşleşen NULL'lar dolar); sonraki geceler = yalnız DEĞİŞEN satır yazılır.
  -- Eşleşmeyen (yukleniciler'de olmayan) DT satırları HİÇ yazılmaz → yuklenici_id NULL kalır (doğru).
  UPDATE public.dogrudan_temin_sonuclari s
  SET yuklenici_id = y.id
  FROM public.yukleniciler y
  WHERE s.kazanan_firma IS NOT NULL
    AND public.normalize_firma(s.kazanan_firma) = y.normalize_ad
    AND s.yuklenici_id IS DISTINCT FROM y.id;
  GET DIAGNOSTICS baglanan = ROW_COUNT;
  RETURN baglanan;
END;
$function$;

ALTER FUNCTION public.dt_yuklenici_baglama() OWNER TO postgres;
