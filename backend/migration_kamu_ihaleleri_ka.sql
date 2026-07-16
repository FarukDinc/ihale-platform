-- kamu_ihaleleri: Kalkınma Ajansları (ka.gov.tr) kaynağı için 2 ek kolon.
-- il = şehir (KA API 'city'); alt_kaynak = ajans kodu (baka/ahika/istka... 12 ajans).
-- kaynak='ka' kayıtları ozel-ihaleler (e-Satınalma) sayfasında "Kalkınma Ajansı" rozetiyle gösterilir
-- (kamu alıcısı değil, ajans hibesi alan ÖZEL firmaların denetimli ihaleleri — kullanıcı kararı).
ALTER TABLE public.kamu_ihaleleri ADD COLUMN IF NOT EXISTS il text;
ALTER TABLE public.kamu_ihaleleri ADD COLUMN IF NOT EXISTS alt_kaynak text;

NOTIFY pgrst, 'reload schema';
