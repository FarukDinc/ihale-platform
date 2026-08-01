-- ============================================================================
-- qa_diagnostics.sql — MADDE 26 QA turu DB bulguları için READ-ONLY teşhis
-- (1 Ağu 2026). SADECE SELECT — hiçbir yazma yok, güvenle çalıştırılabilir.
--
-- Çalıştırma (çıktıyı Claude'a yapıştır):
--   docker exec -i supabase-db psql -U supabase_admin -d postgres -f - < backend/qa_diagnostics.sql
--   (veya: docker exec -i supabase-db psql -U supabase_admin -d postgres < backend/qa_diagnostics.sql)
-- ============================================================================
\pset pager off

\echo '=== 26-2: Trilyon-TL firma anomalisi ==='
-- En yüksek 15 ciro (bozuk toplam avı):
SELECT ad, toplam_ciro, toplam_sozlesme_sayisi
  FROM yukleniciler ORDER BY toplam_ciro DESC NULLS LAST LIMIT 15;
\echo '--- 100 milyar üstü TEKİL sözleşme bedelleri (şüpheli ham kayıt) ---'
SELECT ilan_id, left(kazanan_firma,45) firma, sozlesme_bedeli, kazanan_teklif, sonuc_tarihi
  FROM ihale_sonuclari
 WHERE sozlesme_bedeli > 100000000000 OR kazanan_teklif > 100000000000
 ORDER BY greatest(coalesce(sozlesme_bedeli,0),coalesce(kazanan_teklif,0)) DESC LIMIT 25;

\echo ''
\echo '=== 26-3: İmkânsız tenzilat (tek-kısımlı) ==='
-- ihale_sonuclari şeması (tenzilat/maliyet kolon adları için):
SELECT column_name, data_type FROM information_schema.columns
 WHERE table_schema='public' AND table_name='ihale_sonuclari' ORDER BY ordinal_position;
\echo '--- lot_sayisi dağılımı (tenzilatlı kayıtlar) ---'
SELECT lot_sayisi, count(*) FROM ihale_sonuclari WHERE tenzilat_yuzde IS NOT NULL GROUP BY 1 ORDER BY 1 LIMIT 20;
\echo '--- tek-kısımlı ihalede aşırı tenzilat örnekleri (|.|>90 veya <-30) ---'
SELECT ilan_id, tenzilat_yuzde, kazanan_teklif, sozlesme_bedeli, lot_sayisi
  FROM ihale_sonuclari
 WHERE coalesce(lot_sayisi,1)=1 AND (tenzilat_yuzde > 90 OR tenzilat_yuzde < -30)
 ORDER BY tenzilat_yuzde LIMIT 25;

\echo ''
\echo '=== 26-21: Aktif ihale yaklaşık maliyet dağılımı (bütçe histogram teşhisi) ==='
SELECT
  count(*) FILTER (WHERE yaklasik_maliyet_min > 0 AND yaklasik_maliyet_min < 500000)        b0_500bin,
  count(*) FILTER (WHERE yaklasik_maliyet_min >= 500000 AND yaklasik_maliyet_min < 2000000) b1_2mn,
  count(*) FILTER (WHERE yaklasik_maliyet_min >= 2000000 AND yaklasik_maliyet_min < 10000000) b2_10mn,
  count(*) FILTER (WHERE yaklasik_maliyet_min >= 10000000 AND yaklasik_maliyet_min < 50000000) b3_50mn,
  count(*) FILTER (WHERE yaklasik_maliyet_min >= 50000000 AND yaklasik_maliyet_min < 200000000) b4_200mn,
  count(*) FILTER (WHERE yaklasik_maliyet_min >= 200000000) b5_ust,
  count(*) FILTER (WHERE yaklasik_maliyet_min IS NULL OR yaklasik_maliyet_min <= 0) byok
FROM ilanlar WHERE durum='aktif';
\echo '--- EN KÜÇÜK 15 aktif maliyet (gerçekten hepsi >=10M mi?) ---'
SELECT left(baslik,50) baslik, yaklasik_maliyet_min, yaklasik_maliyet_max, tur
  FROM ilanlar WHERE durum='aktif' AND yaklasik_maliyet_min > 0
 ORDER BY yaklasik_maliyet_min ASC LIMIT 15;

\echo ''
\echo '=== 26-6: İl adı noktalı/noktasız İ dup ==='
SELECT 'ilanlar' t, il, count(*) FROM ilanlar WHERE il ILIKE 'IZM%' OR il ILIKE 'İZM%' GROUP BY il
UNION ALL SELECT 'dt', il, count(*) FROM dogrudan_temin_ilanlari WHERE il ILIKE 'IZM%' OR il ILIKE 'İZM%' GROUP BY il
ORDER BY 1,2;
\echo '--- yukleniciler.il içinde İ/ı dup adayları (aynı ad, farklı yazım) ---'
SELECT il, count(*) FROM yukleniciler
 WHERE il IN ('İZMIR','İZMİR','IZMİR','IZMIR') GROUP BY il ORDER BY il;

\echo ''
\echo '=== 26-8: Sektör taksonomi sızıntısı (kanonik-olmayan kategoriler) ==='
SELECT kategori, count(*) FROM ilanlar
 WHERE kategori IN ('Mal Alımı','Hizmet Alımı','İnşaat & Yapım','Mal Alimi','Hizmet Alimi')
 GROUP BY kategori ORDER BY count(*) DESC;
\echo '--- ilanlar TÜM kategori sayımı (kanonik 41 dışını gör) ---'
SELECT kategori, count(*) FROM ilanlar GROUP BY kategori ORDER BY count(*) DESC;

\echo ''
\echo '=== 26-5: DT ileri-tarih (+1 yıl parse hatası) + test kaydı ==='
SELECT count(*) AS ileri_tarihli_dt
  FROM dogrudan_temin_ilanlari WHERE tarih > now() + interval '200 days';
\echo '--- örnekler (yayin vs tarih farkı ~1 yıl mı?) ---'
SELECT dt_no, left(baslik,40) baslik, yayin_tarihi, tarih,
       (tarih::date - yayin_tarihi::date) gun_farki
  FROM dogrudan_temin_ilanlari WHERE tarih > now() + interval '200 days'
 ORDER BY tarih DESC LIMIT 20;
\echo '--- test/çöp kayıtlar (denme/deneme/test) ---'
SELECT dt_no, baslik, idare FROM dogrudan_temin_ilanlari
 WHERE lower(baslik) IN ('denme','deneme','test','asd','aaa') OR baslik ~* '^(test|deneme)\s*$' LIMIT 20;

\echo ''
\echo '=== 26-24: DT sonuç sayacı vs gerçek kazananlı ==='
SELECT
  (SELECT count(*) FROM dogrudan_temin_ilanlari WHERE durum='Sonuç Duyurusu Yayımlanmış') AS durum_sonuc,
  (SELECT count(*) FROM dogrudan_temin_sonuclari WHERE kazanan_firma IS NOT NULL)          AS kazananli;

\echo ''
\echo '=== 26-28: Bağlantısız kurumlar (DETSİS dışı) — kaynak tablo teşhisi ==='
-- idare_ozet_mv / idare tablosunda DETSİS eşleşmeyen sayısı (kolon adına göre):
SELECT column_name FROM information_schema.columns
 WHERE table_schema='public' AND table_name='idare_ozet_mv' ORDER BY ordinal_position;

\echo ''
\echo '=== 26-23: DMO/kamu firma sınıflandırıcı yukleniciler''da uygulanıyor mu? ==='
SELECT ad, toplam_sozlesme_sayisi FROM yukleniciler
 WHERE ad ILIKE '%DEVLET MALZEME OFİSİ%' OR ad ILIKE '%İŞYURT%' OR ad ILIKE '%CEZA İNFAZ%'
 ORDER BY toplam_sozlesme_sayisi DESC NULLS LAST LIMIT 15;
-- firma_kurum_mu fonksiyonu var mı:
SELECT proname FROM pg_proc WHERE proname='firma_kurum_mu';

\echo ''
\echo '=== TEŞHİS BİTTİ — çıktının tamamını Claude''a yapıştır ==='
