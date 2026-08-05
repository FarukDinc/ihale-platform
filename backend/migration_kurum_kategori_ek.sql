-- =============================================================================
-- migration_kurum_kategori_ek.sql — UV-6: Kurum Merkezi tablosuna AKTİF İHALE +
-- SÖZLEŞME SAYISI (5 Ağu 2026) — rakip ihalepro 4-stat paritesi
-- (Aktif İhale / Arşiv İhale / Sözleşme Sayısı / Toplam Harcama).
-- -----------------------------------------------------------------------------
-- sayim + bedel MV'lerine DOKUNMA (4 ağaç RPC + kurum_kategori_ozet bağlı → yüksek risk).
-- Bedel MV'sindeki AYNI mekanizmayı (kendi = doğrudan detsis; toplam = idare_ata_torun
-- kapanışı rollup) aynalayan paralel MV: idare_hiyerarsi_aktif_mv.
--   * aktif_ihale    : ilanlar.durum='aktif' + son teklif gelecekte (detsis_no'ya göre).
--   * sozlesme_sayisi: ihale_sonuclari sözleşmeli DISTINCT ikn (idare KOLONU YOK → ikn→detsis;
--                      lot şişmesini DISTINCT ikn önler; bedel MV ile aynı ikn_detsis deseni).
-- Yeni kutu /dev/shm=16G → paralellik güvenli (parallel-off SET gerekmez).
-- Uygulama: docker exec -i supabase-db psql -U supabase_admin -d postgres < backend/migration_kurum_kategori_ek.sql
-- REFRESH (gece, run_scraper.sh): REFRESH MATERIALIZED VIEW CONCURRENTLY public.idare_hiyerarsi_aktif_mv;
-- =============================================================================

DROP MATERIALIZED VIEW IF EXISTS public.idare_hiyerarsi_aktif_mv;
CREATE MATERIALIZED VIEW public.idare_hiyerarsi_aktif_mv AS
WITH ikn_detsis AS (
  -- ikn → detsis TEKİL eşleme (ilanlar.ikn çok-lot nedeniyle tekrar eder → şişme önle)
  SELECT DISTINCT ON (ikn) ikn, detsis_no
    FROM public.ilanlar
   WHERE ikn IS NOT NULL AND detsis_no IS NOT NULL
   ORDER BY ikn
),
dugum_aktif AS (
  -- düğüme DOĞRUDAN bağlı AKTİF ihale (durum=aktif + son teklif gelecekte)
  SELECT i.detsis_no, count(*)::bigint AS adet
    FROM public.ilanlar i
   WHERE i.detsis_no IS NOT NULL
     AND i.durum = 'aktif'
     AND (i.son_teklif_tarihi IS NULL OR i.son_teklif_tarihi >= now())
   GROUP BY i.detsis_no
),
dugum_sozlesme AS (
  -- düğüme bağlı SÖZLEŞME sayısı = sözleşmeli DISTINCT ikn (lot şişmesi önlenir)
  SELECT id.detsis_no, count(DISTINCT s.ikn)::bigint AS adet
    FROM public.ihale_sonuclari s
    JOIN ikn_detsis id ON id.ikn = s.ikn
   WHERE s.sozlesme_bedeli > 0
   GROUP BY id.detsis_no
),
yuvarlanan AS (
  -- kendisi + TÜM torunlar (idare_ata_torun kapanışı; sayim/bedel MV ile BİREBİR aynı mekanizma)
  SELECT at.ata_no,
         COALESCE(sum(da.adet), 0)::bigint AS toplam_aktif,
         COALESCE(sum(ds.adet), 0)::bigint AS toplam_sozlesme
    FROM public.idare_ata_torun at
    LEFT JOIN dugum_aktif    da ON da.detsis_no = at.torun_no
    LEFT JOIN dugum_sozlesme ds ON ds.detsis_no = at.torun_no
   GROUP BY at.ata_no
)
SELECT
  h.detsis_no,
  COALESCE(y.toplam_aktif, 0)::bigint    AS aktif_ihale,
  COALESCE(y.toplam_sozlesme, 0)::bigint AS sozlesme_sayisi
FROM public.idare_hiyerarsi h
LEFT JOIN yuvarlanan y ON y.ata_no = h.detsis_no;

CREATE UNIQUE INDEX idx_idare_hiy_aktif_pk ON public.idare_hiyerarsi_aktif_mv (detsis_no);
REVOKE ALL   ON public.idare_hiyerarsi_aktif_mv FROM PUBLIC, anon;
GRANT SELECT ON public.idare_hiyerarsi_aktif_mv TO authenticated, service_role;
-- KRİTİK: gece REFRESH `-U postgres` ile koşuyor; postgres superuser DEĞİL → sahip
-- postgres OLMALI (yoksa "permission denied" ile SESSİZCE bayatlar). sayim/bedel MV ile aynı.
ALTER MATERIALIZED VIEW public.idare_hiyerarsi_aktif_mv OWNER TO postgres;

-- kurum_kategori_ozet() — aktif_ihale + sozlesme_sayisi eklenir (RETURNS TABLE değişimi → DROP+CREATE)
DROP FUNCTION IF EXISTS public.kurum_kategori_ozet();
CREATE FUNCTION public.kurum_kategori_ozet()
RETURNS TABLE (
  detsis_no text, ad text, grup text,
  toplam_ihale bigint, toplam_dt bigint, cocuk_sayisi bigint,
  toplam_ihale_bedel numeric, toplam_dt_bedel numeric,
  aktif_ihale bigint, sozlesme_sayisi bigint
)
LANGUAGE sql STABLE
AS $$
  -- (1) Kökler — YEREL YÖNETİM KURULUŞLARI hariç (çocuklarıyla düzleştiriliyor)
  SELECT s.detsis_no, s.ad,
         CASE WHEN s.ad = 'Bağlantısız Kurumlar' THEN 'diger' ELSE 'merkezi' END AS grup,
         s.toplam_ihale, s.toplam_dt, s.cocuk_sayisi,
         COALESCE(b.toplam_ihale_bedel, 0)::numeric,
         COALESCE(b.toplam_dt_bedel, 0)::numeric,
         COALESCE(a.aktif_ihale, 0)::bigint,
         COALESCE(a.sozlesme_sayisi, 0)::bigint
    FROM public.idare_hiyerarsi_sayim_mv s
    LEFT JOIN public.idare_hiyerarsi_bedel_mv b ON b.detsis_no = s.detsis_no
    LEFT JOIN public.idare_hiyerarsi_aktif_mv a ON a.detsis_no = s.detsis_no
   WHERE s.ust_detsis_no IS NULL
     AND s.detsis_no <> '24350161'
  UNION ALL
  -- (2) YEREL YÖNETİM'in çocuklarını üst kategori olarak aç
  SELECT s.detsis_no, s.ad, 'yerel'::text,
         s.toplam_ihale, s.toplam_dt, s.cocuk_sayisi,
         COALESCE(b.toplam_ihale_bedel, 0)::numeric,
         COALESCE(b.toplam_dt_bedel, 0)::numeric,
         COALESCE(a.aktif_ihale, 0)::bigint,
         COALESCE(a.sozlesme_sayisi, 0)::bigint
    FROM public.idare_hiyerarsi_sayim_mv s
    LEFT JOIN public.idare_hiyerarsi_bedel_mv b ON b.detsis_no = s.detsis_no
    LEFT JOIN public.idare_hiyerarsi_aktif_mv a ON a.detsis_no = s.detsis_no
   WHERE s.ust_detsis_no = '24350161'
  ORDER BY toplam_ihale DESC, toplam_dt DESC, ad;
$$;
REVOKE EXECUTE ON FUNCTION public.kurum_kategori_ozet() FROM PUBLIC, anon;
GRANT  EXECUTE ON FUNCTION public.kurum_kategori_ozet() TO authenticated, service_role;

NOTIFY pgrst, 'reload schema';
