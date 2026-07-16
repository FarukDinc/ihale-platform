-- Denetim #18: satinalma_talepleri anon'a TAM okunuyordu → acik_adres/olusturan_vkn/enlem/boylam
-- giriş yapmadan herkese + arama motoru botlarına açıktı (toplu alıcı-adres/VKN kazıma + KVKK riski).
-- Çözüm: anon'a column-level SELECT — hassas kolonlar HARİÇ. authenticated tam erişim korunur (RLS USING true).
-- (Frontend anon yolları zaten güvenli kolon seçiyor; ozel-ihale-detay anon dalı da güvenli kolona çevrildi.)
REVOKE SELECT ON public.satinalma_talepleri FROM anon;
GRANT SELECT (
  id, olusturan_user_id, olusturan_firma, baslik, aciklama, kategori,
  il, ilce, miktar, tahmini_bedel, para_birimi, son_teklif_tarihi,
  durum, olusturulma, kazanan_teklif_id
) ON public.satinalma_talepleri TO anon;
-- HARİÇ (anon göremez): olusturan_vkn, acik_adres, enlem, boylam
NOTIFY pgrst, 'reload schema';
