-- ilanlar: üye (authenticated) SELECT politikası — İKİ hatayı birden çözer (23 Tem 2026).
--
-- SORUN 1 — ARAMA TIMEOUT'U (kullanıcı bildirdi: "canceling statement due to statement timeout"):
--   Üye rolünde ilanlar'ın tek SELECT politikası şuydu:
--     (kaynak IN ('ekap','uluslararasi')) OR (kaynak='ozel' AND durum='aktif' AND auth.role()='authenticated')
--   RLS aktifken Postgres KULLANICI koşulunu (arama_fold LIKE …) indekse İTMİYOR, politika
--   koşulundan sonra FİLTRE olarak uyguluyor. Ölçülen plan: trigram indeksinden 12 satır
--   okumak yerine 539.203 sonuç satırını tarayıp 336.289 kez ilanlar'a bakıyor → 21,3 SANİYE
--   (authenticated'ın statement_timeout'u 8s → 57014 ile ölüyor).
--   Aynı sorgu service_role'de (RLS baypas) 0,17 sn. Yani sorgu/indeks sağlam, suçlu politika.
--   ⚠️ Denendi ve İŞE YARAMADI: effective_cache_size 128MB→8GB + work_mem 24MB. Süre değişmedi.
--
-- SORUN 2 — ÜYELER MİSAFİRDEN AZ GÖRÜYOR (yan bulgu):
--   anon'un politikası `ilanlar_public_read ... USING (true)` — yani misafir HER ŞEYİ görüyor.
--   Üye ise yalnız kaynak IN ('ekap','uluslararasi') görüyor → bu oturumda düzelttiğimiz
--   DMO / Jandarma / ilan.gov kayıtları (1.107 ilan) ÜYELERE GÖRÜNMÜYOR, misafire görünüyor.
--
-- ÇÖZÜM: üyeye anon ile aynı politikayı ver. Yeni ifşa YARATMAZ — anon zaten `true` ile
-- tüm satırları görüyor; bu değişiklik üyeyi misafirle EŞİTLER, üstüne çıkarmaz.
-- 'ozel' kaynaklı satır tabloda HİÇ YOK (ölçüldü: yalnız ilan_gov/jandarma/dmo var),
-- yani eski politikanın koruduğu bir şey de kalmamış.
--
-- ⛔ KOLON MASKELEMESİ ETKİLENMEZ: misafirden gizlenen alanlar (idare, ekap_id, kazanan_firma…)
-- kolon-GRANT ile kapalı, RLS ile değil. Bu migration onlara DOKUNMAZ.
CREATE POLICY ilanlar_uye_okur ON public.ilanlar
    FOR SELECT TO authenticated
    USING (true);

NOTIFY pgrst, 'reload schema';
