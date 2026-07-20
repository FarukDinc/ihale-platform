-- ============================================================================
-- migration_anon_maske.sql — Misafir (anon) için kilit alan maskeleme, sunucu tarafı
-- (16 Tem 2026, veri-koruma paketi 3/3 — kullanıcı kararı: ihaleciler.com modeli)
--
-- Kural: misafir listeleri ve BAŞLIKLARI görür; kimlik/kilit alanlar göremez:
--   ilanlar          → idare, ekap_id, ikn, ilan_metni, ilan_html, yapay_zeka_ozeti,
--                      arama_fold (içinde idare geçer!), yayinlayan_id
--   ihale_sonuclari  → kazanan_firma(+fold), yuklenici_* (ad/vergi/il/id),
--                      tum_teklifler + ham_json (İÇİNDE TÜM KATILIMCI FİRMALAR!),
--                      ekap_id, ikn, ihale_id
--   yukleniciler     → ad, normalize_ad, arama_fold (ad kopyası), vergi_no, ai_yorum(+tarih)
--   dogrudan_temin_ilanlari → idare, arama_fold (içinde idare geçer!),
--                      dt_ihale_token, dt_idare_token
-- Sayılar/tarihler/il/tür/kategori/bedeller misafire AÇIK (teaser değeri).
-- Belge linkleri (ilanlar.belgeler/ekler/pdf_url) BİLİNÇLİ açık — kullanıcının
-- teklif-hazırlama istisnası; EKAP'a tek tek gider, toplu kopyaya yaramaz.
--
-- Mekanizma: Postgres KOLON-SEVİYESİ GRANT. Tablo-geneli anon SELECT kaldırılır,
-- yalnız izinli kolon listesi GRANT edilir. PostgREST'te anon `select=*` veya
-- izinsiz kolon isteyen sorgu 42501 alır → frontend'ler anon dalında dar kolon
-- listesi kullanır ve '***' çizer (aynı commit'teki sayfa değişiklikleri).
-- NOT: WHERE'de kullanılan kolon için de SELECT yetkisi gerekir → anon idare
-- filtresi/araması da otomatik kapanır (oracle saldırısı yolu yok).
-- authenticated'ın yetkileri DEĞİŞMEZ (tablo-geneli SELECT sürer). RLS aynen.
--
-- Ayrıca: isim döndüren RPC'ler anon'a kapanır (idare_dizin_json deseni —
-- PUBLIC+anon REVOKE ŞART, fonksiyonlar PUBLIC EXECUTE ile doğar):
--   il_sektor_firmalar (firma adları), analiz_pivot (idare/firma grupları),
--   kurum_ozet (idare analizi), rekabet_ozet (top-20 İDARE listesi döner!),
--   ihaleye_uygun_firmalar + _geo (firma önerileri)
-- ve isim içeren MV'lerin anon SELECT'i kapanır (PostgREST MV'leri de servis eder!):
--   idare_ozet_mv, il_sektor_firma_mv
-- Anon'a AÇIK kalan aggregate RPC'ler isim döndürmez: il_sayim, kategori_sayim,
-- il_firma_dagilimi, yuklenici_ozet, sonuc_ozet, il_sektor_ozet, il_rfq_dagilimi,
-- semantik_skor_batch (skor döner; ilanlar'ın İZİNLİ kolonlarını okur → kırılmaz).
--
-- Çalıştır: docker exec -i supabase-db psql -U postgres -d postgres < backend/migration_anon_maske.sql
-- Geri alma: GRANT SELECT ON <tablo> TO anon;  (tablo-geneli yetkiyi geri verir)
-- ============================================================================

BEGIN;

-- ── 1) ilanlar: tablo-geneli anon SELECT → izinli kolon listesi
REVOKE SELECT ON public.ilanlar FROM anon;
GRANT SELECT (
  id, kaynak, baslik, aciklama, il, ulke, tur, usul, durum,
  ilan_tarihi, son_teklif_tarihi, ihale_tarihi, tahmini_bedel, para_birimi,
  hedef_sektorler, gizli_fiyat, goruntulenme, ekap_guncelleme, olusturulma,
  kategori, itiraz_bedeli, yaklasik_maliyet_min, yaklasik_maliyet_max,
  isin_yapilacagi_yer, ihale_yeri, okas, belgeler, ekler, pdf_url,
  esik_katsayi, analiz_tarihi, analiz_pdf_turu, embedding, embedding_guncelleme
) ON public.ilanlar TO anon;

-- ── 2) ihale_sonuclari
REVOKE SELECT ON public.ihale_sonuclari FROM anon;
GRANT SELECT (
  id, ilan_id, kazanan_teklif, kazanan_teklif_farki_yuzde, toplam_teklif_sayisi,
  en_dusuk_teklif, en_yuksek_teklif, ortalama_teklif, sonuc_tarihi, olusturulma,
  sozlesme_bedeli, sozlesme_tarihi, tenzilat_yuzde, yaklasik_maliyet,
  katilimci_sayisi, gecerli_teklif_sayisi, is_baslama_tarihi, is_bitis_tarihi,
  is_suresi_gun, karar_tarihi, sonuc_tur, scrape_tarihi, kisim_no
) ON public.ihale_sonuclari TO anon;

-- ── 3) yukleniciler
REVOKE SELECT ON public.yukleniciler FROM anon;
GRANT SELECT (
  id, il, toplam_sozlesme_sayisi, toplam_ciro, ilk_sozlesme_tarihi,
  son_sozlesme_tarihi, sektor, guncellendi, ortak_girisim, kategori
) ON public.yukleniciler TO anon;

-- ── 4) dogrudan_temin_ilanlari: idare + ondan TÜRETİLEN kolonlar + tokenlar maskeli.
--    Token'lar 18 Tem'de eklendi (migration_dt_kazanan.sql) — EKAP'ın CAPTCHA-korumalı
--    detay sayfasına dahili erişim anahtarları, frontend'in hiç ihtiyaç duymadığı;
--    açık kalırsa herkes bizim scraper'ımızın E10/E11 keşfini kopyalayıp kendi
--    toplu-erişimini kurabilirdi (dt_no/idare gibi "teaser" veri değil, saf altyapı).
--
--    arama_fold 20 Tem'de eklendi (migration_dt_arama.sql) ve KARA LİSTEYE GİRMEK
--    ZORUNDA: tr_fold(baslik || ' ' || idare) içerir, yani maskelenen idare adının
--    katlanmış kopyasıdır. anon'a açılırsa idare adı trigram ILIKE'ıyla harf harf
--    geri okunabilir (oracle) — ilanlar.arama_fold'un anon'a kapalı olmasıyla
--    birebir aynı gerekçe (yukarıdaki başlık, satır 7).
--
-- ── ⚠️ NEDEN BU BLOK KARA LİSTE (ve bedeli) ─────────────────────────────────
--    Diğer üç tablo (ilanlar/ihale_sonuclari/yukleniciler) BEYAZ liste kullanıyor;
--    DT dinamik kara liste kullanıyor çünkü tablo geniş ve elle yazılan bir beyaz
--    listede tek kolon atlanırsa misafir sayfası 42501 ile TÜMDEN ölür
--    (migration_dt_token_authenticated.sql:19-23'teki gerekçe).
--    Bedeli: kara liste AÇIK YÖNE ARIZALANIR — SONRADAN eklenen her kolon bu
--    dosya yeniden koşturulduğunda anon'a SESSİZCE açılır. Tam olarak bu tuzak
--    arama_fold'da işledi: migration_dt_token_authenticated.sql:45-49'daki kalıcı
--    bakım notu "yeni kolon eklerken bu dosyayı ve migration_anon_maske.sql'i
--    TEKRAR çalıştırın" diyor → projenin KENDİ yordamı maskeyi delerdi.
--    Bu yüzden aşağıya BEKÇİ eklendi: sınıflandırılmamış bir `*_fold` kolonu
--    görürse migration COMMIT ETMEZ. `*_fold` özellikle seçildi çünkü bunlar
--    tanım gereği başka kolonların kopyasıdır ve hangi kaynaktan türediklerini
--    adlarından anlamak imkânsızdır; migration_dt_arama.sql:54 zaten olası bir
--    `idare_fold` kolonundan söz ediyor — açık kalsa aynı delik tekrarlanırdı.
DO $$
DECLARE
  kolonlar text;
  -- anon'a KAPALI kolonlar (kimlik/altyapı + onlardan türetilmiş kopyalar)
  anon_yasak        text[] := ARRAY['idare', 'dt_ihale_token', 'dt_idare_token', 'arama_fold'];
  -- anon'a bilinçli AÇIK bırakılmış türev kolonlar. baslik_fold = tr_fold(baslik);
  -- baslik zaten misafire açık olduğu için ek ifşa yok (migration_dt_arama.sql:41-44).
  anon_serbest_fold text[] := ARRAY['baslik_fold'];
  siniflanmamis     text;
BEGIN
  -- BEKÇİ: her `*_fold` kolonu ya yasak ya serbest listesinde OLMALI.
  -- NOT: column_name `sql_identifier` (name üzerinde domain) — text[] ile
  -- karşılaştırmadan önce açıkça ::text'e indiriliyor.
  SELECT string_agg(column_name::text, ', ' ORDER BY column_name::text)
    INTO siniflanmamis
  FROM information_schema.columns
  WHERE table_schema = 'public' AND table_name = 'dogrudan_temin_ilanlari'
    AND right(column_name::text, 5) = '_fold'
    AND NOT (column_name::text = ANY (anon_yasak))
    AND NOT (column_name::text = ANY (anon_serbest_fold));

  IF siniflanmamis IS NOT NULL THEN
    RAISE EXCEPTION
      'ABORT: siniflandirilmamis fold kolonu (%). Icinde idare/kimlik geciyorsa anon_yasak, gecmiyorsa anon_serbest_fold listesine EKLEYIN — aksi halde anon a sessizce acilir.',
      siniflanmamis;
  END IF;

  SELECT string_agg(quote_ident(column_name::text), ', ')
    INTO kolonlar
  FROM information_schema.columns
  WHERE table_schema = 'public' AND table_name = 'dogrudan_temin_ilanlari'
    AND NOT (column_name::text = ANY (anon_yasak));

  IF kolonlar IS NULL THEN
    RAISE EXCEPTION 'ABORT: DT kolon listesi bos cikti — tablo adi yanlis olabilir';
  END IF;

  EXECUTE 'REVOKE SELECT ON public.dogrudan_temin_ilanlari FROM anon';
  EXECUTE format('GRANT SELECT (%s) ON public.dogrudan_temin_ilanlari TO anon', kolonlar);
END $$;

-- ── 5) İsim döndüren RPC'ler anon'a kapalı
REVOKE EXECUTE ON FUNCTION public.il_sektor_firmalar(text[], text, int) FROM PUBLIC, anon;
REVOKE EXECUTE ON FUNCTION public.analiz_pivot(text, text, text, text, text, int) FROM PUBLIC, anon;
REVOKE EXECUTE ON FUNCTION public.kurum_ozet(text) FROM PUBLIC, anon;
REVOKE EXECUTE ON FUNCTION public.rekabet_ozet(text, text, text) FROM PUBLIC, anon;
GRANT EXECUTE ON FUNCTION public.il_sektor_firmalar(text[], text, int) TO authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.analiz_pivot(text, text, text, text, text, int) TO authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.kurum_ozet(text) TO authenticated, service_role;
GRANT EXECUTE ON FUNCTION public.rekabet_ozet(text, text, text) TO authenticated, service_role;

-- ihaleye_uygun_firmalar imzaları değişken olabilir — pg_proc'tan bulup kapat
DO $$
DECLARE
  f record;
BEGIN
  FOR f IN
    SELECT p.oid::regprocedure AS imza
    FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace
    WHERE n.nspname = 'public' AND p.proname IN ('ihaleye_uygun_firmalar', 'ihaleye_uygun_firmalar_geo')
  LOOP
    EXECUTE format('REVOKE EXECUTE ON FUNCTION %s FROM PUBLIC, anon', f.imza);
    EXECUTE format('GRANT EXECUTE ON FUNCTION %s TO authenticated, service_role', f.imza);
  END LOOP;
END $$;

-- ── 6) İsim içeren MV'ler anon'a kapalı (PostgREST MV'leri REST'te servis eder)
REVOKE SELECT ON public.idare_ozet_mv FROM anon;
REVOKE SELECT ON public.il_sektor_firma_mv FROM anon;

COMMIT;

NOTIFY pgrst, 'reload schema';

-- ── Kontroller ──────────────────────────────────────────────
SET ROLE anon;
DO $$
BEGIN
  -- izinli kolonlar çalışmalı
  PERFORM id, baslik, il FROM public.ilanlar LIMIT 1;
  RAISE NOTICE 'OK: anon ilanlar(id,baslik,il) okuyor';
  BEGIN
    PERFORM idare FROM public.ilanlar LIMIT 1;
    RAISE EXCEPTION 'HATA: anon ilanlar.idare okuyabiliyor!';
  EXCEPTION WHEN insufficient_privilege THEN RAISE NOTICE 'OK: ilanlar.idare anon-kapali'; END;
  BEGIN
    PERFORM kazanan_firma FROM public.ihale_sonuclari LIMIT 1;
    RAISE EXCEPTION 'HATA: anon kazanan_firma okuyabiliyor!';
  EXCEPTION WHEN insufficient_privilege THEN RAISE NOTICE 'OK: ihale_sonuclari.kazanan_firma anon-kapali'; END;
  BEGIN
    PERFORM ad FROM public.yukleniciler LIMIT 1;
    RAISE EXCEPTION 'HATA: anon yukleniciler.ad okuyabiliyor!';
  EXCEPTION WHEN insufficient_privilege THEN RAISE NOTICE 'OK: yukleniciler.ad anon-kapali'; END;
  BEGIN
    PERFORM idare FROM public.dogrudan_temin_ilanlari LIMIT 1;
    RAISE EXCEPTION 'HATA: anon DT.idare okuyabiliyor!';
  EXCEPTION WHEN insufficient_privilege THEN RAISE NOTICE 'OK: DT.idare anon-kapali'; END;
  BEGIN
    PERFORM dt_ihale_token FROM public.dogrudan_temin_ilanlari LIMIT 1;
    RAISE EXCEPTION 'HATA: anon DT.dt_ihale_token okuyabiliyor!';
  EXCEPTION WHEN insufficient_privilege THEN RAISE NOTICE 'OK: DT.dt_ihale_token anon-kapali'; END;
  -- DT fold kolonları: migration_dt_arama.sql uygulanmamış kurulumda YOKlar, o yüzden
  -- varlık kontrolü pg_catalog'dan yapılıyor. information_schema KULLANILAMAZ: o view
  -- rolün yetkisi olmayan kolonu GİZLER → arama_fold delik olsa bile "yok" görünür ve
  -- kontrol sessizce atlanırdı (tam da yakalamak istediğimiz durum).
  IF EXISTS (SELECT 1 FROM pg_attribute
              WHERE attrelid = 'public.dogrudan_temin_ilanlari'::regclass
                AND attname = 'arama_fold' AND attnum > 0 AND NOT attisdropped) THEN
    BEGIN
      PERFORM arama_fold FROM public.dogrudan_temin_ilanlari LIMIT 1;
      RAISE EXCEPTION 'HATA: anon DT.arama_fold okuyabiliyor — icinde idare geciyor, MASKE DELINDI!';
    EXCEPTION WHEN insufficient_privilege THEN RAISE NOTICE 'OK: DT.arama_fold anon-kapali'; END;
  END IF;
  -- POZİTİF yön: baslik_fold anon'a AÇIK kalmalı, yoksa misafir DT araması 42501 alır.
  IF EXISTS (SELECT 1 FROM pg_attribute
              WHERE attrelid = 'public.dogrudan_temin_ilanlari'::regclass
                AND attname = 'baslik_fold' AND attnum > 0 AND NOT attisdropped) THEN
    PERFORM baslik_fold FROM public.dogrudan_temin_ilanlari LIMIT 1;
    RAISE NOTICE 'OK: DT.baslik_fold anon-acik (misafir aramasi calisir)';
  END IF;
  BEGIN
    PERFORM * FROM public.il_sektor_firma_mv LIMIT 1;
    RAISE EXCEPTION 'HATA: anon il_sektor_firma_mv okuyabiliyor!';
  EXCEPTION WHEN insufficient_privilege THEN RAISE NOTICE 'OK: il_sektor_firma_mv anon-kapali'; END;
  -- anon'a açık kalan aggregate'ler kırılmamalı
  PERFORM public.il_sayim();
  PERFORM public.il_sektor_ozet();
  PERFORM public.sonuc_ozet();
  RAISE NOTICE 'OK: anon aggregate RPCleri (il_sayim/il_sektor_ozet/sonuc_ozet) calisiyor';
END $$;
RESET ROLE;

SET ROLE authenticated;
SELECT 'OK: authenticated ilanlar.idare = ' || (SELECT count(idare) FROM public.ilanlar WHERE idare IS NOT NULL LIMIT 1)::text AS auth_testi_1;
SELECT 'OK: authenticated rekabet_ozet toplam = ' || (public.rekabet_ozet(NULL,NULL,NULL)->>'toplam') AS auth_testi_2;
RESET ROLE;
