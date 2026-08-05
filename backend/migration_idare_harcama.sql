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

-- Tanım değişti (KÖK temizlik sonrası: sayı=DISTINCT ikn + filtre kaldırıldı) → DROP+CREATE.
DROP MATERIALIZED VIEW IF EXISTS public.idare_harcama_mv;
CREATE MATERIALIZED VIEW public.idare_harcama_mv AS
SELECT il.idare,
       count(DISTINCT s.ikn)::bigint                AS sozlesme_sayisi,
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
  -- sozlesme_sayisi ARTIK LOT değil İHALE sayar (count DISTINCT ikn) — Hakkari 1726 lot değil
  -- ~240 ihale; Kategoriler tablosuyla tutarlı.
  --
  -- FİZİKSEL-SANİTE FİLTRESİ KALDIRILDI (5 Ağu): eski >50× filtresi kaba bir yara bandıydı —
  -- (a) çerçeve total-kopyalarını dışlarken meşru toplamı da kaybediyor, (b) yaklaşık maliyet=1
  -- placeholder olan MEŞRU büyük sözleşmeleri (~5,6 Mr) yanlışlıkla dışlıyordu. KÖK çözüm artık
  -- ham veride: migration_bozuk_sozlesme_temizle.sql çerçeve tekrarını ve ~1000× şişmeyi NULL'ladı,
  -- gelecekte ekap_sonuc_backfill.py çerçeve-dedup guard'ı önlüyor. Ham temiz → düz toplam doğru.
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

-- NOT (5 Ağu, drift uzlaştırma): idare_dizin_json bu dosyadan ÇIKARILDI. Bu migration eskiden
-- burada isimle-join (d.idare=i.idare, h.idare=i.idare), length-8 bir idare_dizin_json tanımlıyordu.
-- KANONİK tanım artık `migration_idare_dedup_detsis.sql` (B3): detsis_no + hi.ad ile length-10,
-- dedup'lı. Buradaki eski sürüm yeniden uygulanırsa B3'ü EZER → bilinçle kaldırıldı. Bu dosya
-- yalnız idare_harcama_mv'yi yönetir; idare_dizin_json'a DOKUNMAZ.

COMMIT;

NOTIFY pgrst, 'reload schema';

-- DOĞRULAMA:
--   SELECT idare, sozlesme_sayisi, toplam_harcama FROM public.idare_harcama_mv ORDER BY toplam_harcama DESC LIMIT 5;
--   -- idare_dizin_json doğrulaması migration_idare_dedup_detsis.sql'de (length 10, detsis).
