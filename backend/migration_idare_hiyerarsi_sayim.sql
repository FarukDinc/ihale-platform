-- =============================================================================
-- migration_idare_hiyerarsi_sayim.sql — hiyerarşi yuvarlama sayaçları (MV)
-- =============================================================================
--
-- migration_idare_hiyerarsi.sql'den AYRI bir dosya, bilinçli olarak:
-- bu MV `idare_tur` tablosuna ve `idare_normalize(text)` fonksiyonuna bağımlı
-- (ikisi de migration_idare_tur.sql'den gelir). İlk sürümde hepsi tek dosyada
-- ve tek transaction'daydı; MV'deki bir hata AĞAÇ TABLOLARINI DA geri aldı.
-- Ayırınca ağaç + kapanış tablosu her hâlükârda kuruluyor, sayaçlar hazır
-- olduğunda ekleniyor.
--
-- ÖNKOŞUL:
--   1) migration_idare_tur.sql       uygulanmış olmalı
--   2) migration_idare_hiyerarsi.sql uygulanmış olmalı
--   3) python backend/idare_hiyerarsi_yukle.py --kapanis  çalışmış olmalı
--
-- Uygulama:
--   docker exec -i supabase-db psql -U postgres -d postgres < backend/migration_idare_hiyerarsi_sayim.sql
--
-- İKİ AYRI SAYI:
--   kendi_*  : yalnız bu düğüme doğrudan bağlı ihaleler
--   toplam_* : kendisi + TÜM torunları (kapanış tablosu üzerinden)
-- Tek sayıya indirilirse kullanıcı toplamın nereden geldiğini göremez.
--
-- ANON'A KAPALI: idare adı bu projede kimlik verisi (bkz. migration_anon_maske.sql).
-- =============================================================================

-- PERFORMANS NOTU: dugum_ihale/dugum_dt CTE'leri idare_normalize()'i SATIR BAŞINA
-- çağırıyor (356K ilan + 1,49M DT). İfade indeksi yoksa tam tarama olur ama tek
-- seferlik; asıl darboğaz ilişkili alt sorgulardı, o kaldırıldı. MV gece bir kez
-- REFRESH ediliyor, çalışma anında bu maliyet kullanıcıya yansımıyor.

BEGIN;

DROP MATERIALIZED VIEW IF EXISTS public.idare_hiyerarsi_sayim_mv;
CREATE MATERIALIZED VIEW public.idare_hiyerarsi_sayim_mv AS
WITH dugum_ihale AS (
  SELECT t.detsis_no, count(*)::bigint AS adet
    FROM public.ilanlar i
    JOIN public.idare_tur t ON t.idare_norm = public.idare_normalize(i.idare)
   WHERE t.detsis_no IS NOT NULL
   GROUP BY t.detsis_no
),
dugum_dt AS (
  SELECT t.detsis_no, count(*)::bigint AS adet
    FROM public.dogrudan_temin_ilanlari d
    JOIN public.idare_tur t ON t.idare_norm = public.idare_normalize(d.idare)
   WHERE t.detsis_no IS NOT NULL
   GROUP BY t.detsis_no
),
-- YUVARLAMA — TEK GEÇİŞ.
-- İlk sürümde bu, satır başına İLİŞKİLİ ALT SORGU olarak yazılmıştı:
--   COALESCE((SELECT sum(...) FROM idare_ata_torun WHERE ata_no = h.detsis_no), 0)
-- Yani 87.528 düğümün HER BİRİ için 312.259 satırlık kapanış tablosuna ayrı bir
-- sorgu. Canlıda MV yaratma komutu asıldı (kullanıcı Ctrl+C ile durdurdu).
-- Doğrusu: kapanış tablosunu bir kez tarayıp ata_no'ya göre grupla, sonra JOIN et.
yuvarlanan AS (
  SELECT at.ata_no,
         COALESCE(sum(di.adet), 0)::bigint AS toplam_ihale,
         COALESCE(sum(dd.adet), 0)::bigint AS toplam_dt
    FROM public.idare_ata_torun at
    LEFT JOIN dugum_ihale di ON di.detsis_no = at.torun_no
    LEFT JOIN dugum_dt    dd ON dd.detsis_no = at.torun_no
   GROUP BY at.ata_no
),
-- cocuk_sayisi da ilişkili alt sorguydu (87.528 kez tam tarama) → grupla+JOIN
cocuklar AS (
  SELECT ust_detsis_no AS ata_no, count(*)::bigint AS adet
    FROM public.idare_hiyerarsi
   WHERE ust_detsis_no IS NOT NULL
   GROUP BY ust_detsis_no
)
SELECT
  h.detsis_no,
  h.ad,
  h.idare_id,
  h.ust_detsis_no,
  h.seviye,
  COALESCE(ki.adet, 0)::bigint        AS kendi_ihale,
  COALESCE(kd.adet, 0)::bigint        AS kendi_dt,
  COALESCE(y.toplam_ihale, 0)::bigint AS toplam_ihale,
  COALESCE(y.toplam_dt, 0)::bigint    AS toplam_dt,
  COALESCE(c.adet, 0)::bigint         AS cocuk_sayisi
FROM public.idare_hiyerarsi h
LEFT JOIN dugum_ihale ki ON ki.detsis_no = h.detsis_no
LEFT JOIN dugum_dt    kd ON kd.detsis_no = h.detsis_no
LEFT JOIN yuvarlanan  y  ON y.ata_no     = h.detsis_no
LEFT JOIN cocuklar    c  ON c.ata_no     = h.detsis_no;

CREATE UNIQUE INDEX idx_idare_hiy_sayim_pk  ON public.idare_hiyerarsi_sayim_mv (detsis_no);
CREATE INDEX        idx_idare_hiy_sayim_ust ON public.idare_hiyerarsi_sayim_mv (ust_detsis_no);
CREATE INDEX        idx_idare_hiy_sayim_top ON public.idare_hiyerarsi_sayim_mv (toplam_ihale DESC);

REVOKE ALL   ON public.idare_hiyerarsi_sayim_mv FROM anon;
GRANT SELECT ON public.idare_hiyerarsi_sayim_mv TO authenticated, service_role;

COMMIT;

NOTIFY pgrst, 'reload schema';

-- =============================================================================
-- DOĞRULAMA
-- =============================================================================
--   SELECT ad, seviye, kendi_ihale, toplam_ihale, cocuk_sayisi
--     FROM idare_hiyerarsi_sayim_mv WHERE ad ILIKE '%EMNİYET GENEL%';
--   -- toplam_ihale > kendi_ihale OLMALI
--
--   -- ÇİFT SAYIM KONTROLÜ: hiçbir düğüm tüm ihale sayısını aşmamalı
--   SELECT max(toplam_ihale) AS en_buyuk, (SELECT count(*) FROM ilanlar) AS tum
--     FROM idare_hiyerarsi_sayim_mv;
