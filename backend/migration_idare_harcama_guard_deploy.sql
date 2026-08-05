-- =============================================================================
-- migration_idare_harcama_guard_deploy.sql — SIKIŞAN fiziksel-sanite guard'ını deploy
-- 5 Ağu 2026
-- =============================================================================
--
-- DURUM (denetimle bulundu): Hakkari-tipi bozuk-sözleşme harcama düzeltmesi commit'li
-- (4144407) AMA canlıya UYGULANMAMIŞ. Dahası canlı idare_harcama_mv ile commit'li
-- dosya DİVERGE: canlı `count(DISTINCT ikn)` (bellek+kullanıcı onaylı doğru sözleşme
-- sayımı, çok-lot şişmesini önler) ama guard YOK; commit'li dosya `count(*)` + guard.
-- Nihai doğru hedef (bellek: bozuk-sozlesme-bedeli-harcama) = DISTINCT ikn + guard.
--
-- BU MIGRATION: canlı DISTINCT-ikn sayımını KORUYARAK fiziksel-sanite guard'ını ekler.
-- idare_dizin_json'a DOKUNMAZ (B3 detsisli sürüm canlıda kalır — commit'li 4144407'nin
-- isimle-join dizin_json'u B3'ü ezerdi; onu bilinçle atlıyoruz).
--
-- GUARD: sözleşme bedeli, yaklaşık maliyetin 50 katından çok olamaz (maliyeti bilinen
-- imkansızları dışla; meşru dev ihaleler ratio~1 korunur). ~1931 lot / ₺20,6 Mr dışlanır.
--
-- Uygulama:
--   ssh ihale2 "docker exec -i supabase-db psql -U postgres -d postgres" < backend/migration_idare_harcama_guard_deploy.sql
-- =============================================================================

BEGIN;

DROP MATERIALIZED VIEW IF EXISTS public.idare_harcama_mv;
CREATE MATERIALIZED VIEW public.idare_harcama_mv AS
SELECT il.idare,
       count(DISTINCT s.ikn)::bigint                AS sozlesme_sayisi,   -- çok-lot şişmesini önler (canlı+bellek)
       COALESCE(sum(s.sozlesme_bedeli), 0)::numeric AS toplam_harcama
FROM public.ihale_sonuclari s
JOIN (
  -- ikn → idare TEKİL eşleme (ilanlar.ikn tekrar edebilir → cross-product şişmesini önle)
  SELECT DISTINCT ON (ikn) ikn, idare
  FROM public.ilanlar
  WHERE idare IS NOT NULL AND ikn IS NOT NULL
  ORDER BY ikn
) il ON il.ikn = s.ikn
WHERE s.sozlesme_bedeli > 0
  -- FİZİKSEL SANİTE (5 Ağu, 4144407'den): kazanan/sözleşme bedeli, yaklaşık maliyetin 50
  -- katından ÇOK olamaz. Eski (2012-2013) veride bozuk-şişmiş parse (ör. Hakkari sahte 312 Mr,
  -- maliyeti 740 ₺ olan kısma 1,4 Mr "sözleşme"). Meşru dev ihaleler (ratio~1) korunur.
  AND NOT (s.yaklasik_maliyet > 0 AND s.sozlesme_bedeli > 50 * s.yaklasik_maliyet)
GROUP BY il.idare;

CREATE UNIQUE INDEX idx_idare_harcama_mv_idare ON public.idare_harcama_mv USING btree (idare);
ALTER MATERIALIZED VIEW public.idare_harcama_mv OWNER TO postgres;   -- gece REFRESH -U postgres
REVOKE ALL ON public.idare_harcama_mv FROM PUBLIC, anon;

COMMIT;

NOTIFY pgrst, 'reload schema';

-- =============================================================================
-- DOĞRULAMA:
--   SELECT idare, round(toplam_harcama/1e9,1) mr, sozlesme_sayisi
--     FROM idare_harcama_mv ORDER BY toplam_harcama DESC LIMIT 5;   -- top-3 meşru (TOKİ/Karayolları)
--   -- grand total ~₺20,6 Mr düşmeli (guard dışladı)
-- =============================================================================
