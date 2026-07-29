-- ============================================================================
-- migration_dt_detay_kurtarma.sql — detaysız damgalanmış DT kayıtlarını geri kuyruğa al
--                                    (29 Tem 2026)  ⚠️ İSTEĞE BAĞLI / AYRI KARAR
--
-- NEDEN: dt_kazanan_scraper.py bugüne dek dtDetayGetir yanıtının yalnız 1/4'ünü
-- (SozlesmeBilgisiList) okuyup kalan 3 bloğu ATIYORDU. Bir dt_no bir kez
-- `kazanan_denendi` damgası yiyince bir daha SEÇİLMEZ → o yanıt bir daha çekilmez.
-- 815.895 kayıt bu durumda. Kod artık 4 bloğu da yazıyor (migration_dt_detay.sql),
-- ama düzeltme yalnız İLERİYE dönüktür; bu dosya GERİYE dönük kurtarmadır.
--
-- AYIRT EDİCİ: migration_ekap_hasat.sql ile gelen `detay_cekildi` kolonu. YENİ kod
-- işlediği HER satırda bunu damgalar (sözleşme bulunsun/bulunmasın, hatta gerçek
-- 404'te bile). Dolayısıyla:
--     kazanan_denendi IS NOT NULL AND detay_cekildi IS NULL
--   = "ESKİ kodla, detay blokları okunmadan damgalanmış"  → net, tahmine gerek yok.
-- (migration_dt_kazanan_kurtarma.sql'deki "kesin ayırt edilemez" sorunu BURADA YOK:
--  orada geçici-hata ile gerçek-404 aynı görünüyordu; burada damga sürümü açık.)
--
-- MALİYET: yeniden çekim EKAP'a EK İSTEK demektir (dtDetayGetir; CAPTCHA/token
-- maliyeti YOK, yalnız zaman + proxy kotası). ⚠️ Proxy havuzunun asıl darboğazı
-- port başına eşzamanlı bağlantı → AYNI ANDA TEK AĞIR PROXY İŞİ kuralı geçerli.
-- Şu an ekap_sonuc_backfill ve ilan_metni_backfill akıyorsa BU DOSYAYI KOŞMAYIN;
-- kuyruk şişer ve gecelik tur yeni "sonuç" kayıtlarına hiç sıra bulamaz.
--
-- ÖNKOŞUL: backend/migration_ekap_hasat.sql UYGULANMIŞ olmalı (detay_cekildi kolonu).
-- Çalıştır: docker exec -i supabase-db psql -U postgres -d postgres < backend/migration_dt_detay_kurtarma.sql
-- Idempotent: yalnız NULL'a çeker; zaten kuyrukta olanları atlar (zararsız tekrar).
-- ============================================================================

-- ── 0) ÖNKOŞUL DENETİMİ ─────────────────────────────────────────────────────
DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM information_schema.columns
                 WHERE table_schema = 'public' AND table_name = 'dogrudan_temin_ilanlari'
                   AND column_name = 'detay_cekildi') THEN
    RAISE EXCEPTION 'ABORT: detay_cekildi kolonu yok — once backend/migration_ekap_hasat.sql uygulayin';
  END IF;
END $$;

-- ── 1) ÖNCE KAPSAMI GÖR (yazma yok) ─────────────────────────────────────────
-- Kaç satır yeniden kuyruğa alınacak? Bu sayıyı GÖRMEDEN 2. adımı koşmayın:
-- gecelik `--limit` bunu eritemezse kuyruk kalıcı olarak şişer.
SELECT count(*) AS yeniden_kuyruga_alinacak,
       min(kazanan_denendi) AS en_eski_damga,
       max(kazanan_denendi) AS en_yeni_damga
FROM public.dogrudan_temin_ilanlari
WHERE kazanan_denendi IS NOT NULL      -- eski kodla damgalanmış
  AND detay_cekildi   IS NULL          -- ama detay blokları HİÇ okunmamış
  AND dt_ihale_token  IS NOT NULL      -- kuyruğa girebilir (E10 var)
  AND durum IN ('Sonuç Duyurusu Yayımlanmış',
                'Doğrudan Temin Sonuçlandırıldı',
                'Sonuç Bilgileri Gönderildi');

-- ── 2) YENİDEN KUYRUĞA AL ───────────────────────────────────────────────────
-- ⚠️ Aşağıdaki blok BİLEREK YORUMDA. Yukarıdaki sayımı görüp koşmaya karar
--    verdiğinizde yorumu kaldırın. Kaza eseri yüz binlerce satırı kuyruğa
--    dökmemek için varsayılan davranış "hiçbir şey yapma"dır.
--
-- BEGIN;
--
-- UPDATE public.dogrudan_temin_ilanlari
-- SET kazanan_denendi = NULL
-- WHERE kazanan_denendi IS NOT NULL
--   AND detay_cekildi   IS NULL
--   AND dt_ihale_token  IS NOT NULL
--   AND durum IN ('Sonuç Duyurusu Yayımlanmış',
--                 'Doğrudan Temin Sonuçlandırıldı',
--                 'Sonuç Bilgileri Gönderildi');
--
-- COMMIT;

-- ── NOT: KAPSAM DARLIĞI (bilinçli) ──────────────────────────────────────────
-- Sorgu yalnız "sonuç" durum grubunu alıyor çünkü dt_kazanan_scraper.py kuyruğu
-- (secim_cek) da öyle. Oysa 3 yeni blok (BransKodList / idare zinciri / ilan
-- listeleri) AKTİF kayıtlarda da dolu geliyor — canlı doğrulandı: durum 202
-- ("Doğrudan Temin Duyurusu Yayımlanmış") bir kayıtta BransKodList=['33194120'].
-- Yani kuyruğu tüm durumlara açmak DT kategori sinyalini bugün sonuçlanmamış
-- ~milyon kayda da getirir. Bu AYRI ve DAHA BÜYÜK bir karar (EKAP istek hacmi
-- katlanır) → burada kasıtlı olarak yapılmadı; YAPILACAKLAR.md'ye yazılmalı.
