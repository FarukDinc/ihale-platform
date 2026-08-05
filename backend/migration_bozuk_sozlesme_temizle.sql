-- ============================================================================
-- migration_bozuk_sozlesme_temizle.sql — KÖK TEMİZLİK: bozuk sözleşme bedeli (5 Ağu 2026)
--
-- BULGU (kullanıcı Hakkari anomalisiyle yakaladı → tam teşhis): bu bir PARSE/ondalık
-- ayraç hatası DEĞİL. `bedel_parse` doğru çalışıyor ("78.203.085,00 TRY" → 78203085).
-- İki AYRI kusur `sum(sozlesme_bedeli)` yapan harcama MV'lerini zehirliyor:
--
--   A) ÇERÇEVE ANLAŞMA / çok-kısımlı total-kopyalama (~500 Mr, baskın):
--      EKAP her firmanın SÖZLEŞME TOPLAMINI kazandığı HER kısma tekrar yazıyor
--      (yaklaşık maliyet ise kısım-bazlı, küçük). Lotlar toplandığında toplam N katına
--      çıkıyor. Örn 2013/116533 (773 kalem çerçeve): ham sum 312,7 Mr; (ikn,firma,bedel)
--      tekilleştirince ~9,25 Mr (gerçek mertebe). Değer her lotta AYNI → tekilleştir.
--
--   B) Tek-lot ~1000× şişme (~88 ihale, ~16 Mr): teklif kolonları (kazanan/en_düşük/
--      en_yüksek) kendi içinde tutarlı ama yaklaşık maliyetin ~1000 katı. ÷1000 yapılınca
--      kazanan teklif maliyetin %9 altına oturuyor (ders kitabı). Ham kaynak dizesi
--      (tum_teklifler) BOŞ → gerçek değer kurtarılamaz → değerleri DIŞLA (NULL'la).
--
-- YANLIŞ POZİTİF (temizlenMEZ): tek-lot + yaklaşık maliyet=1 (placeholder) ama sözleşme
-- meşru büyük (~5,6 Mr). Eski >50× filtresi bunları YANLIŞLIKLA dışlıyordu → artık dahil.
--
-- KAPSAM GÜVENLİĞİ: Kural A YALNIZ "bozuk ihaleler" (≥1 lot >50× maliyet) içinde çalışır.
-- SAĞLAM ihalelerde 14.751 dup grubu / ~12 Mr var (firma aynı fiyata 2 lot kazanmış olabilir
-- = meşru); onlara DOKUNULMAZ ("veriyi çöp sanıp silme" dersi, 26-21).
--
-- GERİ ALINABİLİR: dokunulan her satırın orijinali public.ihale_sonuclari_bozuk_yedek'te.
-- Geri alma:  UPDATE ihale_sonuclari s SET sozlesme_bedeli=y.o_sozlesme_bedeli,
--   kazanan_teklif=y.o_kazanan_teklif, en_dusuk_teklif=y.o_en_dusuk_teklif, ... FROM
--   ihale_sonuclari_bozuk_yedek y WHERE y.id=s.id;
--
-- Çalıştırma: docker exec -i supabase-db psql -U supabase_admin -d postgres < backend/migration_bozuk_sozlesme_temizle.sql
-- ============================================================================

BEGIN;
SET LOCAL statement_timeout = '0';

-- ── 1) Yedek tablosu (orijinal değerler) ───────────────────────────────────
CREATE TABLE IF NOT EXISTS public.ihale_sonuclari_bozuk_yedek (
  id                            uuid PRIMARY KEY,
  ikn                           text,
  kisim_no                      integer,
  kazanan_firma                 text,
  o_sozlesme_bedeli             bigint,
  o_kazanan_teklif              bigint,
  o_en_dusuk_teklif             bigint,
  o_en_yuksek_teklif            bigint,
  o_ortalama_teklif             bigint,
  o_tenzilat_yuzde              numeric,
  o_kazanan_teklif_farki_yuzde  numeric,
  yaklasik_maliyet              bigint,
  defect                        text,
  yedek_zamani                  timestamptz DEFAULT now()
);
REVOKE ALL ON public.ihale_sonuclari_bozuk_yedek FROM PUBLIC, anon;

-- ── Hedef kümeleri (geçici) ────────────────────────────────────────────────
-- Bozuk ihaleler: ≥1 lot fiziksel-imkansız (sözleşme > 50× yaklaşık maliyet)
CREATE TEMP TABLE _bozuk_ihale ON COMMIT DROP AS
  SELECT DISTINCT ikn FROM public.ihale_sonuclari
  WHERE yaklasik_maliyet > 0 AND sozlesme_bedeli > 50 * yaklasik_maliyet;
CREATE INDEX ON _bozuk_ihale (ikn);

-- Kural B: tek-lot ~1000× şişme (yaklaşık maliyet ANLAMLI bir referans, >1000)
CREATE TEMP TABLE _ruleB ON COMMIT DROP AS
  SELECT id FROM public.ihale_sonuclari
  WHERE lot_sayisi = 1 AND yaklasik_maliyet > 1000
    AND sozlesme_bedeli > 50 * yaklasik_maliyet;

-- Kural A: bozuk ihaleler içinde (ikn,firma,bedel) tekrarı → İLK'i tut, kalanı NULL'la.
-- NULL firma kendi grubu (COALESCE ''); kisim_no küçük olan (varsa 1. kısım) tutulur.
CREATE TEMP TABLE _ruleA ON COMMIT DROP AS
  SELECT id FROM (
    SELECT s.id,
           row_number() OVER (
             PARTITION BY s.ikn, COALESCE(s.kazanan_firma,''), s.sozlesme_bedeli
             ORDER BY s.kisim_no NULLS LAST, s.id) AS rn
    FROM public.ihale_sonuclari s
    JOIN _bozuk_ihale b ON b.ikn = s.ikn
    WHERE s.sozlesme_bedeli > 0
  ) q
  WHERE rn > 1
    AND id NOT IN (SELECT id FROM _ruleB);   -- kesişim yok (tek-lot dup olamaz) ama garanti

-- ── 2) Yedekle (dokunulacak tüm satırlar) ──────────────────────────────────
INSERT INTO public.ihale_sonuclari_bozuk_yedek
SELECT s.id, s.ikn, s.kisim_no, s.kazanan_firma,
       s.sozlesme_bedeli, s.kazanan_teklif, s.en_dusuk_teklif, s.en_yuksek_teklif,
       s.ortalama_teklif, s.tenzilat_yuzde, s.kazanan_teklif_farki_yuzde, s.yaklasik_maliyet,
       CASE WHEN b.id IS NOT NULL THEN 'B_single_1000x'
            ELSE 'A_framework_dup' END,
       now()
FROM public.ihale_sonuclari s
LEFT JOIN _ruleA a ON a.id = s.id
LEFT JOIN _ruleB b ON b.id = s.id
WHERE (a.id IS NOT NULL OR b.id IS NOT NULL)
ON CONFLICT (id) DO NOTHING;   -- migration tekrar çalışırsa yedek şişmesin

-- ── 3) Kural A: tekrarlanan çerçeve sözleşme bedelini NULL'la (bir kopya kalır) ──
UPDATE public.ihale_sonuclari s
   SET sozlesme_bedeli = NULL,
       kazanan_teklif  = NULL
FROM _ruleA a
WHERE a.id = s.id;

-- ── 4) Kural B: ~1000× şişmiş tek-lot sözleşme + teklif kolonlarını NULL'la ──
UPDATE public.ihale_sonuclari s
   SET sozlesme_bedeli            = NULL,
       kazanan_teklif             = NULL,
       en_dusuk_teklif            = NULL,
       en_yuksek_teklif           = NULL,
       ortalama_teklif            = NULL,
       tenzilat_yuzde             = NULL,
       kazanan_teklif_farki_yuzde = NULL
FROM _ruleB b
WHERE b.id = s.id;

COMMIT;

-- ── DOĞRULAMA ──────────────────────────────────────────────────────────────
-- SELECT defect, count(*) FROM ihale_sonuclari_bozuk_yedek GROUP BY 1;
-- SELECT to_char(sum(sozlesme_bedeli),'FM999,999,999,999,999') FROM ihale_sonuclari WHERE sozlesme_bedeli>0;
-- -- 116533 artık ~9,25 Mr olmalı (312 Mr değil):
-- SELECT to_char(sum(sozlesme_bedeli),'FM999,999,999,999') FROM ihale_sonuclari WHERE ikn='2013/116533' AND sozlesme_bedeli>0;
