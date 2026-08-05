-- =============================================================================
-- migration_firmam_iki_evren.sql — "Benim Firmam": İhale + DT'yi BİRLİKTE döndür (5 Ağu 2026)
-- =============================================================================
-- İKİ EVREN SÖZLEŞMESİ referans uygulaması (bkz. IKI_EVREN.md, bellek iki-evren-ihale-dt).
-- Eski firmam_getir TEK evren dönüyordu (ya ihale ya DT). Şimdi HER İKİSİ:
--   {ad, il, firma_id, dt_mi, has_ihale, has_dt, ihale:{...}|null, dt:{...}|null}
-- BAĞLAMA = normalize anahtar (y.normalize_ad = d.firma_norm), ASLA ad=ad (çok-yazımlı firma ıskalanır).
-- firma_id/dt_mi geriye-dönük korunur (js/firmam.js, v1-uyumluluk.html okuyor).
-- Uygula: docker exec -i supabase-db psql -U supabase_admin -d postgres < backend/migration_firmam_iki_evren.sql
-- =============================================================================

BEGIN;

CREATE OR REPLACE FUNCTION public.firmam_getir()
RETURNS jsonb LANGUAGE sql STABLE SECURITY DEFINER SET search_path = public AS $$
  SELECT CASE
    -- (1) İHALE firması seçili (profil.firma_id dolu): ihale=yukleniciler; DT=AYNI normalize anahtarıyla.
    WHEN kp.firma_id IS NOT NULL THEN
      jsonb_build_object(
        'ad',        y.ad,
        'il',        y.il,
        'firma_id',  y.id,
        'dt_mi',     false,
        'has_ihale', true,
        'has_dt',    (dti.firma_norm IS NOT NULL),
        'ihale', jsonb_build_object(
                   'ad',       y.ad,
                   'sozlesme', COALESCE(y.toplam_sozlesme_sayisi,0),
                   'ciro',     COALESCE(y.toplam_ciro,0)),
        'dt',    CASE WHEN dti.firma_norm IS NULL THEN NULL
                      ELSE jsonb_build_object(
                        'ad',       dti.ad,
                        'sozlesme', dti.dt_sozlesme,
                        'bedel',    dti.dt_bedel) END)
    -- (2) DT firması seçili (profil.firma_dt_ad dolu): DT=firma_dt_toplam; ihale=AYNI anahtarla yukleniciler (varsa).
    WHEN kp.firma_dt_ad IS NOT NULL THEN
      jsonb_build_object(
        'ad',        COALESCE(y2.ad, dt.ad),
        'il',        COALESCE(y2.il,
                       (SELECT di.il FROM public.dogrudan_temin_sonuclari s
                          JOIN public.dogrudan_temin_ilanlari di ON di.dt_no = s.dt_no
                         WHERE s.kazanan_firma = kp.firma_dt_ad AND di.il IS NOT NULL
                         GROUP BY di.il ORDER BY count(*) DESC LIMIT 1)),
        'firma_id',  y2.id,
        'dt_mi',     (y2.id IS NULL),
        'has_ihale', (y2.id IS NOT NULL),
        'has_dt',    true,
        'ihale', CASE WHEN y2.id IS NULL THEN NULL
                      ELSE jsonb_build_object(
                        'ad',       y2.ad,
                        'sozlesme', COALESCE(y2.toplam_sozlesme_sayisi,0),
                        'ciro',     COALESCE(y2.toplam_ciro,0)) END,
        'dt',    jsonb_build_object(
                   'ad',       dt.ad,
                   'sozlesme', dt.dt_sozlesme,
                   'bedel',    dt.dt_bedel))
    ELSE NULL END
  FROM public.kullanici_profiller kp
  LEFT JOIN public.yukleniciler    y   ON y.id            = kp.firma_id
  LEFT JOIN public.firma_dt_toplam dti ON dti.firma_norm  = y.normalize_ad     -- ihale firmasının DT'si
  LEFT JOIN public.firma_dt_toplam dt  ON dt.ad           = kp.firma_dt_ad     -- DT-only round-trip
  LEFT JOIN public.yukleniciler    y2  ON y2.normalize_ad = dt.firma_norm      -- DT firmasının ihalesi
  WHERE kp.id = auth.uid();
$$;
REVOKE EXECUTE ON FUNCTION public.firmam_getir() FROM public, anon;
GRANT  EXECUTE ON FUNCTION public.firmam_getir() TO authenticated, service_role;

-- Hardening: firma_dt_kirilim ADA değil NORMALIZE-eşleşme (kart totali ↔ kırılım tutarlılığı; çok-yazımlı firma).
-- Functional index (853K satır; normalize_firma IMMUTABLE) → normalize-match indeksli/hızlı.
CREATE INDEX IF NOT EXISTS idx_dt_sonuc_firma_norm
  ON public.dogrudan_temin_sonuclari (public.normalize_firma(kazanan_firma));

CREATE OR REPLACE FUNCTION public.firma_dt_kirilim(p_firma_ad text)
RETURNS jsonb LANGUAGE sql STABLE SECURITY DEFINER SET search_path = public AS $$
  WITH d AS (
    SELECT di.il, di.kategori, di.idare, s.kazanan_bedel
      FROM public.dogrudan_temin_sonuclari s
      JOIN public.dogrudan_temin_ilanlari di ON di.dt_no = s.dt_no
     WHERE public.normalize_firma(s.kazanan_firma) = public.normalize_firma(p_firma_ad)
  )
  SELECT jsonb_build_object(
    'sektor', (SELECT jsonb_build_object('ad', kategori, 'sayi', count(*))
                 FROM d WHERE kategori IS NOT NULL GROUP BY kategori ORDER BY count(*) DESC LIMIT 1),
    'iller', (SELECT COALESCE(jsonb_agg(jsonb_build_object('il', il, 'sayi', c, 'bedel', b) ORDER BY c DESC), '[]'::jsonb)
                FROM (SELECT il, count(*) c, COALESCE(sum(kazanan_bedel),0) b
                        FROM d WHERE il IS NOT NULL GROUP BY il) x),
    'kurum_sayisi', (SELECT count(DISTINCT idare) FROM d WHERE idare IS NOT NULL));
$$;
REVOKE EXECUTE ON FUNCTION public.firma_dt_kirilim(text) FROM public, anon;
GRANT  EXECUTE ON FUNCTION public.firma_dt_kirilim(text) TO authenticated, service_role;

COMMIT;

NOTIFY pgrst, 'reload schema';
