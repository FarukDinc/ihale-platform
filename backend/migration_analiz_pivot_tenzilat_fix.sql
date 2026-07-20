-- ============================================================
-- İhaleGlobal — analiz_pivot.ort_tenzilat: yalnız tek kısımlı ihaleler
--
-- SORUN: ort_tenzilat = AVG(s.tenzilat_yuzde) TÜM satırlar üzerinden alınıyordu.
-- Çok kısımlı ihalede EKAP kısım bazlı yaklaşık maliyet yayımlamadığından ihalenin
-- TOPLAM maliyeti her kısma kopyalanıyor → satır tenzilatı sahte %95-100 (246.639
-- satır / %46). Ortalama bu yüzden şişiyordu.
--
-- ETKİ (3 yüzey birden):
--   • firma-analiz  → idare/kategori kırılımında "ort. %X tenz."
--   • kurum-analiz  → firma kırılımında "ort. %X tenz."
--   • ihale-detay   → "kazanmak için tahmini teklif bandı" (ort_tenzilat ile bant
--                     hesaplanıyor → yanlış tenzilat = KULLANICIYA YANLIŞ TEKLİF ÖNERİSİ)
--
-- ÇÖZÜM: FILTER (WHERE s.lot_sayisi = 1) — tenzilat yalnız tek kısımlı ihalede geçerli.
-- (lot_sayisi: backend/migration_sonuc_lot_sayisi.sql)
-- Diğer alanlar (sayı/bedel/katılımcı) DEĞİŞMEDİ.
--
-- NOT: CREATE OR REPLACE proconfig'i sıfırlar → SET statement_timeout tanımda korunuyor.
--
-- Çalıştırma:
--   docker exec -i supabase-db psql -U postgres -d postgres < backend/migration_analiz_pivot_tenzilat_fix.sql
-- ============================================================

CREATE OR REPLACE FUNCTION public.analiz_pivot(p_grup text, p_firma text DEFAULT NULL::text, p_idare text DEFAULT NULL::text, p_kategori text DEFAULT NULL::text, p_il text DEFAULT NULL::text, p_yil integer DEFAULT NULL::integer)
 RETURNS TABLE(grup_deger text, ihale_sayisi bigint, toplam_bedel numeric, ort_bedel numeric, ort_tenzilat numeric, ort_katilimci numeric, ort_gecerli_teklif numeric)
 LANGUAGE plpgsql
 STABLE
 SET statement_timeout TO '20s'
AS $function$
DECLARE
  grup_expr TEXT;
BEGIN
  -- p_grup whitelist — kullanıcı girdisi doğrudan SQL'e gitmiyor, sabit ifadeler seçiliyor.
  grup_expr := CASE p_grup
    WHEN 'yil'      THEN 'EXTRACT(YEAR FROM s.sonuc_tarihi)::TEXT'
    WHEN 'kategori' THEN 'COALESCE(i.kategori, ''Bilinmiyor'')'
    WHEN 'idare'    THEN 'COALESCE(i.idare, ''Bilinmiyor'')'
    WHEN 'il'       THEN 'COALESCE(i.il, ''Bilinmiyor'')'
    WHEN 'usul'     THEN 'COALESCE(i.usul, ''Bilinmiyor'')'
    WHEN 'tur'      THEN 'COALESCE(i.tur, ''Bilinmiyor'')'
    WHEN 'firma'    THEN 'COALESCE(y.ad, s.kazanan_firma, ''Bilinmiyor'')'
    ELSE NULL
  END;

  IF grup_expr IS NULL THEN
    RAISE EXCEPTION 'geçersiz p_grup: % (izinli: yil, kategori, idare, il, usul, tur, firma)', p_grup;
  END IF;

  -- Firma filtresi yalnız s.kazanan_firma normalize'ı üzerinden:
  -- idx_sonuc_kazanan_firma_norm ifade indeksiyle eşleşir (sağ taraf sabit —
  -- normalize_firma($1) parametre başına 1 kez hesaplanır).
  RETURN QUERY EXECUTE format($f$
    SELECT
      %s                                          AS grup_deger,
      COUNT(*)                                    AS ihale_sayisi,
      COALESCE(SUM(s.kazanan_teklif), 0)::NUMERIC AS toplam_bedel,
      ROUND(AVG(s.kazanan_teklif), 0)             AS ort_bedel,
      ROUND(AVG(s.tenzilat_yuzde) FILTER (WHERE s.lot_sayisi = 1), 2) AS ort_tenzilat,
      ROUND(AVG(s.katilimci_sayisi), 1)           AS ort_katilimci,
      ROUND(AVG(s.gecerli_teklif_sayisi), 1)      AS ort_gecerli_teklif
    FROM ihale_sonuclari s
    JOIN ilanlar i ON i.id = s.ilan_id
    LEFT JOIN yukleniciler y ON y.id = s.yuklenici_id
    WHERE s.kazanan_teklif IS NOT NULL
      AND ($1 IS NULL OR normalize_firma(s.kazanan_firma) = normalize_firma($1))
      AND ($2 IS NULL OR i.idare = $2)
      AND ($3 IS NULL OR i.kategori = $3)
      AND ($4 IS NULL OR i.il = $4)
      AND ($5 IS NULL OR EXTRACT(YEAR FROM s.sonuc_tarihi) = $5)
    GROUP BY %s
    ORDER BY ihale_sayisi DESC
    LIMIT 500
  $f$, grup_expr, grup_expr)
  USING p_firma, p_idare, p_kategori, p_il, p_yil;
END;
$function$;

-- Doğrulama: ort_tenzilat artık makul (~%10-25) olmalı, %90'lar değil
SELECT grup_deger, ihale_sayisi, ort_tenzilat
FROM public.analiz_pivot('kategori') ORDER BY ihale_sayisi DESC LIMIT 5;
