-- ============================================================================
-- migration_dt_kazanan_kurtarma.sql — GEÇMİŞ sessiz kayıp kurtarma (21 Tem 2026)
--
-- NEDEN: dt_kazanan_scraper.py'nin eski sürümü dtDetayGetir'in HER non-200 ve HER
-- istisnasında (403/407/429/5xx blok, TLS/timeout, proxy düşüşü) None dönüyor ve
-- ana döngü satırı YİNE DE kazanan_denendi ile damgalıyordu. Damgalanan satır bir
-- daha seçilmez ve kazanan_denendi'yi NULL yapan hiçbir kod yoktur → GEÇİCİ bir
-- hatayla damgalanan dt_no'lar KALICI kayboldu. Kod düzeltildi (artık yalnız gerçek
-- 404/boş-liste damgalanır; geçici hata alan satır NULL kalıp sonraki gece yeniden
-- denenir), ama düzeltme yalnız İLERİYE dönüktür. Bu dosya GEÇMİŞTE yanlış damgalanan
-- satırları yeniden kuyruğa alır.
--
-- ⚠️ KESİN AYIRT EDİLEMEZ: "geçici hatayla yanlış damgalanmış" satır ile "gerçekten
--    detayı olmayan (404) / boş sonuç" satır, VERİTABANINDA AYNI görünür — ikisi de
--    kazanan_denendi DOLU + dogrudan_temin_sonuclari'nda kaydı YOK. Bu yüzden kurtarma
--    kaçınılmaz olarak İKİSİNİ DE yeniden kuyruğa alır. Düzeltilmiş scraper ile:
--      · gerçek 404/boş  → yeniden çekilir, sonuç yok, TEKRAR damgalanır (tek fazladan
--        istek, kalıcı; API ücretsiz — token/CAPTCHA maliyeti YOK).
--      · geçici kayıp     → bu kez başarıyla çekilir, sonuç yazılır (KURTARILDI).
--
-- ⚠️ HACİM: DT kazanan kapsaması ~%7,9'da takılı; yani "damgalı ama sonuçsuz"
--    satırların ÇOK büyük bir kısmı yeniden kuyruğa girer (yüz binler mertebesi).
--    Gecelik `--limit 2000` bunu ERİTEMEZ — kurtarmadan sonra AYRI, tek seferlik
--    yüksek --limit'li arka plan turu gerekir (bkz. YAPILACAKLAR.md'deki birikmiş
--    kuyruk maddesi). Bu migration'ı O turu koşmaya hazır olduğunuzda uygulayın;
--    aksi halde gecelik kuyruk şişer ve yeni "sonuç" durumlarına sıra geç gelir.
--
-- Çalıştır: docker exec -i supabase-db psql -U postgres -d postgres < backend/migration_dt_kazanan_kurtarma.sql
-- Idempotent: yalnız NULL'a çeker; tekrar çalıştırmak zaten NULL olanları atlar (zararsız).
-- ============================================================================

-- ── 1) ÖNCE KAPSAMI GÖR (yazma yok) ─────────────────────────────────────────
-- Kaç satır yeniden kuyruğa alınacak? Uygulamadan önce bu sayıyı görün.
SELECT count(*) AS yeniden_kuyruga_alinacak
FROM public.dogrudan_temin_ilanlari i
WHERE i.kazanan_denendi IS NOT NULL          -- daha önce damgalanmış
  AND i.dt_ihale_token IS NOT NULL            -- kuyruğa girebilir (token var)
  AND i.durum IN ('Sonuç Duyurusu Yayımlanmış',
                  'Doğrudan Temin Sonuçlandırıldı',
                  'Sonuç Bilgileri Gönderildi')
  AND NOT EXISTS (SELECT 1 FROM public.dogrudan_temin_sonuclari s
                  WHERE s.dt_no = i.dt_no);   -- ama hiç sonuç yazılmamış

-- ── 2) YENİDEN KUYRUĞA AL ────────────────────────────────────────────────────
-- kazanan_denendi = NULL → satır secim_cek kuyruğuna geri döner. Düzeltilmiş scraper
-- geçici kaybı kurtarır, gerçek 404/boşu yeniden (doğru biçimde) damgalar.
BEGIN;

UPDATE public.dogrudan_temin_ilanlari i
SET kazanan_denendi = NULL
WHERE i.kazanan_denendi IS NOT NULL
  AND i.dt_ihale_token IS NOT NULL
  AND i.durum IN ('Sonuç Duyurusu Yayımlanmış',
                  'Doğrudan Temin Sonuçlandırıldı',
                  'Sonuç Bilgileri Gönderildi')
  AND NOT EXISTS (SELECT 1 FROM public.dogrudan_temin_sonuclari s
                  WHERE s.dt_no = i.dt_no);

COMMIT;

-- Doğrulama (elle): kuyruk artık kurtarılacak satırları içermeli
--   SELECT count(*) FROM dogrudan_temin_ilanlari
--   WHERE dt_ihale_token IS NOT NULL AND kazanan_denendi IS NULL
--     AND durum IN ('Sonuç Duyurusu Yayımlanmış','Doğrudan Temin Sonuçlandırıldı','Sonuç Bilgileri Gönderildi');
-- Ardından tek seferlik tur:  python dt_kazanan_scraper.py --limit 500000 --rpm 300
