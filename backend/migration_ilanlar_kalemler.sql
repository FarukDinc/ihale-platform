-- ilanlar'a malzeme/kalem listesi (rakip ihaleciler.com "Malzeme Listesi (N)").
-- KAYNAK BULUNDU (23 Tem probe): EKAP ihale detay yanıtı (GetByIhaleIdIhaleDetay) →
-- item.ihtiyacKalemiOkasList = [{adi, kodu, koduAdi}, ...]. detay_cek zaten bu endpoint'i
-- çağırıyor ama bu alanı çıkarmıyordu. Aynı yanıtta eIhale + kismiIhale de var (yapısal
-- teklif-türü → mevcut teklif_elektronik/teklif_kismi kolonlarını ilan_metni parse'tan daha
-- güvenilir doldurur). Kapsam detay_cek çağrılan ilanlarla sınırlı; backfill ile büyür.
ALTER TABLE public.ilanlar ADD COLUMN IF NOT EXISTS kalemler jsonb;   -- [{adi,kodu,koduAdi}]
GRANT SELECT (kalemler) ON public.ilanlar TO anon;                     -- misafir görebilsin (hassas değil)
NOTIFY pgrst, 'reload schema';
