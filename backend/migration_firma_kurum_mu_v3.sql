-- ============================================================
-- firma_kurum_mu v3 — belediye şirketleri + savunma/SOE A.Ş. kapsamı (2 Ağu 2026)
-- ------------------------------------------------------------
-- SORUN (kullanıcı): Firma haritası "Kamu kuruluşlarını da göster" toggle'ı kapalıyken bile
-- BELKA, ANFA, İSTON, GESTAŞ (belediye şirketleri) ve ASELSAN, TÜRKSAT, TÜBİTAK (savunma/SOE)
-- panelde görünüyor → toggle "değişmiyor" gibi. Neden: bunlar A.Ş./LTD soneki taşıyor (özel gibi
-- görünür), v2'nin sonek deseni + KİT listesi yakalamıyor. v3 bunları ADLA ekler.
--
-- ⚠️ KISA TOKEN TUZAĞI: "iston" → "piston"u, "anfa"/"belka" başka kelimeleri yanlış yakalayabilir
--   → ayırt edici İFADEYLE sabitlendi ("iston istanbul", "belka ankara", "anfa ankara").
-- ⚠️ TÜPRAŞ EKLENMEDİ: artık ÖZEL (Koç Holding) → kamu saymak YANLIŞ olur.
-- ⚠️ Liste GENİŞLETİLEBİLİR: 81 ilde yüzlerce belediye şirketi var (İZSU/ESHOT/BUSKİ… çoğu
--   "genel müdürlüğü" soneğiyle zaten yakalanıyor). Yeni brand-adlı A.Ş.'ler çıktıkça buraya eklenir.
--
-- CREATE OR REPLACE (imza aynı, IMMUTABLE sql) → il_sektor_firmalar(_dt)/firma_dizin_* çağrı
-- anında ADLA çözer, MV refresh GEREKMEZ, anında etkir.
-- Çalıştır (superuser):
--   docker exec -i supabase-db psql -U supabase_admin -d postgres < backend/migration_firma_kurum_mu_v3.sql
-- ============================================================

CREATE OR REPLACE FUNCTION public.firma_kurum_mu(p_ad text)
RETURNS boolean IMMUTABLE LANGUAGE sql AS $$
  SELECT p_ad IS NOT NULL AND (
    -- Kurumsal SONEK (sonda) — idareler + genel müdürlükler
    public.tr_fold(p_ad) ~ '(mudurlugu|baskanligi|bakanligi|belediyesi|belediye baskanligi|universitesi|rektorlugu|valiligi|kaymakamligi|komutanligi|genel sekreterligi|il ozel idaresi|hastanesi|cezaevi|muftulugu|il saglik mudurlugu|halk sagligi merkezi)$'
    -- Ada göre bilinen devlet tedarikçileri / KİT'ler (sonekle yakalanamayanlar)
    OR public.tr_fold(p_ad) ~ '(devlet malzeme ofisi|ceza infaz kurumu|isyurtlari|isyurdu|posta ve telgraf|kizilay|orman genel mudurlugu|makina ve kimya endustrisi|turkiye seker fabrikalari|sumer holding|turkiye komur isletmeleri|turkiye taskomuru|devlet demiryollari|turkiye radyo televizyon|sosyal guvenlik kurumu|turkiye elektrik|boru hatlari ile petrol|turkiye petrolleri|toprak mahsulleri ofisi|tarim isletmeleri|cay isletmeleri|eti maden|devlet hava meydanlari)'
    -- v3: belediye şirketleri + savunma/SOE A.Ş.'leri (brand-adlı, A.Ş./LTD soneki özel gibi görünür)
    OR public.tr_fold(p_ad) ~ '(aselsan|turksat|havelsan|roketsan|tubitak|tusas|turk havacilik ve uzay|gestas|ispark|izaydas|izbeton|izenerji|belplas|iston istanbul|belka ankara|anfa ankara|isbak istanbul|agac ve peyzaj|kiptas|bimtas|kultur as|hamidiye kaynak)'
  );
$$;
GRANT EXECUTE ON FUNCTION public.firma_kurum_mu(text) TO anon, authenticated, service_role;

NOTIFY pgrst, 'reload schema';

-- Doğrulama (anon):
--   firma_kurum_mu('ASELSAN ELEKTRONİK SANAYİ VE TİCARET ANONİM ŞİRKETİ')          -> t
--   firma_kurum_mu('İSTON İSTANBUL BETON ELEMANLARI VE HAZIR BETON FAB.SAN.VE TİC.A.Ş.') -> t
--   firma_kurum_mu('ANFA ANKARA ALTINPARK İŞL.LTD.ŞTİ.')                            -> t
--   firma_kurum_mu('TÜPRAŞ TÜRKİYE PETROL RAFİNERİLERİ A.Ş')                        -> f (ÖZEL — kamu değil)
--   firma_kurum_mu('PİSTON OTOMOTİV SANAYİ A.Ş.')                                   -> f (iston yanlış eşleşmemeli)
