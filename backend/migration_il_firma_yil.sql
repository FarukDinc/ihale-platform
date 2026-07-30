-- ============================================================
-- MADDE 12 — "Bu ilde öne çıkan firmalar" YIL bazlı sıralama (31 Tem 2026)
-- ------------------------------------------------------------
-- SORUN: v1-harita panelinde firmalar yukleniciler.toplam_ciro (TÜM-ZAMAN) ile sıralanıyor
--   → hep toplam en yüksek. Enflasyon nedeniyle yıl bazlı kıyas gerekli.
-- ÇÖZÜM: il_sektor_firmalar deseninin YIL varyantı — kategori filtresi yerine yıl filtresi.
--   Aynı indeksi kullanır: idx_ilanlar_il_fold_kategori (tr_fold(il) prefix'i sargable).
--   Yıl extract'i il-fold il aday kümesi (tek il) daraldıktan SONRA uygulanır → hızlı.
--   normalize_firma ile grupla (il_sektor_firmalar ile aynı; yuklenici_id null riski yok).
--   Yıl aralığı FRONTEND'de sabit 2004→currentYear (çöp 1926 + tam-tablo timeout nedeniyle).
--
-- Çalıştır (yeni fonksiyon → superuser):
--   docker exec -i supabase-db psql -U supabase_admin -d postgres < backend/migration_il_firma_yil.sql
-- ============================================================

CREATE OR REPLACE FUNCTION public.il_firma_yil(
  p_il_folds text[], p_yil int, p_limit int DEFAULT 8)
RETURNS TABLE (ad text, sozlesme bigint, toplam_bedel numeric)
LANGUAGE sql STABLE SECURITY INVOKER SET search_path = public AS $$
  SELECT (array_agg(s.kazanan_firma ORDER BY s.sonuc_tarihi DESC NULLS LAST))[1] AS ad,
         count(*)::bigint                                  AS sozlesme,
         sum(COALESCE(s.kazanan_teklif, 0))::numeric       AS toplam_bedel
  FROM public.ihale_sonuclari s
  JOIN public.ilanlar i ON i.id = s.ilan_id
  WHERE s.kazanan_firma IS NOT NULL
    AND public.tr_fold(i.il) = ANY(p_il_folds)
    AND extract(year FROM COALESCE(s.sozlesme_tarihi, s.sonuc_tarihi)) = p_yil
  GROUP BY public.normalize_firma(s.kazanan_firma)
  ORDER BY sum(COALESCE(s.kazanan_teklif, 0)) DESC, count(*) DESC
  LIMIT LEAST(GREATEST(p_limit, 1), 50);
$$;
ALTER FUNCTION public.il_firma_yil(text[], int, int) SET statement_timeout = '15s';
REVOKE EXECUTE ON FUNCTION public.il_firma_yil(text[], int, int) FROM public;
GRANT  EXECUTE ON FUNCTION public.il_firma_yil(text[], int, int) TO anon, authenticated, service_role;

NOTIFY pgrst, 'reload schema';

-- Doğrulama:
--   SELECT * FROM il_firma_yil(ARRAY['ankara'], 2024, 8);
