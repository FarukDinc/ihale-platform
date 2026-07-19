-- =============================================================================
-- migration_idare_agac_rpc.sql — Ağaç gezinme RPC'leri + ihale/DT bağlantısı
-- =============================================================================
--
-- ÖNKOŞUL: migration_idare_hiyerarsi.sql + idare_hiyerarsi_yukle.py --kapanis
--          + migration_idare_hiyerarsi_sayim.sql
--
-- NEDEN RPC, NEDEN DÜZ TABLO SORGUSU DEĞİL
-- ────────────────────────────────────────
-- Ağacı istemciye komple indirmek 87.528 düğüm demek (~8 MB). Bu projede aynı
-- hata bir kez yapıldı: idare_dizin_json() tek istekte 2 MB döküyordu ve
-- migration_bulk_rpc_kilit.sql ile kilitlendi (bkz. hafıza client-load-all-bug).
-- Ağaç TEMBEL açılır: kullanıcı bir dala tıkladıkça yalnız o dalın çocukları gelir.
--
-- HEPSİ ANON'A KAPALI: idare adı bu projede kimlik verisi. Fonksiyonlar
-- PUBLIC EXECUTE ile doğduğu için REVOKE AÇIKÇA yazıldı (18 Tem'de bu atlandı
-- ve 3 nesnede delik açıldı — bkz. migration_dt_anon_fix.sql).
-- =============================================================================

BEGIN;

-- ---------------------------------------------------------------------------
-- 1) idare_agac_dallar(ust) — bir düğümün çocukları (ust NULL ise kökler)
--    Tembel ağaç açılımının motoru. Sayılar MV'den geldiği için hızlı.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION public.idare_agac_dallar(p_ust text DEFAULT NULL)
RETURNS TABLE (
  detsis_no text, ad text, idare_id integer, seviye smallint,
  kendi_ihale bigint, toplam_ihale bigint,
  kendi_dt bigint, toplam_dt bigint,
  cocuk_sayisi bigint
)
LANGUAGE sql STABLE
AS $$
  SELECT s.detsis_no, s.ad, s.idare_id, s.seviye,
         s.kendi_ihale, s.toplam_ihale, s.kendi_dt, s.toplam_dt, s.cocuk_sayisi
    FROM public.idare_hiyerarsi_sayim_mv s
   WHERE (p_ust IS NULL AND s.ust_detsis_no IS NULL)
      OR (p_ust IS NOT NULL AND s.ust_detsis_no = p_ust)
   -- İçi boş dallar dibe: kullanıcı önce iş olan kurumları görsün
   ORDER BY s.toplam_ihale DESC, s.toplam_dt DESC, s.ad
   LIMIT 500;
$$;

-- ---------------------------------------------------------------------------
-- 2) idare_agac_yol(detsis) — kırıntı yolu (kökten düğüme)
--    Kapanış tablosu sayesinde tek JOIN; recursive CTE gerekmiyor.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION public.idare_agac_yol(p_detsis text)
RETURNS TABLE (detsis_no text, ad text, seviye smallint, mesafe smallint)
LANGUAGE sql STABLE
AS $$
  SELECT h.detsis_no, h.ad, h.seviye, at.mesafe
    FROM public.idare_ata_torun at
    JOIN public.idare_hiyerarsi h ON h.detsis_no = at.ata_no
   WHERE at.torun_no = p_detsis
   ORDER BY at.mesafe DESC;     -- kök önce, düğümün kendisi (mesafe 0) sonda
$$;

-- ---------------------------------------------------------------------------
-- 3) idare_agac_ara(q) — ağaçta ada göre arama
--    Kullanıcı "emniyet" yazınca ağacı elle gezmek zorunda kalmasın.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION public.idare_agac_ara(p_q text, p_limit integer DEFAULT 50)
RETURNS TABLE (
  detsis_no text, ad text, seviye smallint,
  toplam_ihale bigint, toplam_dt bigint, cocuk_sayisi bigint,
  ust_ad text
)
LANGUAGE sql STABLE
AS $$
  SELECT s.detsis_no, s.ad, s.seviye, s.toplam_ihale, s.toplam_dt, s.cocuk_sayisi,
         u.ad AS ust_ad
    FROM public.idare_hiyerarsi_sayim_mv s
    LEFT JOIN public.idare_hiyerarsi u ON u.detsis_no = s.ust_detsis_no
   WHERE p_q IS NOT NULL AND length(btrim(p_q)) >= 2
     -- tr_fold: Türkçe İ/ı ikilisi ilike'ta sessizce 0 döndürüyor (bu projede
     -- iki kez yaşandı, bkz. hafıza ilike-tr-locale-tuzagi)
     AND public.tr_fold(s.ad) LIKE '%' || public.tr_fold(btrim(p_q)) || '%'
   ORDER BY s.toplam_ihale DESC, s.ad
   LIMIT LEAST(COALESCE(p_limit, 50), 200);
$$;

-- ---------------------------------------------------------------------------
-- 4) idare_alt_agac_detsis(detsis) — bir dalın altındaki TÜM düğüm no'ları
--
--    İhale/DT aramasının hiyerarşiye bağlanma noktası. İstemci bu listeyi alıp
--    ilanlar.detsis_no üzerinde `in.(...)` filtresi kurar.
--    Ad DEĞİL no döndürüyor: adlar uzun (ort. 60 karakter), 1.090 düğümlük bir
--    dalda URL 65 KB'a çıkardı ve nginx/PostgREST sınırını aşardı. detsis_no
--    ~8 karakter → aynı dal ~10 KB.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION public.idare_alt_agac_detsis(p_detsis text)
RETURNS TABLE (detsis_no text)
LANGUAGE sql STABLE
AS $$
  SELECT at.torun_no
    FROM public.idare_ata_torun at
   WHERE at.ata_no = p_detsis
   LIMIT 5000;      -- en büyük dal bile bunun altında (EGM 1.090)
$$;

-- ---------------------------------------------------------------------------
-- 5) YETKİLER — hepsi giriş şartlı
-- ---------------------------------------------------------------------------
REVOKE EXECUTE ON FUNCTION public.idare_agac_dallar(text)        FROM PUBLIC, anon;
REVOKE EXECUTE ON FUNCTION public.idare_agac_yol(text)           FROM PUBLIC, anon;
REVOKE EXECUTE ON FUNCTION public.idare_agac_ara(text, integer)  FROM PUBLIC, anon;
REVOKE EXECUTE ON FUNCTION public.idare_alt_agac_detsis(text)    FROM PUBLIC, anon;

GRANT EXECUTE ON FUNCTION public.idare_agac_dallar(text)       TO authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.idare_agac_yol(text)          TO authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.idare_agac_ara(text, integer) TO authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.idare_alt_agac_detsis(text)   TO authenticated, service_role;

COMMIT;

-- =============================================================================
-- 6) İHALE/DT TARAFI — detsis_no kolonu
--
-- !! DİKKAT — BU DOSYAYI AĞIR BİR UPDATE KOŞARKEN TEKRAR ÇALIŞTIRMAYIN !!
-- 19 Tem'de yaşandı: ilan_detsis_esle() çalışırken bu dosya iki kez daha
-- başlatıldı (önceki denemeler Ctrl+C ile kesilmişti ama sunucu tarafındaki
-- sorgular ölmemişti). ALTER TABLE — IF NOT EXISTS olsa ve hiçbir iş yapmasa
-- bile — ACCESS EXCLUSIVE kilidi ister. Kilit sıraya girince PostgreSQL
-- ARKASINA GELEN HER SORGUYU da sıraya alır: düz bir SELECT bile. Yani canlı
-- sitenin ilanlar okumaları tıkandı. Çözüm pg_cancel_backend ile bekleyen
-- ALTER'ları iptal etmek oldu.
--
-- DERS: şema değişikliği (ALTER/CREATE INDEX) ile veri doldurma (UPDATE) aynı
-- dosyada durmamalı. Bu dosya şemayı kurar; doldurmayı ilan_detsis_esle() ayrı
-- ve ELLE çağrılarak yapar.
--
-- AYRI TRANSACTION: index CONCURRENTLY kurulacak, transaction içinde çalışmaz.
-- Bu kolon olmadan "bu kurumun altındaki tüm ihaleler" araması yapılamaz;
-- her seferinde idare metnini normalize edip idare_tur'a join etmek 356K/1,49M
-- satırda tam tarama demek.
-- =============================================================================
ALTER TABLE public.ilanlar                   ADD COLUMN IF NOT EXISTS detsis_no text;
ALTER TABLE public.dogrudan_temin_ilanlari   ADD COLUMN IF NOT EXISTS detsis_no text;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_ilanlar_detsis
  ON public.ilanlar (detsis_no) WHERE detsis_no IS NOT NULL;
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_dt_ilanlari_detsis
  ON public.dogrudan_temin_ilanlari (detsis_no) WHERE detsis_no IS NOT NULL;

-- detsis_no anon'a KAPALI: hangi ihalenin hangi kuruma ait olduğunu ifşa eder,
-- yani maskelenmiş `idare` kolonunun dolaylı karşılığıdır. Kolon-GRANT listesine
-- EKLENMİYOR — maskeli tabloya sonradan eklenen kolon otomatik kapalı gelir
-- (bkz. migration_dt_anon_fix.sql'deki varsayılan-ayrıcalık notu).

NOTIFY pgrst, 'reload schema';

-- =============================================================================
-- 7) detsis_no'yu dolduran fonksiyon (gece tazelemede çağrılır)
-- =============================================================================
CREATE OR REPLACE FUNCTION public.ilan_detsis_esle()
RETURNS TABLE (ihale_guncellenen bigint, dt_guncellenen bigint)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
DECLARE
  a bigint; b bigint;
BEGIN
  UPDATE public.ilanlar i
     SET detsis_no = t.detsis_no
    FROM public.idare_tur t
   WHERE t.idare_norm = public.idare_normalize(i.idare)
     AND t.detsis_no IS NOT NULL
     AND i.detsis_no IS DISTINCT FROM t.detsis_no;
  GET DIAGNOSTICS a = ROW_COUNT;

  UPDATE public.dogrudan_temin_ilanlari d
     SET detsis_no = t.detsis_no
    FROM public.idare_tur t
   WHERE t.idare_norm = public.idare_normalize(d.idare)
     AND t.detsis_no IS NOT NULL
     AND d.detsis_no IS DISTINCT FROM t.detsis_no;
  GET DIAGNOSTICS b = ROW_COUNT;

  RETURN QUERY SELECT a, b;
END;
$$;

REVOKE EXECUTE ON FUNCTION public.ilan_detsis_esle() FROM PUBLIC, anon, authenticated;
GRANT  EXECUTE ON FUNCTION public.ilan_detsis_esle() TO service_role;

NOTIFY pgrst, 'reload schema';

-- =============================================================================
-- KURULUM SONRASI
-- =============================================================================
--   SELECT * FROM public.ilan_detsis_esle();        -- ilk eşleme (uzun sürer)
--   -- Kapsama:
--   SELECT count(*) FILTER (WHERE detsis_no IS NOT NULL) AS eslesen,
--          count(*) AS toplam FROM public.ilanlar;
--
--   -- Ağaç gezinme denemesi (kökler):
--   SELECT ad, toplam_ihale, cocuk_sayisi FROM public.idare_agac_dallar(NULL);
--
--   -- Kullanıcının örneği:
--   SELECT * FROM public.idare_agac_ara('emniyet genel', 5);
--
--   run_scraper.sh gece zincirine eklenmeli:
--     SELECT public.idare_kapanis_uret();
--     SELECT * FROM public.ilan_detsis_esle();
--     REFRESH MATERIALIZED VIEW public.idare_hiyerarsi_sayim_mv;
