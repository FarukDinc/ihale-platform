-- ============================================================
-- Dashboard haritası hızlandırma — il_sayim_aktif / dt_il_sayim_aktif (31 Tem 2026)
-- ------------------------------------------------------------
-- Bana Özel haritası 3 isteği Promise.all ile çeker; en yavaşı bekler:
--   dt_il_sayim_aktif 5.4s (asıl darboğaz) · il_sayim_aktif 1.8s · geojson 1.7s.
-- İkisi de il-bazlı GROUP BY; aktif alt-kümeyi il'e göre indeksleyince index-only grup → hızlı.
--
-- CONCURRENTLY: canlı tabloyu KİLİTLEMEDEN indeks kurar (BEGIN/COMMIT YOK — her biri kendi
--   otomatik-commit'inde). 1.5-2M satır → birkaç dakika sürebilir, site çalışmaya devam eder.
--
-- Çalıştır (superuser; her satır ayrı, CONCURRENTLY transaction'sız):
--   docker exec -i supabase-db psql -U supabase_admin -d postgres < backend/migration_harita_hizlandirma.sql
-- ============================================================

-- DT: aktif durum + il partial indeksi (dt_il_sayim_aktif WHERE'iyle BİREBİR predicate).
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_dt_ilanlari_aktif_il
  ON public.dogrudan_temin_ilanlari (il)
  WHERE durum IN ('Doğrudan Temin Duyurusu Yayımlanmış', 'Teklifler Değerlendiriliyor');

-- İhale: son_teklif_tarihi >= now() aralığı + il (partial predicate now() IMMUTABLE olmadığı
-- için durum yok; son_teklif sıralı indeks aralığı gelecek-tarihli ~6K satırı hızlı verir).
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_ilanlar_sonteklif_il
  ON public.ilanlar (son_teklif_tarihi, il)
  WHERE son_teklif_tarihi IS NOT NULL;

-- Doğrulama (ikisi de <0.5s olmalı):
--   \timing on
--   SELECT sum(adet) FROM dt_il_sayim_aktif();
--   SELECT sum(adet) FROM il_sayim_aktif();
