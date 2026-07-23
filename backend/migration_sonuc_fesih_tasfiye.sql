-- Sözleşme fesih / tasfiye-devir durumu (23 Tem 2026) — rakip #9'un kazımasız karşılanabilen parçası.
--
-- KAYNAK: `tum_teklifler` içindeki `fesihString` ve `tasfiyeTransferString` ("Var"/"Yok").
-- Bu kolon 539.203 satırda dolu ve HİÇBİR yerde okunmuyordu (bkz. [[tum-teklifler-gizli-veri]]).
-- Ölçüm: fesih 2.205 · tasfiye/devir 828. Oran küçük (%0,4) ama SİNYAL DEĞERİ YÜKSEK —
-- feshedilmiş sözleşme, yüklenici hakkında en güçlü risk işaretlerinden biri.
--
-- ⛔ REGEX kullanılıyor, `::jsonb` cast'i DEĞİL: tum_teklifler jsonb'ye çift kodlanmış ve
-- 720 satır eski 15.000 karakter kırpmasından bozuk → cast tüm sorguyu düşürüyor.
ALTER TABLE public.ihale_sonuclari ADD COLUMN IF NOT EXISTS fesih_var   boolean;
ALTER TABLE public.ihale_sonuclari ADD COLUMN IF NOT EXISTS tasfiye_var boolean;

-- ── Gece tazelemesi ─────────────────────────────────────────────────────────
-- DERS ([[tenzilat-cok-lot-hatasi]]): migration'da bir kez doldurulan türetilmiş kolon
-- cron'a bağlanmazsa kapsamı ARTMAZ — yeni kayıtlar NULL gelir, oran zamanla düşer.
-- Bu yüzden tazeleme fonksiyonu migration'ın parçası; run_scraper.sh onu çağırır.
CREATE OR REPLACE FUNCTION public.fesih_tasfiye_tazele()
RETURNS TABLE(guncellenen bigint)
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
DECLARE
    n bigint;
BEGIN
    UPDATE public.ihale_sonuclari s
    SET fesih_var   = (substring(s.tum_teklifler #>> '{}' from '"fesihString": ?"([^"]*)"') = 'Var'),
        tasfiye_var = (substring(s.tum_teklifler #>> '{}' from '"tasfiyeTransferString": ?"([^"]*)"') = 'Var')
    WHERE s.tum_teklifler IS NOT NULL
      AND (s.fesih_var IS NULL OR s.tasfiye_var IS NULL);   -- yalnız işlenmemiş satırlar (artımlı)
    GET DIAGNOSTICS n = ROW_COUNT;
    RETURN QUERY SELECT n;
END;
$$;

REVOKE ALL ON FUNCTION public.fesih_tasfiye_tazele() FROM PUBLIC, anon;

-- İlk doldurma
SELECT * FROM public.fesih_tasfiye_tazele();

-- Firma karnesinde "feshedilmiş sözleşme sayısı" sorgusu için (yalnız TRUE'ları indeksle → küçük kalır)
CREATE INDEX IF NOT EXISTS idx_sonuc_fesih_var ON public.ihale_sonuclari (kazanan_firma_fold)
    WHERE fesih_var IS TRUE;

-- Sözleşme DURUMU; firma kimliği içermez → anon'un zaten gördüğü sonuc_tur ile aynı sınıf.
-- ⚠️ Sonradan eklenen kolon kolon-GRANT'a girmez → vermezsek misafirde 42501 ile sayfayı öldürür.
GRANT SELECT (fesih_var, tasfiye_var) ON public.ihale_sonuclari TO anon;
GRANT SELECT (fesih_var, tasfiye_var) ON public.ihale_sonuclari TO authenticated;

NOTIFY pgrst, 'reload schema';
