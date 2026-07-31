-- ============================================================
-- firma_kurum_mu v2 — KİT (devlet iktisadi teşekkülü) kapsamı (31 Tem 2026)
-- ------------------------------------------------------------
-- Denetim (anon curl): "müdürlüğü" sonekiyle bitmeyen büyük KAMU tedarikçileri kaçıyordu —
-- devlet A.Ş.'leri / "Kurumu" ile bitenler özel A.Ş.'den SONEKLE ayırt edilemez → ada göre
-- (DMO/PTT deseni gibi) küratörlü liste eklenir. "Kurumu$" soneki BİLEREK eklenmedi: özel
-- "… Eğitim Kurumu" gibi yanlış pozitif riski var; yalnız BİLİNEN devlet KİT adları eklenir.
--
-- CREATE OR REPLACE (imza aynı) → il_sektor_firmalar(_dt) + firma_dizin_dt/birlikte çağırdıkları
-- yerde ADLA çözer, yeniden kurmaya gerek YOK. Yanlış pozitif kontrolü: eklenen adlar özel
-- firmalarla çakışmayacak kadar spesifik (ör. "türkiye şeker fabrikalari" ≠ "şeker piliç").
--
-- Çalıştır (superuser):
--   docker exec -i supabase-db psql -U supabase_admin -d postgres < backend/migration_firma_kurum_mu_v2.sql
-- ============================================================

CREATE OR REPLACE FUNCTION public.firma_kurum_mu(p_ad text)
RETURNS boolean IMMUTABLE LANGUAGE sql AS $$
  SELECT p_ad IS NOT NULL AND (
    -- Kurumsal SONEK (sonda) — idareler + genel müdürlükler
    public.tr_fold(p_ad) ~ '(mudurlugu|baskanligi|bakanligi|belediyesi|belediye baskanligi|universitesi|rektorlugu|valiligi|kaymakamligi|komutanligi|genel sekreterligi|il ozel idaresi|hastanesi|cezaevi|muftulugu|il saglik mudurlugu|halk sagligi merkezi)$'
    -- Ada göre bilinen devlet tedarikçileri / KİT'ler (sonekle yakalanamayanlar)
    OR public.tr_fold(p_ad) ~ '(devlet malzeme ofisi|ceza infaz kurumu|isyurtlari|isyurdu|posta ve telgraf|kizilay|orman genel mudurlugu|makina ve kimya endustrisi|turkiye seker fabrikalari|sumer holding|turkiye komur isletmeleri|turkiye taskomuru|devlet demiryollari|turkiye radyo televizyon|sosyal guvenlik kurumu|turkiye elektrik|boru hatlari ile petrol|turkiye petrolleri|toprak mahsulleri ofisi|tarim isletmeleri|cay isletmeleri|eti maden|devlet hava meydanlari)'
  );
$$;
GRANT EXECUTE ON FUNCTION public.firma_kurum_mu(text) TO anon, authenticated, service_role;

NOTIFY pgrst, 'reload schema';

-- Doğrulama (anon):
--   firma_kurum_mu('MAKİNA VE KİMYA ENDÜSTRİSİ ANONİM ŞİRKETİ')       -> t
--   firma_kurum_mu('TÜRKİYE KÖMÜR İŞLETMELERİ KURUMU')                -> t
--   firma_kurum_mu('ŞEKER PİLİÇ VE YEM SANAYİ TİCARET ANONİM ŞİRKETİ')-> f (özel, çakışmamalı)
