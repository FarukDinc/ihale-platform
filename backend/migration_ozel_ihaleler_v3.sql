-- Özel İhaleler v3: açık RFQ'lar HERKESE görünür (tedarikçi keşif hunisi + SEO; kamu ihaleleri gibi).
-- Teklif verme / oluşturma / yönetme yine authenticated + rol bazlı kalır. Teklifler (offers) gizli kalır.
DROP POLICY IF EXISTS "talep_authenticated_okur" ON public.satinalma_talepleri;
DROP POLICY IF EXISTS "talep_herkes_okur" ON public.satinalma_talepleri;
CREATE POLICY "talep_herkes_okur" ON public.satinalma_talepleri
  FOR SELECT USING (true);
GRANT SELECT ON public.satinalma_talepleri TO anon;

NOTIFY pgrst, 'reload schema';
