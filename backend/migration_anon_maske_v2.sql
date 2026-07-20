-- =============================================================================
-- migration_anon_maske_v2.sql — maskeleme kapsamına alınmamış nesneleri kapatır
-- =============================================================================
--
-- KAYNAK: 18 Tem 2026 çok-ajanlı anon denetimi. 61 nesne tarandı, her bulgu
-- bağımsız bir ajan tarafından çürütülmeye çalışıldı; aşağıdakiler ayakta kaldı.
-- Bu dosya migration_dt_anon_fix.sql'den AYRI: orası benim yeni açtığım delikleri
-- kapatır, burası ÖNCEDEN VAR OLAN ve migration_anon_maske.sql kapsamına hiç
-- girmemiş nesneleri kapatır.
--
-- İKİ AYRI KÖK NEDEN VAR — ikisini karıştırmayın:
--
--   (A) VARSAYILAN AYRICALIK KALINTISI
--       ALTER DEFAULT PRIVILEGES ... GRANT ALL ON TABLES TO anon yürürlükte olduğu
--       için, migration_anon_maske.sql'de ADI GEÇMEYEN her tablo doğuştan anon'a
--       tamamen açık kalır. Maskeleme "opt-in" — unutulan tablo korunmaz.
--       -> kamu_ihaleleri, kik_kararlar
--
--   (B) VIEW SAHİP-YETKİSİ (bu daha sinsi)
--       PostgreSQL view'ları varsayılan olarak security_invoker DEĞİL, yani view'i
--       sorgulayan değil view'in SAHİBİ yetkisiyle çalışır. Bu yüzden taban tablodaki
--       kolon-bazlı REVOKE'lar view üzerinden HİÇ uygulanmaz. ilanlar tablosunda
--       maskeleme kusursuz çalışırken aynı kolonlar ilanlar_sonuc view'ından
--       serbestçe okunabiliyordu.
--       -> ilanlar_sonuc
--
-- =============================================================================

BEGIN;

-- ---------------------------------------------------------------------------
-- 1) ilanlar_sonuc — KRİTİK. 356.904 satır. (Kök neden B)
--
--    Kanıt (anon key ile, düzeltme öncesi):
--      /rest/v1/ilanlar?select=idare        -> 401 42501   (taban tablo: doğru maskeli)
--      /rest/v1/ilanlar_sonuc?select=idare  -> 200         (view: arka kapı)
--      ekap_id ve ikn için de aynı; ?select=* -> 200, 23 kolon
--      count=exact -> 356904 satır; idare dolu 356903, ekap_id 356904, ikn 356725
--
--    Frontend kullanımı SIFIR: hiçbir .html/.js dosyası ilanlar_sonuc'u sorgulamıyor
--    (yalnızca .sql dosyalarında geçiyor) — bu yüzden düz REVOKE hiçbir sayfayı bozmaz.
--    authenticated erişimi korunuyor.
--
--    NOT: view'in LEFT JOIN'i (i.ekap_id = s.ekap_id) hiç eşleşmiyor; ihale_sonuclari
--    kaynaklı tüm kolonlar 356.904 satırın tamamında NULL (yuklenici_ad, sozlesme_bedeli,
--    sonuc_tur -> count 0). Yani o kolonlardan fiili ifşa yoktu. Bu AYRI bir hata ve
--    bu migration onu düzeltmiyor — YAPILACAKLAR'a ayrı madde olarak yazıldı.
-- ---------------------------------------------------------------------------
REVOKE SELECT ON public.ilanlar_sonuc FROM anon;

-- ---------------------------------------------------------------------------
-- 2) kik_kararlar — ORTA. 97 satır. (Kök neden A)
--
--    ham_veri (jsonb, 25 anahtar) anon'a tamamen açıktı. Frontend bu kolonu HİÇ
--    seçmiyor: kik-kararlar.html:435 tam olarak aşağıdaki 10 kolonu istiyor.
--    Yani ham_veri, uygulamanın hiç ihtiyaç duymadığı halde açık duran bir yüzeydi.
--
--    Şiddet neden 'kritik' değil: ham_veri içinde uzmanTCKN alanı 97/97 satırda BOŞ;
--    karar/inceleme/itiraz metinleri de boş. En hassas içerik fiilen ifşa olmuyordu.
--    idare ve ihale_konusu BİLEREK misafire gösteriliyor (sayfada oturum dalı yok),
--    o yüzden GRANT listesinde kalıyorlar — düz REVOKE sayfayı bozardı.
-- ---------------------------------------------------------------------------
REVOKE SELECT ON public.kik_kararlar FROM anon;
GRANT SELECT (
  id, karar_no, karar_tarihi, karar_turu, sonuc, baslik, idare, ihale_konusu,
  kaynak_url, ozet
) ON public.kik_kararlar TO anon;

-- ---------------------------------------------------------------------------
-- 3) kamu_ihaleleri — YÜKSEK. 172 satır. (Kök neden A)
--
--    Tablo tamamen anon'a açıktı; anon idare üzerinde FİLTRELEYEBİLİYORDU da
--    (?idare=not.is.null -> 206, 172 satır).
--
--    GRANT listesi ozel-ihaleler.html:389-397'den birebir türetildi — hem SELECT
--    edilen hem FİLTRELENEN her kolon dahil:
--      select : baslik, idare, il, alt_kaynak, tur, son_teklif_tarihi, orijinal_url
--      filtre : kaynak (eq), il (eq), son_teklif_tarihi (gte/lt/lte + order),
--               baslik + idare (or/ilike)
--    PostgreSQL WHERE'de kullanılan kolon için de SELECT yetkisi ister; filtre
--    kolonlarını listeden çıkarmak sayfayı 42501 ile kırar.
--
--    KAPATILANLAR: ekap_referans, talep_no, kaynak_id — üçü de yalnızca dahili
--    eşleştirme/dedup anahtarı, frontend hiçbirini kullanmıyor.
--
--    !! AÇIK KARAR — 'idare' BİLEREK AÇIK BIRAKILDI !!
--    Politika (bkz. hafıza veri-disa-aktarim-yasagi) idare'yi misafire kapalı sayar
--    ve ilanlar tablosunda kapalıdır. Ama ozel-ihaleler.html misafire açık bir sayfa
--    ve Kalkınma Ajansı listesinde idare adını hem gösteriyor hem aratıyor; kapatmak
--    sayfayı işlevsiz bırakır. Bu 172 satır EKAP korpusu değil, KA duyuruları —
--    farklı bir veri kümesi. Politikaya birebir uymak isteniyorsa yapılacak iş
--    REVOKE değil, sayfaya uyeMi dalı + dar select eklemektir (YAPILACAKLAR'da madde).
-- ---------------------------------------------------------------------------
REVOKE SELECT ON public.kamu_ihaleleri FROM anon;
GRANT SELECT (
  id, kaynak, alt_kaynak, baslik, aciklama, idare, il, tur, kategori,
  ilan_tarihi, son_teklif_tarihi, orijinal_url, olusturulma, guncellenme
) ON public.kamu_ihaleleri TO anon;

COMMIT;

NOTIFY pgrst, 'reload schema';

-- =============================================================================
-- KAPSAM DIŞI BIRAKILANLAR (bilinçli — denetimde çıktı ama burada düzeltilmiyor)
-- =============================================================================
--
-- satinalma_talepleri.olusturan_user_id — DÜŞÜK. Anon'a açık ama:
--   * gerçek hassas kolonlar (olusturan_vkn, acik_adres, enlem, boylam) 42501 ile
--     doğru şekilde kapalı — migration_rfq_anon_kolon.sql doğru kalıbı uygulamış,
--     bu kolon GRANT listesine BİLEREK yazılmış (kök neden A değil)
--   * UUID'den isme/e-postaya pivot yolu YOK (kullanici_profiller ve
--     tedarikci_teklifleri anon'a RLS ile boş dönüyor — test edildi)
--   * anon'a görünen toplam 3 satır
--   Düzeltmesi TEK BAŞINA YAPILAMAZ: ozel-ihale-detay.html:265'teki guvenliKolonlar
--   dizesi bu kolonu anon select'ine sabit yazıyor. Önce HTML'den çıkarılmalı, sonra
--   REVOKE SELECT (olusturan_user_id) ... FROM anon. Sıra ters olursa sayfa
--   "İhale bulunamadı" basar. İki dosya birlikte değişeceği için ayrı iş.
--
-- bultenler / bildirimler — tablo-geneli anon GRANT'i var ama RLS 0 satır döndürüyor;
--   fiili ifşa yok. dt_takipler ile aynı sınıf (derinlemesine savunma eksiği).
--
-- =============================================================================
-- DOĞRULAMA — uygulamadan sonra
-- =============================================================================
--   401 42501 BEKLENENLER:
--     /rest/v1/ilanlar_sonuc?select=idare&limit=1
--     /rest/v1/kik_kararlar?select=ham_veri&limit=1
--     /rest/v1/kamu_ihaleleri?select=ekap_referans&limit=1
--
--   200 BEKLENENLER (bozulmamalı — sayfalar bunlara bağlı):
--     /rest/v1/kik_kararlar?select=id,karar_no,idare,ihale_konusu&limit=1
--     /rest/v1/kamu_ihaleleri?select=baslik,idare,il,orijinal_url&kaynak=eq.ka&limit=1
--
--   Sayfa dumanı: ozel-ihaleler ve kik-kararlar sayfalarını GİZLİ SEKMEDE (oturumsuz)
--   açıp liste doluyor mu bak. Boş liste = GRANT listesinde kolon eksik demektir.
