-- =============================================================================
-- migration_idare_hiyerarsi.sql — İdare ağacı + kapanış tablosu + yuvarlama sayaçları
-- =============================================================================
--
-- AMAÇ: "Ankara İl Emniyet Md. → Emniyet Genel Md. → İçişleri Bakanlığı" zinciri
-- boyunca ihale/DT sayılarının yukarı toplanması. Kullanıcının örneği:
--   EGM'de kendi birimlerinden 2000 + il müdürlüklerinden 1800 = 3800,
--   bu 3800 İçişleri Bakanlığı'na da eklenir, o da yukarı dallanır.
--
-- VERİ KAYNAĞI: EKAP DETSİS ağacı (POST /b_idare/api/DetsisKurumBirim/DetsisAgaci)
-- backend/veri/detsis_agaci.json — 87.528 kayıt. backend/idare_hiyerarsi_yukle.py
-- ile bu tabloya basılır. EKAP'a YENİ İSTEK GEREKMEZ, dosya zaten indirilmiş.
--
-- AĞACIN DOĞRULANMIŞ ÖZELLİKLERİ (yerel analiz, 19 Tem):
--   87.528 benzersiz detsis_no · MÜKERRER YOK · DÖNGÜ YOK
--   parent bağlantısı 87.455/87.528 çözülüyor (%99,9); 30 kök, 43 kopuk
--   derinlik 0-7 · 6.419 iç düğüm · 81.109 yaprak
--   Örnek doğrulama: EMNİYET GENEL MÜDÜRLÜĞÜ alt ağacı = 1.090 düğüm,
--   içinde tam 81 "İl Emniyet Müdürlüğü" (81 il — birebir tutuyor)
--
-- =============================================================================
-- !! ANON ERİŞİMİ: BU NESNELERİN HEPSİ MİSAFİRE KAPALI !!
-- İdare adı bu projede kimlik verisi sayılıyor ve ilanlar/idare_ozet_mv'de
-- anon'a kapalı (migration_anon_maske.sql). Hiyerarşi + sayaçlar aynı verinin
-- daha güçlü bir sunumu — açık bırakmak maskelemeyi anlamsız kılar.
-- REVOKE'lar AÇIKÇA yazıldı: "GRANT yazmamak" YETMİYOR, çünkü self-hosted
-- Supabase'de ALTER DEFAULT PRIVILEGES yeni tabloları doğuştan anon'a açıyor
-- (18 Tem'de tam bu yüzden 3 nesnede delik açıldı — bkz. migration_dt_anon_fix.sql).
-- =============================================================================

BEGIN;

-- ---------------------------------------------------------------------------
-- 1) Ağacın kendisi
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.idare_hiyerarsi (
  detsis_no      text PRIMARY KEY,
  idare_id       integer,            -- EKAP idareKodList anahtarı (ihale filtresi bununla)
  ad             text NOT NULL,
  ust_detsis_no  text,               -- NULL = kök
  seviye         smallint NOT NULL DEFAULT 0,   -- HESAPLANAN derinlik (DETSİS'in kendi
                                                 -- 'seviye' alanında 23.000 NULL var, güvenilmez)
  guncelleme     timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_idare_hiy_ust     ON public.idare_hiyerarsi (ust_detsis_no);
CREATE INDEX IF NOT EXISTS idx_idare_hiy_idareid ON public.idare_hiyerarsi (idare_id);
CREATE INDEX IF NOT EXISTS idx_idare_hiy_seviye  ON public.idare_hiyerarsi (seviye);

-- ---------------------------------------------------------------------------
-- 2) KAPANIŞ TABLOSU — işin kalbi
--
-- "Bu kurum ve altındaki her şey" sorgusu, çalışma anında recursive CTE ile
-- yapılırsa 356K ihale / 1,49M DT üzerinde her seferinde ağaç yürür ve
-- statement timeout eder (bu projede aynı sınıftan 3 hata yaşandı — bkz.
-- hafıza statement-timeout-edge). Bunun yerine ata-torun çiftleri BİR KEZ
-- üretilir, sorgular düz JOIN'e döner.
--
-- mesafe = 0 satırı düğümün KENDİSİDİR — "kendi + altı" tek sorguda çıkar.
-- Boyut: Σ(derinlik+1) ≈ 330K satır (87K düğüm, ortalama derinlik ~2,7).
-- ---------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.idare_ata_torun (
  ata_no    text NOT NULL,
  torun_no  text NOT NULL,
  mesafe    smallint NOT NULL,        -- 0 = kendisi, 1 = doğrudan çocuk, ...
  PRIMARY KEY (ata_no, torun_no)
);

CREATE INDEX IF NOT EXISTS idx_ata_torun_torun ON public.idare_ata_torun (torun_no);

-- ---------------------------------------------------------------------------
-- 3) Kapanış tablosunu ağaçtan üreten fonksiyon
--    idare_hiyerarsi yüklendikten SONRA çağrılır; gece tazelemede de.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION public.idare_kapanis_uret()
RETURNS integer
LANGUAGE plpgsql
AS $$
DECLARE
  n integer;
BEGIN
  TRUNCATE public.idare_ata_torun;

  -- Döngüye karşı koruma: UNION (DISTINCT değil ALL) + mesafe tavanı.
  -- Ağaçta döngü YOK (yerel analizde doğrulandı) ama veri tazelendiğinde
  -- bozuk bir parent gelirse sonsuz döngüye girmeyelim.
  INSERT INTO public.idare_ata_torun (ata_no, torun_no, mesafe)
  WITH RECURSIVE yol AS (
    SELECT detsis_no AS ata_no, detsis_no AS torun_no, 0 AS mesafe
      FROM public.idare_hiyerarsi
    UNION ALL
    SELECT y.ata_no, h.detsis_no, y.mesafe + 1
      FROM yol y
      JOIN public.idare_hiyerarsi h ON h.ust_detsis_no = y.torun_no
     WHERE y.mesafe < 12
  )
  SELECT ata_no, torun_no, MIN(mesafe)
    FROM yol
   GROUP BY ata_no, torun_no;

  GET DIAGNOSTICS n = ROW_COUNT;
  ANALYZE public.idare_ata_torun;
  RETURN n;
END;
$$;

-- ---------------------------------------------------------------------------
-- 4) Yuvarlama sayaçları (MV)
--
-- İKİ AYRI SAYI tutuluyor — kullanıcının örneği bunu gerektiriyor:
--   kendi_*  : yalnız bu düğüme doğrudan bağlı ihaleler
--   toplam_* : kendisi + TÜM torunları
-- Tek sayıya indirilirse kullanıcı 3800'ün nereden geldiğini göremez.
--
-- ilanlar.idare (metin) → idare_tur.idare_norm → idare_tur.detsis_no zinciriyle
-- bağlanıyor. Ad ile DOĞRUDAN join YAPILMIYOR: "BİLGİ İŞLEM DAİRE BAŞKANLIĞI"
-- adında 114 DETSİS kaydı var, ad-join sessizce yanlış ağaç üretir.
--
-- MV BU DOSYADA DEĞİL → backend/migration_idare_hiyerarsi_sayim.sql
-- Sebep: MV, idare_tur + idare_normalize()'a bağımlı. İlk sürümde hepsi tek
-- dosyada ve tek transaction'daydı; MV'deki bir yazım hatası AĞAÇ TABLOLARINI
-- DA geri aldı (canlıda yaşandı). Ayrılınca ağaç her hâlükârda kuruluyor.
-- ---------------------------------------------------------------------------

-- ---------------------------------------------------------------------------
-- 5) YETKİLER — hepsi anon'a KAPALI (yukarıdaki uyarıya bakın)
--    MV'nin yetkileri kendi dosyasında.
-- ---------------------------------------------------------------------------
REVOKE ALL ON public.idare_hiyerarsi FROM anon;
REVOKE ALL ON public.idare_ata_torun FROM anon;

GRANT SELECT ON public.idare_hiyerarsi TO authenticated, service_role;
GRANT SELECT ON public.idare_ata_torun TO authenticated, service_role;
GRANT INSERT, UPDATE, DELETE ON public.idare_hiyerarsi TO service_role;

REVOKE EXECUTE ON FUNCTION public.idare_kapanis_uret() FROM PUBLIC, anon;
GRANT  EXECUTE ON FUNCTION public.idare_kapanis_uret() TO service_role;

COMMIT;

NOTIFY pgrst, 'reload schema';

-- =============================================================================
-- KURULUM SIRASI
-- =============================================================================
--   1) Bu dosyayı uygula
--   2) Ağacı yükle:      python backend/idare_hiyerarsi_yukle.py
--   3) Kapanışı üret:    SELECT public.idare_kapanis_uret();
--   4) Sayaç MV'si:      migration_idare_hiyerarsi_sayim.sql  (idare_tur GEREKİR)
--   5) Sayaçları tazele: REFRESH MATERIALIZED VIEW public.idare_hiyerarsi_sayim_mv;
--   5) run_scraper.sh'in gece REFRESH zincirine (3) ve (4) eklenmeli
--
-- DOĞRULAMA — kullanıcının verdiği senaryo
-- =============================================================================
--   SELECT ad, seviye, kendi_ihale, toplam_ihale, cocuk_sayisi
--     FROM idare_hiyerarsi_sayim_mv
--    WHERE ad ILIKE '%EMNİYET GENEL%';
--   -- toplam_ihale > kendi_ihale OLMALI (81 il müdürlüğü + 1.090 alt düğüm)
--
--   -- Zincir yukarı doğru büyümeli: il md. < genel md. < bakanlık
--   SELECT h.ad, s.toplam_ihale
--     FROM idare_ata_torun at
--     JOIN idare_hiyerarsi h ON h.detsis_no = at.ata_no
--     JOIN idare_hiyerarsi_sayim_mv s ON s.detsis_no = at.ata_no
--    WHERE at.torun_no = (SELECT detsis_no FROM idare_hiyerarsi
--                          WHERE ad ILIKE 'ADANA İL EMNİYET%' LIMIT 1)
--    ORDER BY at.mesafe;
--
--   -- Kapanış tablosu boyutu (~330K bekleniyor)
--   SELECT count(*) FROM idare_ata_torun;
--
--   -- ÇİFT SAYIM KONTROLÜ: bir kökün toplamı, tüm ihalelerin sayısını AŞMAMALI
--   SELECT max(toplam_ihale) AS en_buyuk_dugum,
--          (SELECT count(*) FROM ilanlar) AS tum_ihaleler
--     FROM idare_hiyerarsi_sayim_mv;
