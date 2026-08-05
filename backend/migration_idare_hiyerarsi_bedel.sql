-- =============================================================================
-- migration_idare_hiyerarsi_bedel.sql — UV-6 Faz A.2: kategori/hiyerarşi TUTAR (3 Ağu 2026)
-- =============================================================================
-- HEDEF: Kurum Merkezi kategori kartlarına (v1-kurumlar) rakip ihalepro'daki gibi
-- "Toplam Tutar" eklemek. idare_hiyerarsi_sayim_mv YALNIZ SAYI taşır (bedel yok).
--
-- KARAR: sayim MV'ye DOKUNMA (4 ağaç RPC + kurum_kategori_ozet ona bağlı → yüksek risk).
-- Onun yerine AYNI mekanizmayı (kendi = doğrudan detsis eşleşmesi; toplam = idare_ata_torun
-- kapanışıyla kendisi+torunlar yuvarlaması) bedel için AYNALAYAN paralel bir MV kur.
--
-- BEDEL KAYNAĞI (canlı DB'de doğrulandı 3 Ağu):
--   * İHALE: ihale_sonuclari.sozlesme_bedeli (bigint, ~%100 dolu, 2,72M satır).
--     idare KOLONU YOK → ilanlar'a ikn ile bağlanır. ilanlar.ikn çok-lot nedeniyle
--     TEKRAR eder → DISTINCT ON (ikn) ile ikn→detsis tekilleştir (fanout/şişme önle;
--     idare_harcama_mv'deki kanıtlı desen). Her lot FARKLI sozlesme_bedeli taşıyor
--     (kopyalama YOK — doğrulandı) → tüm lot satırlarını toplamak doğru sözleşme tutarını verir.
--   * DT: dogrudan_temin_sonuclari.kazanan_bedel (numeric, %100 dolu, 2,87M satır).
--     idare KOLONU YOK → dogrudan_temin_ilanlari'na dt_no ile bağlanır (o tabloda detsis_no VAR).
--     para_birimi yalnız 'TRY' + boş (yabancı YOK) → boşları TL say, ileri güvenlik için filtre.
--
-- NOT: SAYI (toplam_ihale) tüm ilanları sayar; TUTAR yalnız SONUÇLANMIŞ+sözleşmeli ihaleleri
-- toplar → "X ihale · Y ₺ sözleşme tutarı" (rakip de böyle: Aktif/Geçmiş/Sözleşme/Tutar ayrı).
--
-- ÖNKOŞUL: idare_hiyerarsi_sayim_mv ile AYNI (ilan_detsis_esle() ile dolu detsis_no + idare_ata_torun).
-- Uygulama: docker exec -i supabase-db psql -U supabase_admin -d postgres < backend/migration_idare_hiyerarsi_bedel.sql
-- =============================================================================

BEGIN;

-- Docker /dev/shm yalnız 64MB → paralel hash join DSM segmenti sığmaz
-- ("could not resize shared memory segment ... No space left on device").
-- Bu ağır build'i (2,72M ⋈ 1,6M ilan + 2,87M DT) tek-thread çalıştır (yavaş ama güvenli).
-- Aynı SET gece REFRESH'te de gerekir (run_scraper.sh).
SET LOCAL max_parallel_workers_per_gather = 0;
SET LOCAL max_parallel_maintenance_workers = 0;

DROP MATERIALIZED VIEW IF EXISTS public.idare_hiyerarsi_bedel_mv;
CREATE MATERIALIZED VIEW public.idare_hiyerarsi_bedel_mv AS
WITH ikn_detsis AS (
  -- ikn → detsis TEKİL eşleme (ilanlar.ikn çok-lot nedeniyle tekrar edebilir → cross-product/şişme önle)
  SELECT DISTINCT ON (ikn) ikn, detsis_no
    FROM public.ilanlar
   WHERE ikn IS NOT NULL AND detsis_no IS NOT NULL
   ORDER BY ikn
),
dugum_ihale_bedel AS (
  -- düğüme DOĞRUDAN bağlı ihale sözleşme tutarı (tüm lotlar toplanır — her lot farklı bedel)
  SELECT id.detsis_no, sum(s.sozlesme_bedeli)::numeric AS bedel
    FROM public.ihale_sonuclari s
    JOIN ikn_detsis id ON id.ikn = s.ikn
   WHERE s.sozlesme_bedeli > 0
     -- FİZİKSEL SANİTE (5 Ağu): bozuk-şişmiş eski sözleşme bedellerini dışla — kazanan teklif
     -- maliyetin 50 katından çok olamaz (2012-2013 parse hatası, ~505 Mr hayalet; bkz. migration_idare_harcama.sql).
     AND NOT (s.yaklasik_maliyet > 0 AND s.sozlesme_bedeli > 50 * s.yaklasik_maliyet)
   GROUP BY id.detsis_no
),
dugum_dt_bedel AS (
  -- düğüme DOĞRUDAN bağlı DT kazanan bedeli (TL; boş para_birimi = TL sayılır)
  SELECT d.detsis_no, sum(ds.kazanan_bedel)::numeric AS bedel
    FROM public.dogrudan_temin_sonuclari ds
    JOIN public.dogrudan_temin_ilanlari d ON d.dt_no = ds.dt_no
   WHERE d.detsis_no IS NOT NULL
     AND ds.kazanan_bedel > 0
     AND (ds.para_birimi IS NULL OR ds.para_birimi IN ('TRY', ''))
   GROUP BY d.detsis_no
),
yuvarlanan AS (
  -- kendisi + TÜM torunlar (idare_ata_torun kapanışı; sayim MV ile BİREBİR aynı mekanizma)
  SELECT at.ata_no,
         COALESCE(sum(dib.bedel), 0)::numeric AS toplam_ihale_bedel,
         COALESCE(sum(ddb.bedel), 0)::numeric AS toplam_dt_bedel
    FROM public.idare_ata_torun at
    LEFT JOIN dugum_ihale_bedel dib ON dib.detsis_no = at.torun_no
    LEFT JOIN dugum_dt_bedel    ddb ON ddb.detsis_no = at.torun_no
   GROUP BY at.ata_no
)
SELECT
  h.detsis_no,
  COALESCE(kib.bedel, 0)::numeric            AS kendi_ihale_bedel,
  COALESCE(kdb.bedel, 0)::numeric            AS kendi_dt_bedel,
  COALESCE(y.toplam_ihale_bedel, 0)::numeric AS toplam_ihale_bedel,
  COALESCE(y.toplam_dt_bedel, 0)::numeric    AS toplam_dt_bedel
FROM public.idare_hiyerarsi h
LEFT JOIN dugum_ihale_bedel kib ON kib.detsis_no = h.detsis_no
LEFT JOIN dugum_dt_bedel    kdb ON kdb.detsis_no = h.detsis_no
LEFT JOIN yuvarlanan        y   ON y.ata_no      = h.detsis_no;

CREATE UNIQUE INDEX idx_idare_hiy_bedel_pk ON public.idare_hiyerarsi_bedel_mv (detsis_no);

-- ANON'A KAPALI (idare adı kimlik verisi; sayim MV ile aynı politika)
REVOKE ALL   ON public.idare_hiyerarsi_bedel_mv FROM PUBLIC, anon;
GRANT SELECT ON public.idare_hiyerarsi_bedel_mv TO authenticated, service_role;
ALTER MATERIALIZED VIEW public.idare_hiyerarsi_bedel_mv OWNER TO postgres;  -- gece -U postgres refresh (sessiz-bayat önle)

-- kurum_kategori_ozet() — bedel kolonları eklenir (RETURNS TABLE değişimi → DROP + CREATE şart)
DROP FUNCTION IF EXISTS public.kurum_kategori_ozet();
CREATE FUNCTION public.kurum_kategori_ozet()
RETURNS TABLE (
  detsis_no text, ad text, grup text,
  toplam_ihale bigint, toplam_dt bigint, cocuk_sayisi bigint,
  toplam_ihale_bedel numeric, toplam_dt_bedel numeric
)
LANGUAGE sql STABLE
AS $$
  -- (1) Kökler — YEREL YÖNETİM KURULUŞLARI hariç (çocuklarıyla düzleştiriliyor)
  SELECT s.detsis_no, s.ad,
         CASE WHEN s.ad = 'Bağlantısız Kurumlar' THEN 'diger' ELSE 'merkezi' END AS grup,
         s.toplam_ihale, s.toplam_dt, s.cocuk_sayisi,
         COALESCE(b.toplam_ihale_bedel, 0)::numeric AS toplam_ihale_bedel,
         COALESCE(b.toplam_dt_bedel, 0)::numeric    AS toplam_dt_bedel
    FROM public.idare_hiyerarsi_sayim_mv s
    LEFT JOIN public.idare_hiyerarsi_bedel_mv b ON b.detsis_no = s.detsis_no
   WHERE s.ust_detsis_no IS NULL
     AND s.detsis_no <> '24350161'
  UNION ALL
  -- (2) YEREL YÖNETİM'in çocuklarını üst kategori olarak aç (BELEDİYELER / İL ÖZEL / BİRLİKLER / MUHTARLIKLAR)
  SELECT s.detsis_no, s.ad, 'yerel'::text AS grup,
         s.toplam_ihale, s.toplam_dt, s.cocuk_sayisi,
         COALESCE(b.toplam_ihale_bedel, 0)::numeric AS toplam_ihale_bedel,
         COALESCE(b.toplam_dt_bedel, 0)::numeric    AS toplam_dt_bedel
    FROM public.idare_hiyerarsi_sayim_mv s
    LEFT JOIN public.idare_hiyerarsi_bedel_mv b ON b.detsis_no = s.detsis_no
   WHERE s.ust_detsis_no = '24350161'
  ORDER BY toplam_ihale DESC, toplam_dt DESC, ad;
$$;

REVOKE EXECUTE ON FUNCTION public.kurum_kategori_ozet() FROM PUBLIC, anon;
GRANT  EXECUTE ON FUNCTION public.kurum_kategori_ozet() TO authenticated, service_role;

COMMIT;

NOTIFY pgrst, 'reload schema';

-- =============================================================================
-- DOĞRULAMA
--   -- Çift-sayım kontrolü: hiçbir düğüm toplam bedeli tüm bedeli aşmamalı
--   SELECT max(toplam_ihale_bedel) FROM idare_hiyerarsi_bedel_mv;
--   SELECT COALESCE(sum(sozlesme_bedeli),0) FROM ihale_sonuclari WHERE sozlesme_bedeli>0;
--   -- Kategori kartı verisi (tutar dolu gelmeli):
--   SELECT ad, toplam_ihale, toplam_ihale_bedel, toplam_dt_bedel FROM kurum_kategori_ozet() LIMIT 25;
-- =============================================================================
