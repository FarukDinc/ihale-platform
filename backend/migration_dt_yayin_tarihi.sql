-- ============================================================
-- İhaleGlobal — dogrudan_temin_ilanlari.yayin_tarihi (EKAP E8)
--
-- SORUN: DT'de tek tarih alanı vardı (`tarih` = EKAP E7) ve iki anlam taşıyordu:
--   • aktif duyurularda GELECEĞE gidiyor (1.630 kayıt, 2028'e kadar) → teklif/ihale tarihi
--   • sonuçlananlarda hep geçmiş → sonuç tarihi
-- "Bu ilan ne zaman yayımlandı?" sorusunun cevabı yoktu. `olusturulma` bizim kazıma
-- anımız (tüm tablo 11-18 Tem 2026 aralığında) → kullanıcıya gösterilemez.
--
-- BULGU: EKAP'ın liste yanıtı (YeniIhaleAramaData.ashx?metot=dtAra) zaten E8 alanını
-- döndürüyordu, kazıyıcı almıyordu. Canlı probe (18 Tem):
--   E7=17.07.2026 / E8=18.07.2026   ve   E7=24.03.2026 / E8=18.07.2026
-- → E8 tüm kayıtlarda "duyurunun yayımlandığı gün", E7'den bağımsız. Aradığımız alan bu.
--
-- Doldurma: kazıyıcı artık E8'i yazıyor (ekap_dogrudan_temin_scraper.py).
-- Mevcut 1,48M satır için TEK SEFERLİK tam tarama gerekir (upsert on_conflict=dt_no
-- merge-duplicates olduğu için var olan satırları günceller):
--   systemd-run --unit=dt-yayin --working-directory=/opt/ihale-platform/backend \
--     /opt/ihale-platform/backend/venv/bin/python ekap_dogrudan_temin_scraper.py \
--     --start-page 1 --reset --max-pages 12000
--   (128 kayıt/sayfa × ~11.600 sayfa; ilerleme: journalctl -u dt-yayin -f)
--
-- Çalıştırma:
--   docker exec -i supabase-db psql -U postgres -d postgres < backend/migration_dt_yayin_tarihi.sql
-- ============================================================

BEGIN;

ALTER TABLE public.dogrudan_temin_ilanlari
  ADD COLUMN IF NOT EXISTS yayin_tarihi TIMESTAMPTZ;

-- Liste "en yeni yayın" sıralaması + tarih aralığı filtresi için
CREATE INDEX IF NOT EXISTS idx_dt_ilanlari_yayin_tarih
  ON public.dogrudan_temin_ilanlari (yayin_tarihi DESC);

-- Misafir maskeleme kolon-bazlı: yeni kolonda anon'un yetkisi OLMAZ → açıkça ver.
-- Hassas değil (yalnız duyuru yayın tarihi); idare gibi kilitli kolonlarla ilgisi yok.
GRANT SELECT (yayin_tarihi) ON public.dogrudan_temin_ilanlari TO anon;

COMMIT;

-- Doğrulama: tarama öncesi hepsi NULL olmalı; tarama ilerledikçe dolar.
SELECT count(*) AS toplam,
       count(yayin_tarihi) AS yayin_tarihi_dolu,
       min(yayin_tarihi)::date AS en_eski,
       max(yayin_tarihi)::date AS en_yeni
FROM public.dogrudan_temin_ilanlari;
