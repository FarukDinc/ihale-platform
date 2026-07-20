-- =============================================================================
-- migration_satinalma_revoke.sql — YAPILACAKLAR #8 (20 Tem 2026)
-- satinalma_talepleri.olusturan_user_id anon ifşasının kapatılması.
--
-- ARKA PLAN: migration_rfq_anon_kolon.sql (#18) hassas kolonları (olusturan_vkn,
-- acik_adres, enlem, boylam) anon'dan doğru kapattı ama olusturan_user_id'yi
-- GRANT listesinde bıraktı — çünkü ozel-ihale-detay.html:265 guvenliKolonlar
-- dizesi kolonu anon select'ine sabit yazıyordu (tek başına REVOKE sayfayı
-- "İhale bulunamadı"ya düşürürdü). Frontend düzeltmesi bu migration'la BİRLİKTE
-- geldi: guvenliKolonlar'dan olusturan_user_id çıkarıldı (anon'da user=null →
-- isOwner dalı zaten çalışmaz, kolona client'ta ihtiyaç yok).
--
-- ⚠️ SIRA ŞART: ÖNCE frontend deploy (ozel-ihale-detay.html), SONRA bu migration.
--    Ters sıra = eski HTML hâlâ kolonu select ederken grant kalkar → anon'a 42501
--    → sayfa misafirde "İhale bulunamadı" basar.
--
-- KARAR — authenticated'dan REVOKE EDİLMEDİ (bilinçli):
--   * ozel-ihale-detay.html giriş dalı select('*') kullanır; PostgREST '*' tüm
--     kolonlarda yetki ister → herhangi bir kolon authenticated'dan kalkarsa
--     sayfa girişli kullanıcıda da kırılır.
--   * ihalelerim.html:140 .eq('olusturan_user_id', user.id) filtreler — WHERE'de
--     kullanmak da SELECT yetkisi ister (bkz. anon-maske kök neden C dersi).
--   * isOwner UI dallanması client'ta bu kolonla yapılır; asıl güvenlik zaten
--     RLS'te (talep_sahibi_gunceller, teklif_gizli_okur — auth.uid() tabanlı).
--   * UUID'nin authenticated'a görünmesi pivot vermez: kullanici_profiller ve
--     tedarikci_teklifleri başka kullanıcı için RLS ile boş döner.
--
-- RLS/RPC ETKİLENMEZ: policy ifadeleri ve SECURITY DEFINER fonksiyonlar
-- (bildirim_uret vb.) çağıranın kolon yetkisinden bağımsız çalışır.
-- =============================================================================

-- Önce temiz REVOKE, sonra dar GRANT (kolon-GRANT'lar toplanır; eski listeyi
-- sıfırlamadan yeni liste vermek olusturan_user_id'yi açık bırakırdı).
REVOKE SELECT ON public.satinalma_talepleri FROM anon;
GRANT SELECT (
  id, olusturan_firma, baslik, aciklama, kategori,
  il, ilce, miktar, tahmini_bedel, para_birimi, son_teklif_tarihi,
  durum, olusturulma, kazanan_teklif_id
) ON public.satinalma_talepleri TO anon;
-- HARİÇ (anon göremez): olusturan_user_id, olusturan_vkn, acik_adres, enlem, boylam
-- NOT: kazanan_teklif_id anon'da kalıyor — opak UUID, tedarikci_teklifleri anon'a
-- zaten kapalı (grant yok + RLS) → pivot yolu yok; detay sayfası select'i onu içeriyor.

NOTIFY pgrst, 'reload schema';

-- =============================================================================
-- DOĞRULAMA — uygulamadan sonra (ANON key ile curl, service ile değil):
--   42501 BEKLENEN (kapandı):
--     /rest/v1/satinalma_talepleri?select=olusturan_user_id&limit=1
--     /rest/v1/satinalma_talepleri?select=id&olusturan_user_id=eq.00000000-0000-0000-0000-000000000000
--       (WHERE'de kullanmak da yetki ister — bu da 42501 olmalı)
--   200 BEKLENEN (bozulmamalı — sayfalar bunlara bağlı):
--     /rest/v1/satinalma_talepleri?select=id,olusturan_firma,baslik,aciklama,kategori,il,ilce,miktar,tahmini_bedel,para_birimi,son_teklif_tarihi,durum,olusturulma,kazanan_teklif_id&limit=1
--     /rest/v1/satinalma_talepleri?select=id,baslik,kategori,tahmini_bedel&durum=eq.acik&limit=1   (harita.html)
--     /rest/v1/satinalma_talepleri?select=id,baslik,kategori,il,miktar,tahmini_bedel,son_teklif_tarihi,durum,olusturan_firma&limit=1   (ozel-ihaleler.html)
--   Sayfa dumanı: GİZLİ SEKMEDE (oturumsuz) ozel-ihale-detay?id=<mevcut-id> aç →
--   kart dolu gelmeli; ayrıca girişli kullanıcıyla aynı sayfa + ihalelerim
--   "Açtıklarım" sekmesi bozulmamalı (authenticated grant'ına dokunulmadı).
-- =============================================================================
