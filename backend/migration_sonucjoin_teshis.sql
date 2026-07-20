-- =============================================================================
-- İhaleGlobal — ilanlar_sonuc bozuk LEFT JOIN TEŞHİSİ (SALT-OKUNUR)
-- YAPILACAKLAR #9 — 20 Tem 2026
--
-- BİLİNEN: view 'i.ekap_id = s.ekap_id' ile join ediyor; 356.904 ilan satırının
-- TAMAMINDA sonuç tarafı NULL (18 Tem anon_maske_v2 denetimi: yuklenici_ad,
-- sozlesme_bedeli, sonuc_tur -> count 0).
--
-- KOD TABANINDAN ÇIKAN HİPOTEZLER:
--
--   H1 (EN GÜÇLÜ — kök neden): ihale_sonuclari.ekap_id ~%100 NULL.
--       Tabloyu dolduran tek canlı yazar ekap_sonuc_backfill.py ve bu script
--       ekap_id'yi HİÇ yazmıyor — upsert anahtarı (ilan_id, kisim_no), ilan_id =
--       ilanlar.id UUID FK (bkz. script başlık yorumu: "migration_sonuc_schema.sql
--       hiç çalıştırılmamış; gerçek şema ilan_id bazlı"). Tasarım B kolonları
--       (ikn, yuklenici_ad, sozlesme_bedeli...) dolduruluyor ama ekap_id asla.
--       SQL'de NULL = NULL asla TRUE olmadığı için LEFT JOIN 0 eşleşir.
--       Kanıt-1: canlı RPC'ler zaten 'i.id = s.ilan_id' kullanıyor ve çalışıyor
--       (migration_analiz_rpc.sql:60, migration_yuklenici_agg.sql:81).
--
--   H2 (yedek anahtar): s.ikn dolu (backfill yazıyor) → i.ikn = s.ikn de eşleşir;
--       ama ilanlar.ikn %100 dolu değil (356.725/356.904) ve tekilliği garanti
--       değil — ilan_id FK varken gereksiz/riskli.
--
--   H3 (görev ipucundaki prefix hipotezi — TALİ): DMO 'DMO-<no>', Jandarma
--       'JND-<psn>' prefixli ekap_id yazar (dmo_scraper.py:91, jandarma_scraper.py:100),
--       EKAP ise IKN ('yyyy/nnnnnn') ya da sayısal id yazar. s.ekap_id dolu OLSAYDI
--       bile DMO/JND satırları eşleşmezdi; ama EKAP kaynaklı çoğunluk eşleşirdi —
--       yani prefix tek başına 0/356.904'ü AÇIKLAYAMAZ. H1 asıl neden.
--
-- ÇALIŞTIRMA (VDS):
--   docker exec -i supabase-db psql -U postgres -d postgres \
--     < backend/migration_sonucjoin_teshis.sql
-- TÜM SORGULAR SALT-OKUNUR (yalnız SELECT; DDL/DML yok).
-- =============================================================================

-- [T0] Prod'daki gerçek view tanımı — kod tabanındakiyle aynı mı?
-- BEKLENEN: "... FROM ilanlar i LEFT JOIN ihale_sonuclari s ON i.ekap_id = s.ekap_id"
SELECT pg_get_viewdef('public.ilanlar_sonuc'::regclass, true) AS view_tanimi;

-- [T1] ihale_sonuclari anahtar doluluğu — H1'in ana testi.
-- BEKLENEN (H1 doğruysa):
--   toplam        ≈ 538.064+ (9 Tem sayımı 288.728 tek + 249.336 çok kısım; bugün artmış olabilir)
--   ekap_id_dolu  ≈ 0        (ekap_sonuc_scraper.py hiç koşmadıysa tam 0; birkaç deneme satırı olabilir)
--   ilan_id_dolu  ≈ toplam   (eski ~15 legacy satır dahil — eski şema da ilan_id bazlıydı)
--   ikn_dolu      ≈ toplam   (backfill yazıyor)
SELECT count(*)             AS toplam,
       count(ekap_id)       AS ekap_id_dolu,
       count(ilan_id)       AS ilan_id_dolu,
       count(ikn)           AS ikn_dolu,
       count(yuklenici_ad)  AS yuklenici_ad_dolu,
       count(kazanan_firma) AS kazanan_firma_dolu
FROM public.ihale_sonuclari;

-- [T2] ekap_id dolu satır VARSA formatını gör.
-- BEKLENEN (H1 doğruysa): 0 satır. Satır dönerse format IKN mi / sayısal id mi
-- / prefixli mi bak — fix'in join'ine ek COALESCE dalı gerekip gerekmediğini belirler.
SELECT ekap_id, ikn, (ilan_id IS NOT NULL) AS ilan_id_var, scrape_tarihi
FROM public.ihale_sonuclari
WHERE ekap_id IS NOT NULL
LIMIT 20;

-- [T3] Mevcut (bozuk) join'in eşleşme sayısı — kontrol grubu.
-- BEKLENEN: 0
SELECT count(*) AS eski_join_eslesme
FROM public.ilanlar i
JOIN public.ihale_sonuclari s ON i.ekap_id = s.ekap_id;

-- [T4] H1 testi: ilan_id join eşleşmesi.
-- BEKLENEN: eslesen_sonuc_satiri ≈ T1.toplam (tamamına yakını eşleşmeli);
--   eslesen_ilan ≈ 330-340K (288.728 tek-lot ihale + ~46K çok-lot ihale).
SELECT count(*)                  AS eslesen_sonuc_satiri,
       count(DISTINCT s.ilan_id) AS eslesen_ilan
FROM public.ihale_sonuclari s
JOIN public.ilanlar i ON i.id = s.ilan_id;

-- [T5] Öksüz sonuç satırı (ilanlar'da karşılığı olmayan ilan_id).
-- BEKLENEN: 0 (FK varsa garantili). >0 çıkarsa FK yok demektir; fix'i etkilemez
-- (view LEFT JOIN'i ilanlar yönünden), ama ayrı temizlik maddesi açılır.
SELECT count(*) AS oksuz_sonuc
FROM public.ihale_sonuclari s
LEFT JOIN public.ilanlar i ON i.id = s.ilan_id
WHERE s.ilan_id IS NOT NULL AND i.id IS NULL;

-- [T6] H2 testi (kıyas): ikn join eşleşmesi.
-- BEKLENEN: T4'e yakın ama daha küçük ya da (ikn mükerrerse) ŞİŞKİN.
-- T4 ile aynı büyüklükteyse bile ilan_id tercih edilir (FK + UUID, format riski yok).
SELECT count(*) AS ikn_join_eslesme
FROM public.ilanlar i
JOIN public.ihale_sonuclari s ON i.ikn = s.ikn;

-- [T7] ilanlar.ikn tekilliği — H2'nin neden riskli olduğunun kanıtı.
-- BEKLENEN: az sayıda mükerrer ikn (dedup anahtarı ekap_id, ikn değil —
-- kompakt satır + DT mükerrerleri). Mükerrer >0 ise ikn join satır şişirir.
SELECT ikn, count(*) AS adet
FROM public.ilanlar
WHERE ikn IS NOT NULL AND ikn <> ''
GROUP BY ikn
HAVING count(*) > 1
ORDER BY adet DESC
LIMIT 10;

-- [T8] H3 belgeleme: ilanlar.ekap_id format dağılımı.
-- BEKLENEN: büyük çoğunluk 'IKN (yyyy/n)'; 'DMO-prefix' ve 'JND-prefix' azınlık;
-- 'salt rakam' (EKAP dahili id fallback) az sayıda.
SELECT CASE
         WHEN ekap_id LIKE 'DMO-%'            THEN 'DMO-prefix'
         WHEN ekap_id LIKE 'JND-%'            THEN 'JND-prefix'
         WHEN ekap_id ~ '^[0-9]{4}/[0-9]+$'   THEN 'IKN (yyyy/n)'
         WHEN ekap_id ~ '^[0-9]+$'            THEN 'salt rakam (EKAP ihaleId fallback)'
         ELSE 'diger'
       END      AS format,
       count(*) AS adet
FROM public.ilanlar
GROUP BY 1
ORDER BY adet DESC;

-- [T9] Düzeltilmiş view'ın satır sayısı önizlemesi (kardinalite değişimi).
-- BEKLENEN: 356.904 + (çok kısımlı ihalelerin EKSTRA kısım satırları ≈ 249K - 46K)
-- ≈ 560K civarı. NOT: yeni join ilan başına değil KISIM başına satır döndürür —
-- fix bu yüzden kisim_no + lot_sayisi kolonlarını da dışarı veriyor
-- (tüketici 'lot_sayisi=1' tenzilat kuralını uygulayabilsin).
SELECT count(*) AS yeni_view_satir
FROM public.ilanlar i
LEFT JOIN public.ihale_sonuclari s ON s.ilan_id = i.id;

-- [T10] lot_sayisi doluluğu — fix view bu kolonu dışarı verecek.
-- BEKLENEN: lot_null 0'a yakın (gece UPDATE'i run_scraper.sh'e henüz eklenmediyse
-- 18 Tem sonrası scrape edilen satırlarda NULL görülebilir — bu ayrı açık madde).
-- Bu sorgu HATA verirse lot_sayisi kolonu prod'da yok demektir → fix'ten o kolonu çıkar.
SELECT count(*) FILTER (WHERE lot_sayisi IS NULL) AS lot_null,
       count(*) FILTER (WHERE lot_sayisi = 1)     AS tek_kisim,
       count(*) FILTER (WHERE lot_sayisi > 1)     AS cok_kisim
FROM public.ihale_sonuclari;

-- [T11] Mevcut GRANT durumu — fix'in AYNEN koruması gereken güvenlik hali.
-- BEKLENEN: authenticated -> SELECT VAR; anon -> HİÇBİR SATIR YOK
-- (migration_anon_maske_v2 REVOKE'u, 18 Tem). anon satırı görünürse ÖNCE
-- anon_maske_v2'nin uygulandığını doğrula — fix bu durumu değiştirmemeli.
SELECT grantee, privilege_type
FROM information_schema.role_table_grants
WHERE table_schema = 'public' AND table_name = 'ilanlar_sonuc'
ORDER BY grantee, privilege_type;
