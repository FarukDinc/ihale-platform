-- ============================================================================
-- migration_qa_26_data_fixes.sql — MADDE 26 veri düzeltmeleri (2 Ağu 2026)
--   Teşhis: backend/qa_diagnostics.sql çıktısı. Hepsi idempotent, önce SAYIM raporlar.
--   26-3  İmkânsız tenzilat (yaklaşık maliyet çöp) → tenzilat_yuzde NULL
--   26-21 Sentetik placeholder yaklaşık maliyet (min=10785492 & max=43142132) → NULL
--   26-6  İl adı 'İZMIR' (noktasız) → 'İZMİR'
--   26-8  Sektör sızıntısı: İnşaat & Yapım → kanonik İnşaat; Mal/Hizmet Alımı → Diğer
--   26-5  DT +1 yıl parse hatası (gün_farkı ~365) → tarih -1 yıl; +3 yıl/çöp → NULL
--
-- Çalıştırma:
--   docker exec -i supabase-db psql -U supabase_admin -d postgres < backend/migration_qa_26_data_fixes.sql
-- ============================================================================
\pset pager off
BEGIN;

-- ── 26-3: İmkânsız tenzilat ────────────────────────────────────────────────
-- tenzilat_yuzde <= -100 (teklif > 2× maliyet) veya > 100 (teklif < 0) = imkânsız.
-- Kaynak yaklaşık maliyet çöp; gerçek tenzilat bilinemez → NULL (frontend "—" gösterir).
\echo '26-3: nullanacak imkansiz tenzilat sayisi:'
SELECT count(*) FROM ihale_sonuclari WHERE tenzilat_yuzde <= -100 OR tenzilat_yuzde > 100;
UPDATE ihale_sonuclari SET tenzilat_yuzde = NULL
 WHERE tenzilat_yuzde <= -100 OR tenzilat_yuzde > 100;

-- ── 26-21: Sentetik placeholder yaklaşık maliyet ───────────────────────────
-- min=10.785.492 & max=43.142.132 (max=min×4) alakasız ihalelere yapıştırılmış → çöp.
\echo '26-21: nullanacak placeholder maliyet sayisi (beklenen ~2068+):'
SELECT count(*) FROM ilanlar WHERE yaklasik_maliyet_min = 10785492 AND yaklasik_maliyet_max = 43142132;
UPDATE ilanlar SET yaklasik_maliyet_min = NULL, yaklasik_maliyet_max = NULL
 WHERE yaklasik_maliyet_min = 10785492 AND yaklasik_maliyet_max = 43142132;

-- ── 26-6: İl adı noktasız İ → noktalı ──────────────────────────────────────
\echo '26-6: duzeltilecek İZMIR satiri:'
SELECT count(*) FROM ilanlar WHERE il = 'İZMIR';
UPDATE ilanlar SET il = 'İZMİR' WHERE il = 'İZMIR';

-- ── 26-8: Sektör taksonomi sızıntısı ───────────────────────────────────────
\echo '26-8: reklasifiye edilecek kategoriler:'
SELECT kategori, count(*) FROM ilanlar
 WHERE kategori IN ('İnşaat & Yapım','Mal Alımı','Hizmet Alımı') GROUP BY kategori;
UPDATE ilanlar SET kategori = 'İnşaat - Altyapı - Üstyapı - Yapım' WHERE kategori = 'İnşaat & Yapım';
UPDATE ilanlar SET kategori = 'Diğer' WHERE kategori IN ('Mal Alımı','Hizmet Alımı');

-- ── 26-5: DT ileri-tarih (+1 yıl parse) ────────────────────────────────────
-- yayın var + son tarih ~1 yıl ileri (360-400 gün) = +1 yıl parse hatası → 1 yıl geri al.
\echo '26-5a: +1 yil duzeltilecek DT sayisi:'
SELECT count(*) FROM dogrudan_temin_ilanlari
 WHERE yayin_tarihi IS NOT NULL AND tarih > now() + interval '200 days'
   AND (tarih::date - yayin_tarihi::date) BETWEEN 360 AND 400;
UPDATE dogrudan_temin_ilanlari
   SET tarih = tarih - interval '1 year'
 WHERE yayin_tarihi IS NOT NULL AND tarih > now() + interval '200 days'
   AND (tarih::date - yayin_tarihi::date) BETWEEN 360 AND 400;
-- Kalan aşırı-ileri (yayın yok veya >400 gün ileri) = güvenilmez → tarih NULL.
\echo '26-5b: NULL yapilacak (guvenilmez ileri tarih) DT sayisi:'
SELECT count(*) FROM dogrudan_temin_ilanlari WHERE tarih > now() + interval '400 days';
UPDATE dogrudan_temin_ilanlari SET tarih = NULL WHERE tarih > now() + interval '400 days';

COMMIT;

-- ── Kontroller ─────────────────────────────────────────────────────────────
\echo '=== KONTROL: aktif bütçe histogramı (artık dağılmalı) ==='
SELECT
  count(*) FILTER (WHERE yaklasik_maliyet_min > 0 AND yaklasik_maliyet_min < 500000)          b0,
  count(*) FILTER (WHERE yaklasik_maliyet_min >= 500000 AND yaklasik_maliyet_min < 2000000)   b1,
  count(*) FILTER (WHERE yaklasik_maliyet_min >= 2000000 AND yaklasik_maliyet_min < 10000000) b2,
  count(*) FILTER (WHERE yaklasik_maliyet_min >= 10000000 AND yaklasik_maliyet_min < 50000000) b3,
  count(*) FILTER (WHERE yaklasik_maliyet_min >= 50000000 AND yaklasik_maliyet_min < 200000000) b4,
  count(*) FILTER (WHERE yaklasik_maliyet_min >= 200000000) b5
FROM ilanlar WHERE durum='aktif';
\echo '=== KONTROL: sektör sızıntısı kalmadı mı (0 satır beklenir) ==='
SELECT kategori, count(*) FROM ilanlar WHERE kategori IN ('İnşaat & Yapım','Mal Alımı','Hizmet Alımı') GROUP BY kategori;
