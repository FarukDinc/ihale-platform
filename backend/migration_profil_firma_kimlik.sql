-- profil: e-Satınalma (RFQ) için firma kimlik alanları. Şu ana kadar VKN yalnız localStorage'daydı,
-- açık adres hiç yoktu. Artık RFQ formu bunları profilden OTOMATİK+KİLİTLİ çeker (kullanıcı kararı):
-- önce profil doldurulur, sonra e-Satınalma'da değiştirilemez. Adres MaaS/harita eşleştirmesi için kritik.
-- profil tablosu kullanıcıya özel (RLS user_id=auth.uid()); bu alanlar anon'a AÇILMAZ (satinalma_talepleri'nin
-- aksine — orada acik_adres/VKN anon'dan REVOKE'luydu, bkz. migration_rfq_anon_kolon).
ALTER TABLE public.profil ADD COLUMN IF NOT EXISTS vergi_no    text;
ALTER TABLE public.profil ADD COLUMN IF NOT EXISTS acik_adres  text;
ALTER TABLE public.profil ADD COLUMN IF NOT EXISTS firma_il    text;
ALTER TABLE public.profil ADD COLUMN IF NOT EXISTS firma_ilce  text;

NOTIFY pgrst, 'reload schema';
