-- =============================================================================
-- migration_rfq_ka_dahil.sql — YAPILACAKLAR_v2 V2-4 (21 Tem 2026)
-- Haritanın "Açık RFQ" katmanına Kalkınma Ajansı (KA) güncel ilanlarını da dahil et.
--
-- SORUN: il_rfq_dagilimi() yalnız satinalma_talepleri'ni sayıyordu (canlıda 3 seed RFQ).
-- Ama e-Satınalma LİSTESİ (ozel-ihaleler.html) hem platform RFQ hem KA (kamu_ihaleleri
-- kaynak='ka') ilanlarını gösteriyor → harita listeden az "açık fırsat" gösteriyordu
-- (kullanıcı "açık RFQ 3 gösteriyor, gerçek veriler girilmemiş" şikâyeti). Karar: KA dahil.
--
-- KARAR (kullanıcı, 21 Tem): haritanın açık-fırsat katmanı KA'yı da saysın; etiket "Açık RFQ"
-- kalır. Böylece harita sayacı/pinleri e-Satınalma listesiyle birebir tutarlı olur.
--
-- KURALLAR (bkz. migration_rfq_bayat.sql):
--   • İmza DEĞİŞMİYOR (p_kategori text DEFAULT NULL); dönen alanlar (il, adet) — maske etkilenmez.
--   • Platform RFQ: NULL-güvenli (son_teklif_tarihi IS NULL OR >= now()) — tarihsiz RFQ korunur.
--   • KA: kaCek (ozel-ihaleler.html) ile AYNI kural → düz `son_teklif_tarihi >= now()` (KA'da
--     güncel = süresi dolmamış; kaCek de çıplak .gte kullanıyor, tutarlı).
--   • Sektör (p_kategori) seçiliyse KA HARİÇ — KA'da 41-kanonik taksonomi yok (kaCek de böyle).
--   • Frontend rfqYukle keyOf(il) ile fold'layıp topluyor → il casing farkı sorun değil,
--     yine de outer GROUP BY ile tek-satır-per-il temiz sözleşmesi korunur.
-- =============================================================================

CREATE OR REPLACE FUNCTION public.il_rfq_dagilimi(p_kategori text DEFAULT NULL)
RETURNS TABLE(il text, adet bigint)
LANGUAGE sql STABLE
AS $$
  SELECT b.il, sum(b.adet)::bigint AS adet
  FROM (
    -- 1) Platform RFQ (satinalma_talepleri) — NULL-güvenli, sektör filtreli
    SELECT il, count(*)::bigint AS adet
    FROM public.satinalma_talepleri
    WHERE durum = 'acik'
      AND (son_teklif_tarihi IS NULL OR son_teklif_tarihi >= now())   -- ⚠️ NULL-güvenli
      AND il IS NOT NULL AND btrim(il) <> ''
      AND (p_kategori IS NULL OR kategori = p_kategori)
    GROUP BY il

    UNION ALL

    -- 2) Kalkınma Ajansı (kamu_ihaleleri kaynak='ka') — yalnız sektör filtresi YOKKEN,
    --    güncel (süresi dolmamış). kaCek ile aynı: çıplak >= now() (KA'da NULL deadline güncel değil).
    SELECT il, count(*)::bigint AS adet
    FROM public.kamu_ihaleleri
    WHERE kaynak = 'ka'
      AND son_teklif_tarihi >= now()
      AND il IS NOT NULL AND btrim(il) <> ''
      AND p_kategori IS NULL
    GROUP BY il
  ) b
  GROUP BY b.il;
$$;

-- Yetki (fonksiyon CREATE OR REPLACE ile gövde değişse de yeniden GRANT güvenli):
REVOKE ALL     ON FUNCTION public.il_rfq_dagilimi(text) FROM public;
GRANT  EXECUTE ON FUNCTION public.il_rfq_dagilimi(text) TO anon, authenticated, service_role;

NOTIFY pgrst, 'reload schema';

-- =============================================================================
-- DOĞRULAMA (ANON key ile):
--   curl -s -X POST https://ihaleglobal.com/rest/v1/rpc/il_rfq_dagilimi \
--     -H "apikey: <anon>" -H "Content-Type: application/json" -d '{}'
--   -- Beklenen: platform RFQ illeri (Kocaeli/İstanbul/Ankara) + KA güncel illeri (Sakarya,
--   -- Bolu, ...) birlikte; toplam adet platform(3) + KA_guncel(~10) ≈ 13.
--   -- Sektör filtreli çağrıda (p_kategori dolu) KA HARİÇ, yalnız platform RFQ dönmeli.
-- =============================================================================
