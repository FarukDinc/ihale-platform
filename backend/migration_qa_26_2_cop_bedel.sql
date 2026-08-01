-- ============================================================================
-- migration_qa_26_2_cop_bedel.sql — 26-2: trilyon-TL firma anomalisi
--   (2 Ağu 2026). TEŞHİS: ihale_sonuclari id=9fd3be07-2329-4b30-a74d-c909351b6432
--   kazanan_teklif=sozlesme_bedeli=1111111111111 (on üç adet 1 = ~1,1 trilyon TL).
--   Bariz çöp/test EKAP kaydı → YAMAN ENERJİ cirosunu ve Bank "12,3 Tn" toplamını şişiriyordu.
--   toplam_ciro = SUM(kazanan_teklif) (bkz. yuklenici_yenile) → teklif'i null'lamak yeterli.
--
-- EŞİK: ≥900 milyar TL TEKİL bedel imkânsız. En büyük GERÇEK tek sözleşme ~85 milyar
--   (KALYON Malatya-Narlı demiryolu). REC/YAPI MERKEZİ gibi 75-187 milyar değerler
--   FİRMA TOPLAMLARI (SUM), tekil satır değil → eşik onları etkilemez.
--
-- Çalıştırma:
--   docker exec -i supabase-db psql -U supabase_admin -d postgres < backend/migration_qa_26_2_cop_bedel.sql
-- Idempotent (düzeltildikten sonra eşik hiçbir satırı yakalamaz → no-op).
-- ============================================================================
BEGIN;

-- 1) Etkilenecek firmaların normalize adlarını sakla (ciro yeniden hesabı için)
CREATE TEMP TABLE _qa262_firms ON COMMIT DROP AS
  SELECT DISTINCT normalize_firma(kazanan_firma) AS na
    FROM ihale_sonuclari
   WHERE (kazanan_teklif  >= 900000000000
       OR sozlesme_bedeli >= 900000000000)
     AND kazanan_firma IS NOT NULL;

\echo '--- Temizlenecek çöp satırlar: ---'
SELECT id, left(kazanan_firma,40) firma, kazanan_teklif, sozlesme_bedeli, sonuc_tarihi
  FROM ihale_sonuclari
 WHERE kazanan_teklif >= 900000000000 OR sozlesme_bedeli >= 900000000000;

-- 2) Çöp bedelleri null'la (satırı SİLME — sözleşme sayısı korunur, yalnız fake tutar gider)
UPDATE ihale_sonuclari
   SET kazanan_teklif = NULL, sozlesme_bedeli = NULL
 WHERE kazanan_teklif >= 900000000000 OR sozlesme_bedeli >= 900000000000;

-- 3) Etkilenen firmaların toplam_ciro'sunu anında yeniden hesapla
--    (tam yuklenici_yenile gece cron'da; burada yalnız etkilenenler)
UPDATE yukleniciler y
   SET toplam_ciro = r.ciro, guncellendi = now()
  FROM (
    SELECT normalize_firma(s.kazanan_firma) AS na, COALESCE(SUM(s.kazanan_teklif),0) AS ciro
      FROM ihale_sonuclari s
     WHERE normalize_firma(s.kazanan_firma) IN (SELECT na FROM _qa262_firms)
     GROUP BY 1
  ) r
 WHERE y.normalize_ad = r.na;

COMMIT;

\echo '--- Kontrol: YAMAN ENERJİ artık gerçek cirosunu göstermeli (~<1 milyar bekleniyor, 47 söz.) ---'
SELECT ad, toplam_ciro, toplam_sozlesme_sayisi
  FROM yukleniciler WHERE ad ILIKE '%YAMAN ENERJİ%';
\echo '--- Yeni en yüksek 5 ciro (trilyon gitti mi): ---'
SELECT left(ad,50) ad, toplam_ciro FROM yukleniciler ORDER BY toplam_ciro DESC NULLS LAST LIMIT 5;
