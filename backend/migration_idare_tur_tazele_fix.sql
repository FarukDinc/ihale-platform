-- ============================================================================
-- migration_idare_tur_tazele_fix.sql — idare_tur_tazele() statement timeout
--                                                              (20 Tem 2026)
-- SORUN (ölçüldü): kural backfill 40.027 eşleme yazdı (28.566 → 68.595), ama
--   idare_tur_tazele() çağrısı 57014 "canceling statement due to statement
--   timeout" ile öldü. Eşlemeler tabloda duruyor, ilanlar/DT kolonları BOŞ kaldı.
--
-- İKİ AYRI SEBEP:
--   1) DT'de İFADE İNDEKSİ YOK. migration_idare_tur.sql yalnız ilanlar'a koydu:
--        CREATE INDEX idx_ilanlar_idare_norm ON ilanlar (idare_normalize(idare));
--      dogrudan_temin_ilanlari (1,49M satır) için karşılığı hiç oluşturulmamış →
--      join satır başına fonksiyon çağırıyor.
--   2) Fonksiyonun kendi timeout'u yok. 813K satır güncellenecek; bu bir bakım
--      işi, kullanıcı isteği değil — REST rolünün kısa timeout'una tabi olmamalı.
--
-- ⚠️ İNDEKS KİLİDİ: düz CREATE INDEX tabloya yazma kilidi alır. Bu migration
--   scraper'lar DURURKEN koşulmalı (20 Tem: proxy havuzu 402 ile kapalı, kazıma
--   zaten yok → güvenli an). Kazıma açıkken koşulacaksa CONCURRENTLY kullanın:
--     CREATE INDEX CONCURRENTLY idx_dt_idare_norm ON public.dogrudan_temin_ilanlari
--       (public.idare_normalize(idare));
--   (CONCURRENTLY transaction bloğu İÇİNDE çalışmaz — tek başına gönderilmeli.)
--
-- Çalıştırma (uzun sürer, nohup ile ayrık koşun):
--   nohup docker exec -i supabase-db psql -U postgres -d postgres \
--     -f /dev/stdin < backend/migration_idare_tur_tazele_fix.sql \
--     > /opt/ihale-platform/logs/idare_tazele_fix.log 2>&1 &
-- Idempotent.
-- ============================================================================

-- ── 1) DT ifade indeksi (eksikti) ───────────────────────────────────────────
CREATE INDEX IF NOT EXISTS idx_dt_idare_norm
  ON public.dogrudan_temin_ilanlari (public.idare_normalize(idare));

-- ── 2) Tazeleme fonksiyonu: kendi timeout'u + ilerleme raporu ───────────────
-- SECURITY DEFINER + service_role'a kısıtlı olduğu için uzun timeout güvenli:
-- bu fonksiyonu misafir ya da üye çağıramaz (REVOKE aşağıda korunuyor).
CREATE OR REPLACE FUNCTION public.idare_tur_tazele()
  RETURNS jsonb
  LANGUAGE plpgsql
  SECURITY DEFINER
  SET search_path = public
  SET statement_timeout = '1800s'
AS $$
DECLARE
  n_ilan int;
  n_dt   int;
BEGIN
  UPDATE public.ilanlar i
     SET idare_tur = t.tur
    FROM public.idare_tur t
   WHERE t.idare_norm = public.idare_normalize(i.idare)
     AND i.idare_tur IS DISTINCT FROM t.tur;
  GET DIAGNOSTICS n_ilan = ROW_COUNT;

  UPDATE public.dogrudan_temin_ilanlari d
     SET idare_tur = t.tur
    FROM public.idare_tur t
   WHERE t.idare_norm = public.idare_normalize(d.idare)
     AND d.idare_tur IS DISTINCT FROM t.tur;
  GET DIAGNOSTICS n_dt = ROW_COUNT;

  RETURN jsonb_build_object('ilanlar_guncellenen', n_ilan, 'dt_guncellenen', n_dt);
END;
$$;

REVOKE EXECUTE ON FUNCTION public.idare_tur_tazele() FROM PUBLIC, anon;
GRANT  EXECUTE ON FUNCTION public.idare_tur_tazele() TO service_role;

-- ── 3) Şimdi çalıştır (813K satır — dakikalar sürebilir) ────────────────────
SELECT public.idare_tur_tazele();

NOTIFY pgrst, 'reload schema';

-- Kontrol:
--   SELECT idare_tur, count(*) FROM ilanlar GROUP BY 1 ORDER BY 2 DESC;
--   SELECT count(*) FROM ilanlar WHERE idare_tur IS NULL;                 -- ~0 beklenir
--   SELECT count(*) FROM dogrudan_temin_ilanlari WHERE idare_tur IS NULL; -- ~29K beklenir
