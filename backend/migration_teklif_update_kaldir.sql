-- Denetim #32: "teklif_talep_sahibi_gunceller" policy'si alıcıya tedarikci_teklifleri üzerinde KOLON-KISITSIZ
-- UPDATE veriyordu → alıcı, tedarikçinin teklif_bedeli/aciklama'sını değiştirebilirdi (veri bütünlüğü/tampering).
-- Ödül akışı satinalma_talepleri.kazanan_teklif_id üzerinden yapılıyor; bu policy hiçbir kodda KULLANILMIYOR.
-- Kaldırıyoruz. (İleride kabul/red gerekirse: SECURITY DEFINER RPC ile yalnız 'durum' kolonunu güncelle.)
DROP POLICY IF EXISTS "teklif_talep_sahibi_gunceller" ON public.tedarikci_teklifleri;
-- Not: RLS açık ve başka UPDATE policy'si olmadığı için artık tedarikci_teklifleri güncellenemez (sealed-bid: teklif finaldir).
NOTIFY pgrst, 'reload schema';
