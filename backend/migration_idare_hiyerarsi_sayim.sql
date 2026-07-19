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
)
SELECT
  h.detsis_no,
  h.ad,
  h.idare_id,
  h.ust_detsis_no,
  h.seviye,
  -- ki/kd aşağıda LEFT JOIN ile bağlanıyor. İlk sürümde bu JOIN'ler YOKTU ve
  -- "missing FROM-clause entry for table ki" ile tüm migration geri alındı.
  COALESCE(ki.adet, 0)                                   AS kendi_ihale,
  COALESCE(kd.adet, 0)                                   AS kendi_dt,
  COALESCE((SELECT sum(x.adet) FROM public.idare_ata_torun at
              JOIN dugum_ihale x ON x.detsis_no = at.torun_no
             WHERE at.ata_no = h.detsis_no), 0)::bigint  AS toplam_ihale,
  COALESCE((SELECT sum(x.adet) FROM public.idare_ata_torun at
              JOIN dugum_dt x ON x.detsis_no = at.torun_no
             WHERE at.ata_no = h.detsis_no), 0)::bigint  AS toplam_dt,
  (SELECT count(*) FROM public.idare_hiyerarsi c WHERE c.ust_detsis_no = h.detsis_no) AS cocuk_sayisi
FROM public.idare_hiyerarsi h
LEFT JOIN dugum_ihale ki ON ki.detsis_no = h.detsis_no
LEFT JOIN dugum_dt    kd ON kd.detsis_no = h.detsis_no;

CREATE UNIQUE INDEX idx_idare_hiy_sayim_pk  ON public.idare_hiyerarsi_sayim_mv (detsis_no);
CREATE INDEX        idx_idare_hiy_sayim_ust ON public.idare_hiyerarsi_sayim_mv (ust_detsis_no);
CREATE INDEX        idx_idare_hiy_sayim_top ON public.idare_hiyerarsi_sayim_mv (toplam_ihale DESC);

REVOKE ALL  ON public.idare_hiyerarsi_sayim_mv FROM anon;
GRANT SELECT ON public.idare_hiyerarsi_sayim_mv TO authenticated, service_role;

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
