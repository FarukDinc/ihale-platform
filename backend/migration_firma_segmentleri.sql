-- ============================================================
-- FİRMA SEGMENTLERİ — İhalePro paritesi (25 Tem 2026)
-- Parlayan Yıldızlar · Sönen Yıldızlar · İlk Kez Kazananlar · 150Mn+ Kazananlar
--
-- ⚠️ VERİ TAMLIĞI: Bu segmentler firmanın TAM kazanç geçmişine dayanır. Sonuç
-- backfill %100 olmadan çalıştırılırsa YANLIŞ çıkar — özellikle "İlk Kez Kazananlar"
-- (firma sadece eski kazanımı henüz yüklenmediği için 'ilk kez' görünür). Bu migration
-- ALTYAPIYI kurar; gerçek sayılar sonuç backfill bitince `yuklenici_segment_yenile()`
-- tek çağrısıyla üretilir. Eşikler tam veride kalibre edilecek (bkz. İhalePro sayıları:
-- Parlayan ~1.858 · İlk Kez ~7.238 · 150Mn+ ~2.816 · Sönen ~15.479).
--
-- Kaynak: ihale_sonuclari (kazıma YOK, mevcut veriden türetilir). Zaman çapası:
-- verideki en güncel gerçek sonuç tarihi (gelecekteki 2027/2028 çöp tarihler hariç).
-- ============================================================

BEGIN;

-- ── Segment kolonları + pencere ciroları (görüntüleme için) ──
ALTER TABLE public.yukleniciler
  ADD COLUMN IF NOT EXISTS ciro_son_12ay      bigint,
  ADD COLUMN IF NOT EXISTS ciro_onceki_12ay   bigint,
  ADD COLUMN IF NOT EXISTS buyume_yuzde       numeric,
  ADD COLUMN IF NOT EXISTS seg_parlayan       boolean DEFAULT false,
  ADD COLUMN IF NOT EXISTS seg_sonen          boolean DEFAULT false,
  ADD COLUMN IF NOT EXISTS seg_ilk_kez        boolean DEFAULT false,
  ADD COLUMN IF NOT EXISTS seg_150mn          boolean DEFAULT false,
  ADD COLUMN IF NOT EXISTS segment_guncellendi timestamptz;

CREATE OR REPLACE FUNCTION public.yuklenici_segment_yenile()
RETURNS integer
LANGUAGE plpgsql
AS $$
DECLARE
  ref_tarih date;
  guncellenen integer;
BEGIN
  -- Zaman çapası: verideki en güncel GERÇEK sonuç tarihi (gelecek çöp tarihleri ele).
  SELECT max(sonuc_tarihi)::date INTO ref_tarih
  FROM public.ihale_sonuclari
  WHERE sonuc_tarihi <= now();
  IF ref_tarih IS NULL THEN
    ref_tarih := current_date;
  END IF;

  WITH pencere AS (
    SELECT
      public.normalize_firma(s.kazanan_firma) AS normalize_ad,
      SUM(s.kazanan_teklif) FILTER (
        WHERE s.sonuc_tarihi >  (ref_tarih - INTERVAL '12 months')
          AND s.sonuc_tarihi <= ref_tarih)                     AS son12,
      SUM(s.kazanan_teklif) FILTER (
        WHERE s.sonuc_tarihi >  (ref_tarih - INTERVAL '24 months')
          AND s.sonuc_tarihi <= (ref_tarih - INTERVAL '12 months')) AS onceki12,
      COUNT(*) FILTER (
        WHERE s.sonuc_tarihi >  (ref_tarih - INTERVAL '12 months')
          AND s.sonuc_tarihi <= ref_tarih)                     AS say12,
      MIN(s.sonuc_tarihi)::date AS ilk_tarih,
      COALESCE(SUM(s.kazanan_teklif), 0) AS toplam
    FROM public.ihale_sonuclari s
    WHERE s.kazanan_firma IS NOT NULL
      AND public.normalize_firma(s.kazanan_firma) IS NOT NULL
      AND s.sonuc_tarihi IS NOT NULL
    GROUP BY public.normalize_firma(s.kazanan_firma)
  ),
  hesap AS (
    SELECT
      normalize_ad,
      COALESCE(son12, 0)    AS son12,
      COALESCE(onceki12, 0) AS onceki12,
      COALESCE(say12, 0)    AS say12,
      ilk_tarih, toplam,
      CASE WHEN COALESCE(onceki12,0) > 0
           THEN round(((COALESCE(son12,0)::numeric / onceki12) - 1) * 100, 1)
           ELSE NULL END AS buyume
    FROM pencere
  )
  UPDATE public.yukleniciler y SET
    ciro_son_12ay    = h.son12,
    ciro_onceki_12ay = h.onceki12,
    buyume_yuzde     = h.buyume,
    -- İLK KEZ: firmanın ilk kazanımı son 12 ayda + gerçek bir iş (≥ 100K)
    seg_ilk_kez  = (h.ilk_tarih > (ref_tarih - INTERVAL '12 months')::date
                    AND h.toplam >= 100000),
    -- 150MN+: kümülatif ciro ≥ 150.000.000 TL
    seg_150mn    = (h.toplam >= 150000000),
    -- PARLAYAN: son 12 ay anlamlı (≥5Mn) ve önceki döneme göre ≥2x büyüme;
    --           YA DA yeni gelip büyük iş yapan (ilk kez + son12 ≥ 20Mn)
    seg_parlayan = (
        (h.son12 >= 5000000 AND h.onceki12 > 0 AND h.son12 >= h.onceki12 * 2)
        OR (h.ilk_tarih > (ref_tarih - INTERVAL '12 months')::date AND h.son12 >= 20000000)
    ),
    -- SÖNEN: önceki dönem anlamlıydı (≥5Mn) ama son 12 ayda %70+ düştü (sıfır dahil)
    seg_sonen    = (h.onceki12 >= 5000000 AND h.son12 <= h.onceki12 * 0.3),
    segment_guncellendi = now()
  FROM hesap h
  WHERE y.normalize_ad = h.normalize_ad;

  GET DIAGNOSTICS guncellenen = ROW_COUNT;
  RETURN guncellenen;
END;
$$;

GRANT EXECUTE ON FUNCTION public.yuklenici_segment_yenile() TO service_role;

-- ── Kısmi indeksler (her segment listesi hızlı gelsin) ──
CREATE INDEX IF NOT EXISTS ix_yuk_seg_parlayan ON public.yukleniciler (ciro_son_12ay DESC) WHERE seg_parlayan;
CREATE INDEX IF NOT EXISTS ix_yuk_seg_sonen    ON public.yukleniciler (ciro_onceki_12ay DESC) WHERE seg_sonen;
CREATE INDEX IF NOT EXISTS ix_yuk_seg_ilkkez   ON public.yukleniciler (ilk_sozlesme_tarihi DESC) WHERE seg_ilk_kez;
CREATE INDEX IF NOT EXISTS ix_yuk_seg_150mn    ON public.yukleniciler (toplam_ciro DESC) WHERE seg_150mn;

-- ── Segment sayaçları (dashboard/başlık rozeti için, tek jsonb) ──
CREATE OR REPLACE FUNCTION public.firma_segment_sayilari()
RETURNS jsonb
LANGUAGE sql STABLE
AS $$
  SELECT jsonb_build_object(
    'parlayan', count(*) FILTER (WHERE seg_parlayan),
    'sonen',    count(*) FILTER (WHERE seg_sonen),
    'ilk_kez',  count(*) FILTER (WHERE seg_ilk_kez),
    'yuz50mn',  count(*) FILTER (WHERE seg_150mn),
    'guncellendi', max(segment_guncellendi)
  )
  FROM public.yukleniciler;
$$;

-- ── Segment listesi RPC'si (login-gated; sayfalı; jsonb döner — client-load-all dersi) ──
-- p_segment: 'parlayan' | 'sonen' | 'ilk_kez' | '150mn'
CREATE OR REPLACE FUNCTION public.firma_segment_listesi(
  p_segment text, p_limit int DEFAULT 50, p_offset int DEFAULT 0)
RETURNS jsonb
LANGUAGE sql STABLE
AS $$
  WITH kaynak AS (
    SELECT id, ad, il, toplam_ciro, toplam_sozlesme_sayisi,
           ciro_son_12ay, ciro_onceki_12ay, buyume_yuzde,
           ilk_sozlesme_tarihi, son_sozlesme_tarihi,
           CASE p_segment
             WHEN 'parlayan' THEN ciro_son_12ay
             WHEN 'sonen'    THEN ciro_onceki_12ay
             WHEN 'ilk_kez'  THEN extract(epoch FROM ilk_sozlesme_tarihi)::bigint
             ELSE toplam_ciro END AS sirala
    FROM public.yukleniciler
    WHERE (p_segment = 'parlayan' AND seg_parlayan)
       OR (p_segment = 'sonen'    AND seg_sonen)
       OR (p_segment = 'ilk_kez'  AND seg_ilk_kez)
       OR (p_segment = '150mn'    AND seg_150mn)
  ),
  say AS (SELECT count(*) AS toplam FROM kaynak)
  SELECT jsonb_build_object(
    'toplam', (SELECT toplam FROM say),
    'firmalar', COALESCE(jsonb_agg(to_jsonb(k) - 'sirala'), '[]'::jsonb)
  )
  FROM (SELECT * FROM kaynak ORDER BY sirala DESC NULLS LAST LIMIT p_limit OFFSET p_offset) k;
$$;

GRANT EXECUTE ON FUNCTION public.firma_segment_sayilari()                 TO authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.firma_segment_listesi(text, int, int)    TO authenticated, service_role;
-- anon KASITLI dışarıda: firma ad listeleri login gerektirir (bkz. veri-disa-aktarim-yasagi)

COMMIT;

NOTIFY pgrst, 'reload schema';

-- Manuel (test): SELECT public.yuklenici_segment_yenile();
--                SELECT public.firma_segment_sayilari();
