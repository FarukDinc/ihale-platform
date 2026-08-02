-- ============================================================
-- konu_tenzilat(p_kelime) — UV-1 Faz 1.5 (1 Ağu 2026)
-- ------------------------------------------------------------
-- sartname_oku'nun çıkardığı KONU (kapsam kelimeleri) ile SONUÇLANMIŞ benzer ihalelerin
-- GERÇEK ortalama tenzilatını döndürür → teklif stratejisine "konuya özgü" referans (il/genel'den
-- daha isabetli). Tenzilat PRECOMPUTED (ihale_sonuclari.tenzilat_yuzde; analiz_pivot da bunu kullanır).
--
-- ⚡ HIZ: baslik trgm indeksli (idx_ilanlar_baslik_fold_trgm) → kelime filtresi hızlı. Geniş kelime
--    (ör. 'temizlik' 51K eşleşme) tüm kümeyi toplarsa ~10sn (statement_timeout aşımı). Çözüm:
--    ORDER'SIZ LIMIT p_limit → trgm taraması p_limit eşleşmede DURUR (temizlik 9,8s→1,45s ölçüldü).
--    Örneklem avg tenzilat için yeterli. statement_timeout=4sn ek emniyet; aşım/hatada BOŞ döner
--    (çağıran il/genel'e düşer — graceful).
-- ⛔ çok-lot bug'ı: COALESCE(s.lot_sayisi,1)=1 (sahte %95 tenzilat elenir; bkz. tenzilat-cok-lot).
-- ============================================================

CREATE OR REPLACE FUNCTION public.konu_tenzilat(p_kelime text, p_limit integer DEFAULT 5000)
RETURNS TABLE(grup_deger text, ihale_sayisi bigint, ort_tenzilat numeric)
LANGUAGE plpgsql
STABLE
SECURITY DEFINER
SET statement_timeout TO '4000'
AS $function$
BEGIN
  IF p_kelime IS NULL OR length(btrim(p_kelime)) < 3 THEN
    RETURN;
  END IF;
  RETURN QUERY
  SELECT p_kelime AS grup_deger, count(*)::bigint AS ihale_sayisi,
         round(avg(t.tz)::numeric, 2) AS ort_tenzilat
  FROM (
    SELECT s.tenzilat_yuzde AS tz
    FROM public.ilanlar i
    JOIN public.ihale_sonuclari s ON s.ilan_id = i.id
    WHERE public.tr_fold(i.baslik) LIKE '%' || public.tr_fold(p_kelime) || '%'
      AND s.tenzilat_yuzde IS NOT NULL
      AND COALESCE(s.lot_sayisi, 1) = 1
    LIMIT p_limit
  ) t
  HAVING count(*) >= 3;   -- 3'ten az eşleşme istatistiksel değil → satır döndürme (çağıran atlar)
EXCEPTION WHEN OTHERS THEN
  -- statement_timeout (query_canceled) ya da beklenmeyen hata → BOŞ dön, turu bozma.
  RETURN;
END;
$function$;

-- Sahip supabase_admin (SECURITY DEFINER → tabloları onun yetkisiyle okur). API service_role ile çağırır.
GRANT EXECUTE ON FUNCTION public.konu_tenzilat(text, integer) TO authenticated, service_role;
