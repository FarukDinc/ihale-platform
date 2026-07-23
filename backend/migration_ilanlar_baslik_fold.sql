-- Misafir araması için katlanmış BAŞLIK kolonu + trigram indeksi (23 Tem 2026).
--
-- SORUN: Sonuç/Geçmiş sekmelerinde MİSAFİR araması 3 saniyede timeout'a giriyordu (anon'un
-- statement_timeout'u 3s). Sebep: misafir `baslik ILIKE '%…%'` gönderiyor, mevcut trigram
-- indeksi ise `tr_fold(baslik)` İFADESİ üzerinde → indeks EŞLEŞMİYOR, seq scan (1,96M satır).
--
-- ⛔ NEDEN `arama_fold`'u anon'a AÇMIYORUZ: içeriği
--     tr_fold(baslik || idare || okas || isin_yapilacagi_yer || ilan_metni)
--   ve `idare` misafirden KOLON-GRANT ile gizli. Anon'a verilseydi misafir, LIKE sorgularıyla
--   idare adını arayıp doğrulayarak maskelenmiş veriyi geri çıkarabilirdi. Maskeleme delinirdi.
--
-- ÇÖZÜM: yalnız misafirin ZATEN görebildiği alanlardan üretilmiş ayrı bir kolon.
-- baslik/okas/isin_yapilacagi_yer üçü de anon'a açık → yeni ifşa YOK.
-- Ayrıca misafir de artık Türkçe katlamalı arama yapabiliyor (İ/ı sorunu ortadan kalkıyor).
ALTER TABLE public.ilanlar
    ADD COLUMN IF NOT EXISTS baslik_fold text
    GENERATED ALWAYS AS (
        tr_fold(COALESCE(baslik,'') || ' ' || COALESCE(okas,'') || ' ' || COALESCE(isin_yapilacagi_yer,''))
    ) STORED;

CREATE INDEX IF NOT EXISTS idx_ilanlar_baslik_fold_trgm2
    ON public.ilanlar USING gin (baslik_fold gin_trgm_ops);

-- ⚠️ Sonradan eklenen kolon kolon-GRANT'a girmez → vermezsek misafirde 42501 ile sayfa ölür.
GRANT SELECT (baslik_fold) ON public.ilanlar TO anon;
GRANT SELECT (baslik_fold) ON public.ilanlar TO authenticated;

NOTIFY pgrst, 'reload schema';
