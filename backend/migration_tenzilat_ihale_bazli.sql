-- ============================================================
-- İhaleGlobal — Ort. Tenzilat düzeltmesi (çok-lotlu ihale hatası)
--
-- SORUN: ihale_sonuclari satır başına bir KISIM/lot tutar (kisim_no, upsert ilan_id,kisim_no).
-- Çok-lotlu ihalelerde EKAP, ihalenin TOPLAM yaklasik_maliyet'ini HER lot satırına kopyalıyor —
-- 46.083 çok-lotlu ihalenin 46.077'sinde (%99,99) ym tüm satırlarda birebir aynı. Satır-bazlı
-- tenzilat = (ym - lot_teklifi)/ym olduğundan küçük lot teklifi ÷ dev TOPLAM maliyet = sahte ~%95.
--   Örnek (5 lot, ym=6.297.340 her satırda): teklifler 293.420/1.007.900/59.760/256.500/210.000
--   → kaydedilen tenzilatlar %95,3/%84,0/%99,1/%95,9/%96,7. Gerçek: teklif toplamı 1.827.580
--   = ym'nin %29'u → ihale tenzilatı ≈%71.
-- Etki: 246.639 satır (%46). %90-100 bandındaki 158.755 kaydın %99,2'si çok-lotlu.
-- MV ortalaması bu yüzden %48,3 çıkıyordu (tek-lot %14,75 ile çok-lot %86,78'in karışımı).
--
-- ÇÖZÜM: tenzilat İHALE BAZINDA — önce lot teklifleri toplanır, sonra tek maliyete bölünür:
--   (max(yaklasik_maliyet) - sum(kazanan_teklif)) / max(yaklasik_maliyet) * 100
-- Ölçüm: ort %16,96 / medyan %12,43 (n=328.823 ihale). Tek-lot %14,75 · çok-lot %30,66 — gerçekçi.
--
-- toplam / toplam_bedel / farkli_firma AYNEN korundu; yalnız ort_tenzilat düzeltildi.
-- NOT: ilanlar.yaklasik_maliyet_min sonuçlu ihalelerde neredeyse hiç dolu değil (20 kayıt) →
--      payda olarak ihale_sonuclari.yaklasik_maliyet kullanılır (530.440 kayıtta dolu).
--
-- Çalıştırma:
--   docker exec -i supabase-db psql -U postgres -d postgres < backend/migration_tenzilat_ihale_bazli.sql
-- ============================================================

BEGIN;

DROP MATERIALIZED VIEW IF EXISTS public.sonuc_ozet_mv;

CREATE MATERIALIZED VIEW public.sonuc_ozet_mv AS
WITH ihale AS (          -- ihale başına: maliyet (lotlarda tekrarlı → max) + lot tekliflerinin TOPLAMI
  SELECT ilan_id,
         max(yaklasik_maliyet) AS ym,
         sum(kazanan_teklif)   AS toplam_teklif
  FROM   public.ihale_sonuclari
  WHERE  yaklasik_maliyet IS NOT NULL AND yaklasik_maliyet > 0
    AND  kazanan_teklif IS NOT NULL
  GROUP  BY ilan_id
),
tenz AS (
  SELECT ((ym - toplam_teklif)::numeric / ym * 100) AS t FROM ihale
),
temel AS (
  SELECT count(*)                                        AS toplam,
         sum(COALESCE(kazanan_teklif, sozlesme_bedeli))  AS toplam_bedel,
         count(DISTINCT kazanan_firma)                   AS farkli_firma
  FROM   public.ihale_sonuclari
  WHERE  kazanan_firma IS NOT NULL AND kazanan_firma <> ''
)
SELECT 1 AS id,
       t.toplam,
       t.toplam_bedel,
       (SELECT round(avg(x.t), 1) FROM tenz x WHERE x.t BETWEEN -100 AND 100) AS ort_tenzilat,
       t.farkli_firma
FROM   temel t;

-- REFRESH MATERIALIZED VIEW CONCURRENTLY için ŞART (eski adıyla birebir)
CREATE UNIQUE INDEX idx_sonuc_ozet_mv_pk ON public.sonuc_ozet_mv USING btree (id);

-- Eski ACL birebir geri: anon=r, authenticated=arwd, service_role=r
GRANT SELECT                         ON public.sonuc_ozet_mv TO anon;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.sonuc_ozet_mv TO authenticated;
GRANT SELECT                         ON public.sonuc_ozet_mv TO service_role;

COMMIT;

-- Doğrulama: ort_tenzilat ~17 olmalı (48.3 değil); diğer 3 alan değişmemeli
SELECT * FROM public.sonuc_ozet_mv;
