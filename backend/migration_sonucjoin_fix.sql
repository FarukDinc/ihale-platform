-- =============================================================================
-- İhaleGlobal — ilanlar_sonuc view join DÜZELTMESİ (TASLAK)
-- YAPILACAKLAR #9 — 20 Tem 2026
--
-- ÖN KOŞUL: backend/migration_sonucjoin_teshis.sql çıktıları H1'i doğrulamalı:
--   T1: ekap_id_dolu ≈ 0        (sonuç tablosunda ekap_id hiç yazılmıyor)
--   T3: eski_join_eslesme = 0   (mevcut join ölü)
--   T4: eslesen_sonuc_satiri ≈ T1.toplam  (ilan_id join tabloyu kapsıyor)
--   T10 hata verirse lot_sayisi kolonu yok → aşağıdaki s.lot_sayisi satırını çıkar.
--
-- KÖK NEDEN: ihale_sonuclari'nı dolduran tek canlı yazar ekap_sonuc_backfill.py,
-- ekap_id kolonunu HİÇ yazmıyor; gerçek anahtar (ilan_id, kisim_no) ve ilan_id =
-- ilanlar.id UUID FK. Eski join 'i.ekap_id = s.ekap_id' NULL'a eşitlik olduğundan
-- 356.904 satırın tamamında sonuç tarafı NULL kalıyordu. Canlı RPC'ler zaten
-- 'i.id = s.ilan_id' kullanıyor (migration_analiz_rpc.sql:60,
-- migration_yuklenici_agg.sql:81) — view aynı kanona çekiliyor.
--
-- ── GÜVENLİK / GRANT KORUMA (KRİTİK) ─────────────────────────────────────────
-- Bu view sahip-yetkisiyle çalışır ve 18 Tem denetiminde (anon_maske_v2) anon'dan
-- REVOKE edildi; authenticated SELECT'i korundu. Bu dosya BİLEREK
-- CREATE OR REPLACE kullanır (DROP+CREATE DEĞİL):
--   • CREATE OR REPLACE mevcut grant'ları aynen korur.
--   • Yine de sonda aynı güvenlik hali idempotent olarak YENİDEN yazılır —
--     dosya ileride DROP+CREATE'e çevrilirse bile anon kapalı kalsın.
-- Uygulama sonrası anon REST doğrulaması ŞART (aşağıda).
--
-- ── KOLON KURALI ─────────────────────────────────────────────────────────────
-- CREATE OR REPLACE VIEW eski kolon adı/tipi/sırasını değiştiremez, yalnız SONA
-- ekleyebilir. Eski 23 kolon birebir korunuyor; sona 2 yeni kolon eklendi:
--   kisim_no   — çok kısımlı ihalede kısım sırası (backfill anahtarının parçası)
--   lot_sayisi — tenzilat güven kuralı için: lot_sayisi=1 → tenzilat GEÇERLİ,
--                lot_sayisi>1 → tenzilat/yaklaşık maliyet BİLİNEMEZ, gösterme
--                (bkz. migration_sonuc_lot_sayisi.sql).
--
-- ── KARDİNALİTE DEĞİŞİMİ (bilinçli) ──────────────────────────────────────────
-- Eski view (teoride) ilan başına 1 satırdı; yeni join KISIM başına satır döndürür
-- (çok kısımlı ihalede ilan başına birden çok satır; toplam ≈ T9 çıktısı, ~560K).
-- Frontend'de view'ı kullanan SIFIR dosya var (18 Tem denetimi + 20 Tem yeniden
-- tarama: hiçbir .html/.js/.py sorgulamıyor) → kırılacak tüketici yok.
-- İleride ilan başına tek satır gerekirse kisim_no=1 filtresi YETMEZ (çok-lot
-- ihalede yanıltıcı) — lot_sayisi=1 filtresi ya da ayrı özet view kullanılmalı.
--
-- ÇALIŞTIRMA (VDS — teşhis onayından SONRA):
--   docker exec -i supabase-db psql -U postgres -d postgres \
--     < backend/migration_sonucjoin_fix.sql
-- =============================================================================

BEGIN;

CREATE OR REPLACE VIEW public.ilanlar_sonuc AS
SELECT
  i.id, i.ekap_id, i.ikn, i.baslik, i.idare, i.il, i.tur, i.usul, i.kategori,
  i.son_teklif_tarihi, i.ilan_tarihi, i.yaklasik_maliyet_min, i.yaklasik_maliyet_max, i.durum,
  s.yuklenici_ad, s.sozlesme_bedeli, s.tenzilat_yuzde, s.katilimci_sayisi,
  s.gecerli_teklif_sayisi, s.sozlesme_tarihi, s.is_baslama_tarihi, s.is_bitis_tarihi, s.sonuc_tur,
  -- YENİ kolonlar (yalnız SONA eklenebilir — CREATE OR REPLACE kuralı):
  s.kisim_no,
  s.lot_sayisi
FROM public.ilanlar i
LEFT JOIN public.ihale_sonuclari s ON s.ilan_id = i.id;
-- ^ DÜZELTME: eski koşul 'i.ekap_id = s.ekap_id' idi; s.ekap_id tüm satırlarda
--   NULL olduğundan hiç eşleşmiyordu.

-- Güvenlik halinin idempotent yeniden-yazımı (anon_maske_v2 ile birebir aynı):
REVOKE SELECT ON public.ilanlar_sonuc FROM anon;
GRANT  SELECT ON public.ilanlar_sonuc TO authenticated;
-- service_role grant gerektirmez (Supabase'de bypass).

COMMIT;

NOTIFY pgrst, 'reload schema';

-- =============================================================================
-- DOĞRULAMA — uygulamadan sonra
-- =============================================================================
-- 1) psql: sonuç kolonları artık dolu mu?
--      SELECT count(*) AS sonuclu FROM public.ilanlar_sonuc WHERE yuklenici_ad IS NOT NULL;
--    BEKLENEN: 0 DEĞİL — T4'teki eşleşme sayısına yakın (yuklenici_ad dolu olanlar).
-- 2) psql: toplam satır ≈ T9 çıktısı (kardinalite beklendiği gibi mi?).
--      SELECT count(*) FROM public.ilanlar_sonuc;
-- 3) anon REST (maskeleme BOZULMAMALI):
--      curl -s -o /dev/null -w '%{http_code}' \
--        'https://ihaleglobal.com/rest/v1/ilanlar_sonuc?select=id&limit=1' \
--        -H "apikey: $ANON_KEY" -H "Authorization: Bearer $ANON_KEY"
--    BEKLENEN: 401 (42501). 200 dönerse DERHAL: REVOKE SELECT ON public.ilanlar_sonuc FROM anon;
-- 4) authenticated REST: aynı istek login token'la → 200 BEKLENİR.
-- 5) GRANT durumu T11 ile aynı kalmalı:
--      SELECT grantee, privilege_type FROM information_schema.role_table_grants
--      WHERE table_schema='public' AND table_name='ilanlar_sonuc' ORDER BY 1,2;
