-- ============================================================
-- MADDE 9 — "Benzer İhaleler" skorlu eşleştirme (30 Tem 2026)
-- ------------------------------------------------------------
-- SORUN: v1-ihale-detay.html benzerYukle() yalnız kategori + tur SABİT filtresi (.eq)
--   kullanıyordu → İstanbul'daki BALIK ihalesine Aksaray'daki EKMEKLİK UN "benzer"
--   çıkıyordu (ikisi de "Gıda" + "Mal"). Kategori tek başına çok kaba.
--
-- ÇÖZÜM: skorlu RPC — aynı idare (+35), aynı il (+20), aynı kategori (+20), + BAŞLIK
--   konu-kelimesi örtüşmesi (+8/kelime; ihale_konu_kelimeleri ile). Kelime sinyali
--   "balık" ile "un"u aynı kategoride bile ayırır. Tur (ihale tipi) ön-eleme kalır.
--
-- SECURITY DEFINER: idare anon'a KAPALI ama skorlamada kullanılır → fonksiyon idare'yi
--   İÇERİDE okur, DÖNDÜRMEZ (sadece "Aynı idare" gerekçesi; kurum ADI sızmaz). ilanlar'ın
--   diğer alanları (baslik/il/tur/kategori) zaten anon'a açık. Misafir de daha iyi öneri alır.
--
-- Aktif küme küçük (~5-6K) → keyword LIKE taraması timeout riski taşımaz.
-- Çalıştır (yeni fonksiyon → superuser):
--   docker exec -i supabase-db psql -U supabase_admin -d postgres < backend/migration_benzer_ihaleler.sql
-- ============================================================

CREATE OR REPLACE FUNCTION public.benzer_ihaleler(p_ilan_id uuid, p_limit int DEFAULT 6)
RETURNS TABLE (id uuid, baslik text, il text, tur text, kategori text,
               son_teklif_tarihi timestamptz, skor numeric, neden text)
LANGUAGE sql STABLE SECURITY DEFINER SET search_path = public AS $$
  WITH kaynak AS (
    SELECT i.kategori, i.il, i.idare, i.tur, i.baslik
    FROM public.ilanlar i WHERE i.id = p_ilan_id
  ),
  kw AS (
    SELECT COALESCE(array_agg(t.kelime), ARRAY[]::text[]) AS kws
    FROM kaynak k, public.ihale_konu_kelimeleri(k.baslik) t
  )
  SELECT i.id, i.baslik, i.il, i.tur, i.kategori,
         i.son_teklif_tarihi::timestamptz,
         round((
           (CASE WHEN k.idare    IS NOT NULL AND i.idare    = k.idare    THEN 35 ELSE 0 END)
         + (CASE WHEN k.il       IS NOT NULL AND i.il       = k.il       THEN 20 ELSE 0 END)
         + (CASE WHEN k.kategori IS NOT NULL AND i.kategori = k.kategori THEN 20 ELSE 0 END)
         + (SELECT count(*) FROM unnest(kw.kws) w WHERE public.tr_fold(i.baslik) LIKE '%'||w||'%') * 8
         )::numeric, 1) AS skor,
         NULLIF(concat_ws(' · ',
           CASE WHEN k.idare    IS NOT NULL AND i.idare    = k.idare    THEN 'Aynı idare'    END,
           CASE WHEN k.kategori IS NOT NULL AND i.kategori = k.kategori THEN 'Aynı kategori' END,
           CASE WHEN k.il       IS NOT NULL AND i.il       = k.il       THEN 'Aynı il'       END
         ), '') AS neden
  FROM public.ilanlar i, kaynak k, kw
  WHERE i.id <> p_ilan_id
    AND i.durum = 'aktif'
    AND (i.son_teklif_tarihi IS NULL OR i.son_teklif_tarihi >= now())
    AND (k.tur IS NULL OR i.tur = k.tur)   -- ihale tipi ön-eleme (Yapım'a Satış/Kiraya Verme çıkmasın)
    AND ( (k.idare    IS NOT NULL AND i.idare    = k.idare)
       OR (k.kategori IS NOT NULL AND i.kategori = k.kategori)
       OR (k.il       IS NOT NULL AND i.il       = k.il)
       OR EXISTS (SELECT 1 FROM unnest(kw.kws) w WHERE public.tr_fold(i.baslik) LIKE '%'||w||'%') )
  ORDER BY skor DESC, i.son_teklif_tarihi ASC NULLS LAST
  LIMIT LEAST(GREATEST(p_limit, 1), 20);
$$;
REVOKE EXECUTE ON FUNCTION public.benzer_ihaleler(uuid,int) FROM public;
GRANT  EXECUTE ON FUNCTION public.benzer_ihaleler(uuid,int) TO anon, authenticated, service_role;

NOTIFY pgrst, 'reload schema';
