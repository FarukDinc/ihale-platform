-- ============================================================================
-- migration_idare_harcama.sql — UV-6: Kurumlar listesine PARA (3 Ağu 2026)
--
-- Rakip (ihalepro) Kurumlar tablosunda "Sözleşme Sayısı" + "Toplam Harcama Tutarı"
-- var; bizde idare listesinde para YOKtu (yalnız ihale/DT SAYISI). Bu migration
-- idare-bazında harcamayı ekler.
--
-- KAYNAK: ihale_sonuclari'nda idare KOLONU YOK → idare ilanlar'dan ikn eşlemesiyle
-- gelir. ilanlar.ikn tekil olmayabilir (çok-lot/dedup) → DISTINCT ON (ikn) ile ikn→idare
-- tekilleştirilir (cross-product/şişme önlenir). Harcama = sum(sozlesme_bedeli>0).
--
-- Ağır join (539K sonuç ⋈ 1.6M ilan) → MV (gece REFRESH; run_scraper.sh'e eklenecek).
-- ANON KAPALI (idare_dizin_json zaten authenticated-only; MV'yi de yalnız authenticated'a aç).
--
-- Çalıştırma:
--   docker exec -i supabase-db psql -U supabase_admin -d postgres < backend/migration_idare_harcama.sql
-- ============================================================================

BEGIN;

-- Tanım değişti (fiziksel-sanite filtresi) → IF NOT EXISTS yerine DROP+CREATE.
DROP MATERIALIZED VIEW IF EXISTS public.idare_harcama_mv;
CREATE MATERIALIZED VIEW public.idare_harcama_mv AS
SELECT il.idare,
       count(*)::bigint                          AS sozlesme_sayisi,
       COALESCE(sum(s.sozlesme_bedeli), 0)::numeric AS toplam_harcama
FROM public.ihale_sonuclari s
JOIN (
  -- ikn → idare TEKİL eşleme (ilanlar.ikn tekrar edebilir → şişmeyi önle)
  SELECT DISTINCT ON (ikn) ikn, idare
  FROM public.ilanlar
  WHERE idare IS NOT NULL AND ikn IS NOT NULL
  ORDER BY ikn
) il ON il.ikn = s.ikn
WHERE s.sozlesme_bedeli > 0
  -- FİZİKSEL SANİTE (5 Ağu): kazanan teklif, yaklaşık maliyetin 50 katından ÇOK olamaz. Eski
  -- (2012-2013 ağırlıklı) veride kazanan_teklif/sozlesme_bedeli bozuk-şişmiş parse edilmiş
  -- (13.977 lot / 936 ihale / ~505 Mr HAYALET harcama) → harcama sıralamasını zehirliyordu:
  -- ör. Hakkari hastane birliği sahte 312 Mr (maliyeti 740 ₺ olan kısma 1,4 Mr "sözleşme").
  -- Meşru dev ihaleler korunur (sözleşme ≈ maliyet, ratio ~1). Maliyeti bilinen imkansızları dışla.
  AND NOT (s.yaklasik_maliyet > 0 AND s.sozlesme_bedeli > 50 * s.yaklasik_maliyet)
GROUP BY il.idare;

CREATE UNIQUE INDEX IF NOT EXISTS idx_idare_harcama_mv_idare
  ON public.idare_harcama_mv (idare);

ANALYZE public.idare_harcama_mv;

-- KRİTİK: gece REFRESH `-U postgres` ile koşuyor → sahip postgres OLMALI (yoksa sessiz-bayat).
ALTER MATERIALIZED VIEW public.idare_harcama_mv OWNER TO postgres;

-- anon'a AÇMA (maske dersi): yalnız authenticated + service_role. idare_dizin_json
-- SECURITY DEFINER olduğu için MV'yi sahibi olarak okur; grant caller için sadece tutarlılık.
REVOKE ALL ON public.idare_harcama_mv FROM PUBLIC, anon;
GRANT SELECT ON public.idare_harcama_mv TO authenticated, service_role;

-- idare_dizin_json'a [6]=sözleşme sayısı, [7]=toplam harcama ekle (DT join'i korunur)
CREATE OR REPLACE FUNCTION public.idare_dizin_json()
RETURNS jsonb
LANGUAGE sql STABLE SECURITY DEFINER SET search_path = public AS $$
  SELECT COALESCE(jsonb_agg(
    jsonb_build_array(i.idare, i.toplam, i.aktif, i.en_yakin_il,
                      COALESCE(d.toplam, 0), COALESCE(d.aktif, 0),
                      COALESCE(h.sozlesme_sayisi, 0), COALESCE(h.toplam_harcama, 0))
    ORDER BY i.toplam DESC), '[]'::jsonb)
  FROM public.idare_ozet_mv i
  LEFT JOIN public.dt_idare_ozet_mv d ON d.idare = i.idare
  LEFT JOIN public.idare_harcama_mv h ON h.idare = i.idare;
$$;
ALTER FUNCTION public.idare_dizin_json() SET statement_timeout = '20s';
GRANT EXECUTE ON FUNCTION public.idare_dizin_json() TO authenticated, service_role;

COMMIT;

NOTIFY pgrst, 'reload schema';

-- DOĞRULAMA:
--   SELECT jsonb_array_length((public.idare_dizin_json())->0);  -- 8 olmalı
--   SELECT idare, sozlesme_sayisi, toplam_harcama FROM public.idare_harcama_mv ORDER BY toplam_harcama DESC LIMIT 5;
