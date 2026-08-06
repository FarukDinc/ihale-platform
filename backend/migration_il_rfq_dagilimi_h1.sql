-- =============================================================================
-- migration_il_rfq_dagilimi_h1.sql — H1: harita "Açık Talepler" = e-Satınalma ile tutarlı
-- 6 Ağu 2026
-- =============================================================================
-- SORUN: harita KPI "Açık Talepler" = 9 ama e-Satınalma listesi = 3. Fark: il_rfq_dagilimi
-- iki kaynağı UNION'lıyordu — platform RFQ (satinalma_talepleri, 3) + Kalkınma Ajansı
-- (kamu_ihaleleri kaynak='ka', 6). Ama KA aslında İHALE'dir (İhaleler sayfasında görünür),
-- RFQ/satınalma talebi DEĞİL → "Açık Talepler" (e-Satınalma) kapsamına sokulması yanlış
-- kategori + kullanıcıyı şaşırtıyor (harita 9, tıklayınca liste 3).
-- ÇÖZÜM: KA UNION'ını çıkar → il_rfq_dagilimi yalnız platform RFQ sayar = e-Satınalma ile birebir.
--
-- CREATE OR REPLACE grant'ları korur (anon-açık kalır). owner=postgres.
--   ssh ihale2 "docker exec -i supabase-db psql -U postgres -d postgres" < backend/migration_il_rfq_dagilimi_h1.sql
-- =============================================================================

CREATE OR REPLACE FUNCTION public.il_rfq_dagilimi(p_kategori text DEFAULT NULL::text)
RETURNS TABLE(il text, adet bigint)
LANGUAGE sql STABLE
AS $function$
  -- H1: YALNIZ platform RFQ (satinalma_talepleri) — e-Satınalma listesiyle BİREBİR aynı kapsam.
  -- (Eskiden Kalkınma Ajansı kamu_ihaleleri kaynak='ka' UNION'ı da vardı → 9 vs 3 tutarsızlık;
  --  KA = ihale, İhaleler'de sayılır, RFQ değil.)
  SELECT il, count(*)::bigint AS adet
  FROM public.satinalma_talepleri
  WHERE durum = 'acik'
    AND (son_teklif_tarihi IS NULL OR son_teklif_tarihi >= now())   -- NULL-güvenli
    AND il IS NOT NULL AND btrim(il) <> ''
    AND (p_kategori IS NULL OR kategori = p_kategori)
  GROUP BY il;
$function$;

NOTIFY pgrst, 'reload schema';

-- DOĞRULAMA: SELECT sum(adet) FROM il_rfq_dagilimi();  -- 3 (satinalma_talepleri açık sayısı) olmalı
