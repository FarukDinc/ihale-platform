-- =============================================================================
-- migration_dt_index.sql — DT listesinde kategori/tür filtrelerini kullanılabilir kılar
-- =============================================================================
--
-- SORUN (18 Tem 2026, canlıda ölçüldü — anon key, /rest/v1):
--   dogrudan_temin_ilanlari 1.489.878 satır. Mevcut dogrudan-temin.html sayfasındaki
--   Kategori ve Tür dropdown'ları indekssiz kolonlara düşüyor ve ORDER BY tarih DESC
--   ile birleşince tam tarama yapıyor:
--
--     ?kategori=eq.<x>&order=tarih.desc            -> HTTP 522, ~20 sn (Cloudflare origin timeout)
--     ?kategori=... + Prefer:count=exact           -> HTTP 522, ~20 sn
--     ?tur=eq.Yapım&order=tarih.desc               -> HTTP 200 ama 38,1 sn
--     ?tur=... + Prefer:count=exact                -> HTTP 206 ama 14,5 sn
--
--   KIYAS (indeksli kolon, aynı tablo, aynı sıralama):
--     ?il=eq.ANKARA&order=tarih.desc               -> HTTP 200, 1,6 sn
--     ?il=... + Prefer:count=exact                 -> HTTP 206, 2,7 sn
--     filtresiz + Prefer:count=exact               -> HTTP 206, 2,0 sn
--
--   Yani sorun sayımda değil, İNDEKSTE. Kullanıcı bugün kategori seçtiğinde sayfa
--   ya 20 saniye bekliyor ya da hata alıyor. Bu, detaylı aramadan bağımsız MEVCUT
--   bir hata; yeni filtreler eklemeden önce kapatılmalı yoksa daha da kötüleşir.
--
-- NEDEN ŞİMDİYE KADAR FARK EDİLMEDİ:
--   idx_dt_ilanlari_kategori_tarih migration_dashboard_dt_ozet.sql'de YORUM İÇİNDE
--   duruyor ("transaction dışında elle çalıştırılır" notuyla) — yani prod'a hiç
--   uygulanmamış. Bu dosya o eksiği kapatır ve tür için de karşılığını ekler.
--
-- BİLEŞİK (kolon, tarih DESC) TERCİHİ:
--   Tek kolonluk indeks filtreyi hızlandırır ama ORDER BY tarih DESC için yine
--   sıralama gerekir (1,49M satırda pahalı). (kategori, tarih DESC) bileşiği hem
--   filtreyi hem sıralamayı tek indeksten karşılar — il indeksinin hızlı olmasının
--   sebebi de sayfanın il+tarih erişim deseniyle uyuşması.
--
-- !! CONCURRENTLY: BU DOSYADA BEGIN/COMMIT YOK — bilinçli.
--   CREATE INDEX CONCURRENTLY transaction bloğu içinde çalışmaz (25001 hatası verir).
--   Karşılığında tabloyu yazmaya kapatmaz; gece scraper'ı koşarken bile güvenlidir.
--   1,49M satırda her indeks birkaç dakika sürebilir — sabırlı olun, takılmadı.
--
-- Uygulama:
--   docker exec -i supabase-db psql -U postgres -d postgres < backend/migration_dt_index.sql
--
-- İlgili hafıza: statement-timeout-edge, client-load-all-bug
-- =============================================================================

-- Kategori + tarih: dropdown'dan kategori seçimi + varsayılan "En Yeni" sıralaması
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_dt_ilanlari_kategori_tarih
  ON public.dogrudan_temin_ilanlari (kategori, tarih DESC)
  WHERE kategori IS NOT NULL;

-- Tür + tarih: Mal / Hizmet / Yapım / Danışmanlık dropdown'ı
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_dt_ilanlari_tur_tarih
  ON public.dogrudan_temin_ilanlari (tur, tarih DESC)
  WHERE tur IS NOT NULL;

ANALYZE public.dogrudan_temin_ilanlari;

-- =============================================================================
-- DOĞRULAMA — uygulamadan sonra (anon key ile, süreler saniye)
-- =============================================================================
--   curl -s -o /dev/null -w '%{http_code} %{time_total}\n' -H "apikey: $ANON" -H "Authorization: Bearer $ANON" \
--     -H 'Range: 0-24' \
--     'https://ihaleglobal.com/rest/v1/dogrudan_temin_ilanlari?select=dt_no&tur=eq.Yap%C4%B1m&order=tarih.desc'
--   Beklenen: 200 ve ~1-2 sn (öncesi: 38 sn). Kategori için de benzer.
--
-- SQL tarafı — indeks gerçekten kullanılıyor mu:
--   EXPLAIN (ANALYZE, BUFFERS)
--   SELECT dt_no FROM public.dogrudan_temin_ilanlari
--    WHERE tur = 'Yapım' ORDER BY tarih DESC LIMIT 25;
--   Beklenen: "Index Scan using idx_dt_ilanlari_tur_tarih". "Seq Scan" görürsen
--   indeks oluşmamış ya da planlayıcı ANALYZE görmemiş demektir.
--
-- İndekslerin oluştuğunu listele:
--   SELECT indexname FROM pg_indexes
--    WHERE tablename = 'dogrudan_temin_ilanlari' ORDER BY indexname;
--
-- NOT: CONCURRENTLY başarısız olursa indeks INVALID durumda kalır ve sorguda
-- kullanılmaz. Kontrol:
--   SELECT c.relname FROM pg_index i JOIN pg_class c ON c.oid = i.indexrelid
--    WHERE NOT i.indisvalid;
-- Çıkan olursa: DROP INDEX CONCURRENTLY <ad>; sonra bu dosyayı tekrar çalıştırın.
