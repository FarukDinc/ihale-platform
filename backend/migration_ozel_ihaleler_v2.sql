-- Özel İhaleler Faz 2: kazanan teklif seçimi (offer-update RLS'sine gerek kalmadan talep üzerinden).
ALTER TABLE public.satinalma_talepleri ADD COLUMN IF NOT EXISTS kazanan_teklif_id uuid;

-- Talep sahibi, gelen tekliflerin durumunu da güncelleyebilsin (kabul/red) — opsiyonel akış için.
DROP POLICY IF EXISTS "teklif_talep_sahibi_gunceller" ON public.tedarikci_teklifleri;
CREATE POLICY "teklif_talep_sahibi_gunceller" ON public.tedarikci_teklifleri
  FOR UPDATE TO authenticated USING (
    auth.uid() = (SELECT olusturan_user_id FROM public.satinalma_talepleri t WHERE t.id = talep_id)
  );
GRANT UPDATE ON public.tedarikci_teklifleri TO authenticated;

NOTIFY pgrst, 'reload schema';
