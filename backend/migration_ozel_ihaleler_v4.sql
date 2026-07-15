-- e-Satınalma v4: RFQ AÇMAYI kurumsallığa bağla.
--  1) VKN + ünvan zorunlu (tedarikçi kime teklif verdiğini bilsin).
--  2) İhale YAYINLAMA yalnızca geçerli 'kurumsal' abonelikle (ciddiyetsiz firmayı eler).
-- Güvenlik JS'te DEĞİL burada (RLS): anon key ile herkes /rest/v1'e POST atabilir.

-- 1) VKN kolonu (ünvan zaten 'olusturan_firma' olarak var).
ALTER TABLE public.satinalma_talepleri ADD COLUMN IF NOT EXISTS olusturan_vkn text;

-- Format guard: mevcut NULL satırlar geçer; dolu olan 10 hane rakam olmalı.
ALTER TABLE public.satinalma_talepleri DROP CONSTRAINT IF EXISTS satinalma_vkn_format;
ALTER TABLE public.satinalma_talepleri ADD CONSTRAINT satinalma_vkn_format
  CHECK (olusturan_vkn IS NULL OR olusturan_vkn ~ '^[0-9]{10}$');

-- 1b) Yapısal iş/teslimat adresi (MaaS harita + lojistik için hazır veri; il zaten var).
--     Düz metin değil yapısal: pin koordinatı il/ilçe merkezinden, ileride açık adres geocode edilir.
ALTER TABLE public.satinalma_talepleri ADD COLUMN IF NOT EXISTS ilce       text;
ALTER TABLE public.satinalma_talepleri ADD COLUMN IF NOT EXISTS acik_adres text;
ALTER TABLE public.satinalma_talepleri ADD COLUMN IF NOT EXISTS enlem      double precision;  -- lat (ileride geocode)
ALTER TABLE public.satinalma_talepleri ADD COLUMN IF NOT EXISTS boylam     double precision;  -- lng (ileride geocode)

-- 2) Kurumsal kontrolü: SECURITY DEFINER fonksiyon → kullanici_krediler'i çağıranın RLS/grant'ine
--    bağlı OLMADAN okur (owner yetkisiyle). Parametre YOK → yalnız kendi planını kontrol eder
--    (auth.uid() JWT'den gelir, SECURITY DEFINER bunu değiştirmez), başkasının planı sızmaz.
CREATE OR REPLACE FUNCTION public.kullanici_kurumsal_mi()
RETURNS boolean
LANGUAGE sql STABLE SECURITY DEFINER SET search_path = public
AS $$
  SELECT EXISTS (
    SELECT 1 FROM public.kullanici_krediler kk
    WHERE kk.kullanici_id = auth.uid()
      AND kk.plan = 'kurumsal'
      AND (kk.plan_bitis IS NULL OR kk.plan_bitis > now())
  );
$$;
REVOKE ALL     ON FUNCTION public.kullanici_kurumsal_mi() FROM public, anon;
GRANT  EXECUTE ON FUNCTION public.kullanici_kurumsal_mi() TO authenticated, service_role;

-- 3) INSERT policy: sahiplik + VKN(10 hane) + ünvan dolu + geçerli KURUMSAL abonelik.
DROP POLICY IF EXISTS "talep_sahibi_ekler"   ON public.satinalma_talepleri;
DROP POLICY IF EXISTS "talep_kurumsal_ekler" ON public.satinalma_talepleri;
CREATE POLICY "talep_kurumsal_ekler" ON public.satinalma_talepleri
  FOR INSERT TO authenticated
  WITH CHECK (
    auth.uid() = olusturan_user_id
    AND olusturan_vkn ~ '^[0-9]{10}$'
    AND olusturan_firma IS NOT NULL AND btrim(olusturan_firma) <> ''
    AND il         IS NOT NULL AND btrim(il)         <> ''   -- harita/MaaS konum çapası zorunlu
    AND ilce       IS NOT NULL AND btrim(ilce)       <> ''
    AND acik_adres IS NOT NULL AND btrim(acik_adres) <> ''
    AND public.kullanici_kurumsal_mi()
  );

-- Not: v3 "talep_herkes_okur" (anon+authenticated SELECT) korunuyor → VKN + ünvan tedarikçilere
-- görünür. VKN ticari veri (fatura üstünde açık), KVKK anlamında kişisel veri değil.

NOTIFY pgrst, 'reload schema';
