-- Eski taksonomi kalıntılarını kanonik adlara taşı (23 Tem 2026).
--
-- BULUNUŞ: rekabet-analizi.html'in kategori dropdown'ı eski taksonomiyi kullanıyordu
-- (26 seçenekten 25'i sıfır sonuç). Onu düzeltirken veride de kalıntı olduğu görüldü:
-- lokal sınıflandırıcının eğitim raporunda "İnşaat & Yapım" f1=0,11 ve "Danışmanlık"
-- f1=0,20 ile en zayıf sınıflar arasındaydı — model ÖLÜ bir etiketi öğreniyordu.
--
-- İKİ AYRI ZARAR:
--   1) Bu satırlar arayüzden ERİŞİLEMEZ: kategori dropdown'ları js/kategoriler.js'ten
--      (41 kanonik) üretiliyor → kullanıcı bu değeri hiç seçemiyor, ihaleler görünmez oluyor.
--   2) Eğitim setini kirletiyor → sınıflandırıcı ölü etikete olasılık dağıtıyor.
--
-- Eşleme birebir ve bilgi kaybı yok (ikisinin de temiz kanonik karşılığı var).
UPDATE public.ilanlar SET kategori = 'İnşaat - Altyapı - Üstyapı - Yapım'
    WHERE kategori = 'İnşaat & Yapım';
UPDATE public.ilanlar SET kategori = 'Mühendislik - Mimarlık - Danışmanlık'
    WHERE kategori = 'Danışmanlık';

UPDATE public.dogrudan_temin_ilanlari SET kategori = 'İnşaat - Altyapı - Üstyapı - Yapım'
    WHERE kategori = 'İnşaat & Yapım';
UPDATE public.dogrudan_temin_ilanlari SET kategori = 'Mühendislik - Mimarlık - Danışmanlık'
    WHERE kategori = 'Danışmanlık';

-- Doğrulama: aşağıdaki sorgu 0 satır dönmeli.
SELECT 'KALINTI VAR' AS uyari, kategori, count(*)
  FROM public.ilanlar WHERE kategori IN ('İnşaat & Yapım','Danışmanlık') GROUP BY 1,2;
