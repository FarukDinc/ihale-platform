-- =============================================================================
-- migration_firmam_dt_destek.sql — "Benim Firmam" analizine DT-ONLY firma desteği (5 Ağu 2026)
-- =============================================================================
-- SORUN: "Seçili Firma Analizi" (v1-analiz) tamamen İHALE kazananı (yukleniciler + yuklenici_id)
--   üzerine kurulu. Yalnız doğrudan temin kazanan firmalar (ör. DİNÇ LAZER: 11 DT / 0 ihale)
--   yukleniciler'de YOK → arama bulamıyor, firmami_belirle reddediyor.
-- ÇÖZÜM: DT firmalarını da "benim firmam" olarak seçilebilir yap. DT firma özeti = firma_dt_toplam
--   (ad, firma_norm, dt_sozlesme, dt_bedel). DT seçili firma AD ile saklanır (yuklenici_id yok).
-- Uygulama: docker exec -i supabase-db psql -U supabase_admin -d postgres < backend/migration_firmam_dt_destek.sql
-- =============================================================================

BEGIN;

-- 1) DT seçili firmayı ADA göre sakla (firma_id uuid; DT firmanın uuid'si yok).
ALTER TABLE public.kullanici_profiller ADD COLUMN IF NOT EXISTS firma_dt_ad text;

-- 2) İhale firması seçilince DT seçimini TEMİZLE (ikisi aynı anda olmasın).
CREATE OR REPLACE FUNCTION public.firmami_belirle(p_yuklenici_id uuid)
RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path = public AS $$
BEGIN
  IF auth.uid() IS NULL THEN RAISE EXCEPTION 'giris gerekli'; END IF;
  IF p_yuklenici_id IS NOT NULL
     AND NOT EXISTS (SELECT 1 FROM public.yukleniciler WHERE id = p_yuklenici_id) THEN
    RAISE EXCEPTION 'firma bulunamadi';
  END IF;
  INSERT INTO public.kullanici_profiller (id, firma_id, firma_dt_ad, firma_secildi)
  VALUES (auth.uid(), p_yuklenici_id, NULL, now())
  ON CONFLICT (id) DO UPDATE SET firma_id = EXCLUDED.firma_id, firma_dt_ad = NULL, firma_secildi = now();
END; $$;
REVOKE EXECUTE ON FUNCTION public.firmami_belirle(uuid) FROM public, anon;
GRANT  EXECUTE ON FUNCTION public.firmami_belirle(uuid) TO authenticated, service_role;

-- 3) DT firmayı ADA göre "benim firmam" yap (firma_id NULL).
CREATE OR REPLACE FUNCTION public.firmami_belirle_dt(p_firma_ad text)
RETURNS void LANGUAGE plpgsql SECURITY DEFINER SET search_path = public AS $$
BEGIN
  IF auth.uid() IS NULL THEN RAISE EXCEPTION 'giris gerekli'; END IF;
  IF p_firma_ad IS NOT NULL
     AND NOT EXISTS (SELECT 1 FROM public.firma_dt_toplam WHERE ad = p_firma_ad) THEN
    RAISE EXCEPTION 'firma bulunamadi';
  END IF;
  INSERT INTO public.kullanici_profiller (id, firma_id, firma_dt_ad, firma_secildi)
  VALUES (auth.uid(), NULL, p_firma_ad, now())
  ON CONFLICT (id) DO UPDATE SET firma_id = NULL, firma_dt_ad = EXCLUDED.firma_dt_ad, firma_secildi = now();
END; $$;
REVOKE EXECUTE ON FUNCTION public.firmami_belirle_dt(text) FROM public, anon;
GRANT  EXECUTE ON FUNCTION public.firmami_belirle_dt(text) TO authenticated, service_role;

-- 4) Seçili firmayı getir — İHALE (yukleniciler) VEYA DT (firma_dt_toplam). dt_mi bayrağı eklendi.
CREATE OR REPLACE FUNCTION public.firmam_getir()
RETURNS jsonb LANGUAGE sql STABLE SECURITY DEFINER SET search_path = public AS $$
  SELECT CASE
    WHEN kp.firma_id IS NOT NULL THEN
      jsonb_build_object('firma_id', y.id, 'ad', y.ad, 'il', y.il,
        'toplam_ciro', y.toplam_ciro, 'toplam_sozlesme_sayisi', y.toplam_sozlesme_sayisi, 'dt_mi', false)
    WHEN kp.firma_dt_ad IS NOT NULL THEN
      jsonb_build_object('firma_id', NULL, 'ad', dt.ad,
        'il', (SELECT di.il FROM public.dogrudan_temin_sonuclari s
                 JOIN public.dogrudan_temin_ilanlari di ON di.dt_no = s.dt_no
                WHERE s.kazanan_firma = kp.firma_dt_ad AND di.il IS NOT NULL
                GROUP BY di.il ORDER BY count(*) DESC LIMIT 1),
        'toplam_ciro', dt.dt_bedel, 'toplam_sozlesme_sayisi', dt.dt_sozlesme, 'dt_mi', true)
    ELSE NULL END
  FROM public.kullanici_profiller kp
  LEFT JOIN public.yukleniciler y ON y.id = kp.firma_id
  LEFT JOIN public.firma_dt_toplam dt ON dt.ad = kp.firma_dt_ad
  WHERE kp.id = auth.uid();
$$;
REVOKE EXECUTE ON FUNCTION public.firmam_getir() FROM public, anon;
GRANT  EXECUTE ON FUNCTION public.firmam_getir() TO authenticated, service_role;

-- 5) DT firma için AÇIK İHALE eşleştirmesi — profil DT kazanımlarından (kategori + il).
--    firma_icin_acik_ihaleler ile AYNI kolon şeması (frontend tek yol).
CREATE OR REPLACE FUNCTION public.firma_dt_icin_acik_ihaleler(p_firma_ad text, p_limit int DEFAULT 12)
RETURNS TABLE (
  id uuid, baslik text, idare text, il text, kategori text,
  yaklasik_maliyet_min numeric, yaklasik_maliyet_max numeric, tahmini_bedel numeric,
  son_teklif_tarihi timestamptz, skor numeric, eslesme_nedeni text)
LANGUAGE sql STABLE AS $$
  WITH firma AS (
    SELECT
      (SELECT array_agg(k) FROM (
         SELECT di.kategori k FROM public.dogrudan_temin_sonuclari s
           JOIN public.dogrudan_temin_ilanlari di ON di.dt_no = s.dt_no
          WHERE public.normalize_firma(s.kazanan_firma) = public.normalize_firma(p_firma_ad) AND di.kategori IS NOT NULL
          GROUP BY di.kategori ORDER BY count(*) DESC LIMIT 5) t)          AS kategoriler,
      (SELECT array_agg(DISTINCT di.il) FROM public.dogrudan_temin_sonuclari s
         JOIN public.dogrudan_temin_ilanlari di ON di.dt_no = s.dt_no
        WHERE public.normalize_firma(s.kazanan_firma) = public.normalize_firma(p_firma_ad) AND di.il IS NOT NULL)          AS iller
  )
  SELECT i.id, i.baslik, i.idare, i.il, i.kategori,
         i.yaklasik_maliyet_min::numeric, i.yaklasik_maliyet_max::numeric, i.tahmini_bedel::numeric,
         i.son_teklif_tarihi::timestamptz,
         round(( (CASE WHEN i.kategori = ANY(f.kategoriler) THEN 40 ELSE 0 END)
               + (CASE WHEN i.il = ANY(f.iller) THEN 15 ELSE 0 END) )::numeric) AS skor,
         ( (CASE WHEN i.kategori = ANY(f.kategoriler) THEN 'Uzmanlık alanınız (DT geçmişi)' ELSE 'Benzer konu' END)
         || (CASE WHEN i.il = ANY(f.iller) THEN ' · çalıştığınız il' ELSE '' END) ) AS eslesme_nedeni
    FROM public.ilanlar i, firma f
   WHERE i.durum = 'aktif' AND i.son_teklif_tarihi >= now()
     AND f.kategoriler IS NOT NULL AND i.kategori = ANY(f.kategoriler)
   ORDER BY skor DESC, i.son_teklif_tarihi ASC NULLS LAST
   LIMIT p_limit;
$$;
REVOKE EXECUTE ON FUNCTION public.firma_dt_icin_acik_ihaleler(text,int) FROM public, anon;
GRANT  EXECUTE ON FUNCTION public.firma_dt_icin_acik_ihaleler(text,int) TO authenticated, service_role;

-- 6) Dashboard wrapper — DT firma ise DT eşleştirmesine dallan (oturumdan okur).
CREATE OR REPLACE FUNCTION public.firmam_acik_ihaleler(p_limit int DEFAULT 12)
RETURNS TABLE (
  id uuid, baslik text, idare text, il text, kategori text,
  yaklasik_maliyet_min numeric, yaklasik_maliyet_max numeric, tahmini_bedel numeric,
  son_teklif_tarihi timestamptz, skor numeric, eslesme_nedeni text)
LANGUAGE plpgsql STABLE SECURITY DEFINER SET search_path = public AS $$
DECLARE v_fid uuid; v_dt text;
BEGIN
  SELECT firma_id, firma_dt_ad INTO v_fid, v_dt FROM public.kullanici_profiller WHERE id = auth.uid();
  IF v_dt IS NOT NULL THEN
    RETURN QUERY SELECT * FROM public.firma_dt_icin_acik_ihaleler(v_dt, p_limit);
  ELSE
    RETURN QUERY SELECT * FROM public.firma_icin_acik_ihaleler(v_fid, p_limit, 5);
  END IF;
END; $$;
REVOKE EXECUTE ON FUNCTION public.firmam_acik_ihaleler(int) FROM public, anon;
GRANT  EXECUTE ON FUNCTION public.firmam_acik_ihaleler(int) TO authenticated, service_role;

-- 7) DT firma KIRILIMI (panel: sektör etiketi + il haritası + kurum sayısı) — tek jsonb.
CREATE OR REPLACE FUNCTION public.firma_dt_kirilim(p_firma_ad text)
RETURNS jsonb LANGUAGE sql STABLE SECURITY DEFINER SET search_path = public AS $$
  WITH d AS (
    SELECT di.il, di.kategori, di.idare, s.kazanan_bedel
      FROM public.dogrudan_temin_sonuclari s
      JOIN public.dogrudan_temin_ilanlari di ON di.dt_no = s.dt_no
     WHERE s.kazanan_firma = p_firma_ad
  )
  SELECT jsonb_build_object(
    'sektor', (SELECT jsonb_build_object('ad', kategori, 'sayi', count(*))
                 FROM d WHERE kategori IS NOT NULL GROUP BY kategori ORDER BY count(*) DESC LIMIT 1),
    'iller', (SELECT COALESCE(jsonb_agg(jsonb_build_object('il', il, 'sayi', c, 'bedel', b) ORDER BY c DESC), '[]'::jsonb)
                FROM (SELECT il, count(*) c, COALESCE(sum(kazanan_bedel),0) b
                        FROM d WHERE il IS NOT NULL GROUP BY il) x),
    'kurum_sayisi', (SELECT count(DISTINCT idare) FROM d WHERE idare IS NOT NULL)
  );
$$;
REVOKE EXECUTE ON FUNCTION public.firma_dt_kirilim(text) FROM public, anon;
GRANT  EXECUTE ON FUNCTION public.firma_dt_kirilim(text) TO authenticated, service_role;

-- 8) DT firma ARAMA (tr_fold + trigram GIN; ilike İ/ı tuzağını atlar — yukleniciler.arama_fold deseni).
--    280K satırda seq scan ~1,3s → trigram index ile ms'ye iner. tr_fold IMMUTABLE (functional index şartı).
CREATE INDEX IF NOT EXISTS idx_firma_dt_toplam_ad_trgm
  ON public.firma_dt_toplam USING gin (public.tr_fold(ad) gin_trgm_ops);
CREATE OR REPLACE FUNCTION public.firma_dt_ara(p_q text, p_limit int DEFAULT 6)
RETURNS TABLE (ad text, dt_sozlesme bigint, dt_bedel numeric)
LANGUAGE sql STABLE SECURITY DEFINER SET search_path = public AS $$
  SELECT ad, dt_sozlesme, dt_bedel
    FROM public.firma_dt_toplam
   WHERE public.tr_fold(ad) LIKE '%'||public.tr_fold(p_q)||'%'
   ORDER BY dt_bedel DESC NULLS LAST
   LIMIT p_limit;
$$;
REVOKE EXECUTE ON FUNCTION public.firma_dt_ara(text,int) FROM public, anon;
GRANT  EXECUTE ON FUNCTION public.firma_dt_ara(text,int) TO authenticated, service_role;

COMMIT;

NOTIFY pgrst, 'reload schema';

-- DOĞRULAMA:
--   SELECT public.firmami_belirle_dt('DİNÇ LAZER MAKİNE İTHALAT İHRACAT SANAYİ VE TİCARET LİMİTED ŞİRKETİ');
--   SELECT public.firmam_getir();          -- dt_mi=true, toplam_sozlesme_sayisi=11, ciro=1300750
--   SELECT public.firma_dt_kirilim('DİNÇ LAZER MAKİNE İTHALAT İHRACAT SANAYİ VE TİCARET LİMİTED ŞİRKETİ');
