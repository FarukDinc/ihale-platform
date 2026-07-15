-- Sektör-bazlı "sana uygun yeni ihale/RFQ" bildirimi (notify.py yalnız TAKİP edilen ihale hatırlatıcısıydı).
-- Taksonomi hizalandıktan sonra profil.sektorler (kanonik) = ilanlar.kategori (kanonik) → doğrudan eşleşir.
-- SECURITY DEFINER: profil + bildirimler RLS'ini aşar (backend/cron çağırır). Dedup: NOT EXISTS.
-- profil.user_id = kullanici_profiller.id = auth.users.id (doğrulandı) → bildirimler FK güvenli.

-- 1) Kamu ilanı → sektörü eşleşen firmalara
CREATE OR REPLACE FUNCTION public.yeni_ilan_bildirim_uret(p_gun int DEFAULT 1)
RETURNS integer
LANGUAGE plpgsql SECURITY DEFINER SET search_path = public
AS $$
DECLARE eklenen integer;
BEGIN
  WITH adaylar AS (
    SELECT p.user_id, i.id AS ilan_id, i.baslik, i.kategori, i.il, i.idare
    FROM public.ilanlar i
    JOIN public.profil p
      ON i.kategori = ANY(p.sektorler)
     AND (p.tercih_iller  IS NULL OR array_length(p.tercih_iller,1)  IS NULL OR i.il  = ANY(p.tercih_iller))
     AND (p.tercih_turler IS NULL OR array_length(p.tercih_turler,1) IS NULL OR i.tur = ANY(p.tercih_turler))
    WHERE i.durum = 'aktif'
      AND i.kategori IS NOT NULL
      AND i.olusturulma >= now() - (p_gun * interval '1 day')
      AND (i.son_teklif_tarihi IS NULL OR i.son_teklif_tarihi > now())
      AND p.sektorler IS NOT NULL AND array_length(p.sektorler,1) > 0
  ), yeni AS (
    INSERT INTO public.bildirimler (kullanici_id, baslik, icerik, tur, ilan_id, aksiyon_url, okundu, olusturulma)
    SELECT a.user_id,
           'Sektörünüzde yeni ihale: ' || left(a.baslik, 70),
           a.kategori || COALESCE(' · ' || a.il, '') || COALESCE(' · ' || a.idare, ''),
           'ihale', a.ilan_id, 'ihale-detay?id=' || a.ilan_id, false, now()
    FROM adaylar a
    WHERE NOT EXISTS (
      SELECT 1 FROM public.bildirimler b
      WHERE b.kullanici_id = a.user_id AND b.ilan_id = a.ilan_id AND b.tur = 'ihale'
    )
    RETURNING 1
  )
  SELECT count(*) INTO eklenen FROM yeni;
  RETURN eklenen;
END;
$$;

-- 2) Yeni RFQ (özel satınalma) → sektörü eşleşen tedarikçilere (kendi RFQ'su hariç)
--    bildirimler.ilan_id FK ilanlar'a bakar → RFQ'da NULL; dedup aksiyon_url üzerinden.
CREATE OR REPLACE FUNCTION public.yeni_rfq_bildirim_uret(p_gun int DEFAULT 1)
RETURNS integer
LANGUAGE plpgsql SECURITY DEFINER SET search_path = public
AS $$
DECLARE eklenen integer;
BEGIN
  WITH adaylar AS (
    SELECT p.user_id, t.id AS talep_id, t.baslik, t.kategori, t.il
    FROM public.satinalma_talepleri t
    JOIN public.profil p
      ON t.kategori = ANY(p.sektorler)
     AND (p.tercih_iller IS NULL OR array_length(p.tercih_iller,1) IS NULL OR t.il = ANY(p.tercih_iller))
    WHERE t.durum = 'acik'
      AND t.olusturulma >= now() - (p_gun * interval '1 day')
      AND p.user_id <> t.olusturan_user_id
      AND p.sektorler IS NOT NULL AND array_length(p.sektorler,1) > 0
  ), yeni AS (
    INSERT INTO public.bildirimler (kullanici_id, baslik, icerik, tur, aksiyon_url, okundu, olusturulma)
    SELECT a.user_id,
           'Size uygun yeni satınalma ilanı: ' || left(a.baslik, 60),
           a.kategori || COALESCE(' · ' || a.il, ''),
           'eslestirme', 'ozel-ihale-detay?id=' || a.talep_id, false, now()
    FROM adaylar a
    WHERE NOT EXISTS (
      SELECT 1 FROM public.bildirimler b
      WHERE b.kullanici_id = a.user_id
        AND b.aksiyon_url = 'ozel-ihale-detay?id=' || a.talep_id
        AND b.tur = 'eslestirme'
    )
    RETURNING 1
  )
  SELECT count(*) INTO eklenen FROM yeni;
  RETURN eklenen;
END;
$$;

REVOKE ALL     ON FUNCTION public.yeni_ilan_bildirim_uret(int) FROM public, anon;
REVOKE ALL     ON FUNCTION public.yeni_rfq_bildirim_uret(int)  FROM public, anon;
GRANT  EXECUTE ON FUNCTION public.yeni_ilan_bildirim_uret(int) TO service_role;
GRANT  EXECUTE ON FUNCTION public.yeni_rfq_bildirim_uret(int)  TO service_role;
