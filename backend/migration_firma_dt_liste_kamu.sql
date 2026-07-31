-- ============================================================================
-- Firma DT liste sekmesi + harita firma sıralamasında KAMU KURULUŞU filtresi (31 Tem 2026)
-- ----------------------------------------------------------------------------
-- ① Kullanıcı: harita firma sıralamasında DMO / cezaevi (İşyurtları) / PTT gibi KAMU
--    kuruluşları "kazanan firma" olarak çıkıyor (veri DOĞRU — bunlar DT'de gerçek tedarikçi,
--    ama rakip firma analizinde gürültü). Karar: VARSAYILAN GİZLE + toggle.
--    → firma_kurum_mu(ad) sınıflandırıcı + il_sektor_firmalar(_dt)'ye p_kamu_dahil (default false).
-- ② Kullanıcı: firma-analiz'de "Katıldığı İhaleler" (var) yanında ayrı "Katıldığı Doğrudan
--    Teminler" sekmesi + satır tıklanınca DT detayına gitsin. → firma_dt_liste RPC.
--
-- Çalıştır (superuser):
--   docker exec -i supabase-db psql -U supabase_admin -d postgres < backend/migration_firma_dt_liste_kamu.sql
-- ============================================================================

-- ── 1) Kamu kuruluşu sınıflandırıcı (kazanan ADI kurumsal mı) ──
-- Kurumsal SONEK sonda (tr_fold'lu; ortada eşleşme yok → yanlış pozitif düşük) + birkaç
-- bilinen devlet tedarikçisi (DMO/PTT/İşyurtları) ad-içi. Özel firmalar ŞİRKETİ/LTD/A.Ş./
-- SANAYİ/TİCARET ile biter → soneklere takılmaz.
CREATE OR REPLACE FUNCTION public.firma_kurum_mu(p_ad text)
RETURNS boolean IMMUTABLE LANGUAGE sql AS $$
  SELECT p_ad IS NOT NULL AND (
    public.tr_fold(p_ad) ~ '(mudurlugu|baskanligi|bakanligi|belediyesi|belediye baskanligi|universitesi|rektorlugu|valiligi|kaymakamligi|komutanligi|genel sekreterligi|il ozel idaresi|hastanesi|cezaevi|muftulugu|il saglik mudurlugu|halk sagligi merkezi)$'
    OR public.tr_fold(p_ad) ~ '(devlet malzeme ofisi|ceza infaz kurumu|isyurtlari|isyurdu|posta ve telgraf|kizilay|orman genel mudurlugu)'
  );
$$;
GRANT EXECUTE ON FUNCTION public.firma_kurum_mu(text) TO anon, authenticated, service_role;

-- ── 2) Harita firma sıralaması: p_kamu_dahil (default false → kamu kuruluşları GİZLİ) ──
--    İmza 5→6 arg; eski 5-arg çağrılar default'la düşer. Kurumsal süzme, agregasyondan
--    SONRA (dış sorguda temsili `ad` üzerinden) → GROUP BY'ı bozmaz.
DROP FUNCTION IF EXISTS public.il_sektor_firmalar(text[], text, int, boolean, text);
CREATE OR REPLACE FUNCTION public.il_sektor_firmalar(
  p_il_folds text[], p_kategori text DEFAULT NULL, p_limit int DEFAULT 8,
  p_son_yil boolean DEFAULT false, p_olcut text DEFAULT 'bedel', p_kamu_dahil boolean DEFAULT false)
RETURNS TABLE(ad text, sozlesme bigint, toplam_bedel numeric)
LANGUAGE sql STABLE AS $$
  SELECT ad, sozlesme, toplam_bedel FROM (
    SELECT (array_agg(ad ORDER BY son_tarih DESC NULLS LAST))[1] AS ad,
           sum(CASE WHEN p_son_yil THEN sozlesme_1y ELSE sozlesme END)::bigint AS sozlesme,
           sum(CASE WHEN p_son_yil THEN bedel_1y   ELSE toplam_bedel END)      AS toplam_bedel
    FROM public.il_sektor_firma_mv
    WHERE il_fold = ANY(p_il_folds) AND (p_kategori IS NULL OR kategori = p_kategori)
    GROUP BY firma_norm
    HAVING sum(CASE WHEN p_son_yil THEN sozlesme_1y ELSE sozlesme END) > 0
  ) t
  WHERE p_kamu_dahil OR NOT public.firma_kurum_mu(ad)
  ORDER BY CASE WHEN p_olcut='sozlesme' THEN sozlesme::numeric ELSE toplam_bedel END DESC, sozlesme DESC
  LIMIT GREATEST(1, LEAST(COALESCE(p_limit, 8), 50));
$$;
ALTER FUNCTION public.il_sektor_firmalar(text[], text, int, boolean, text, boolean) SET statement_timeout = '15s';
GRANT EXECUTE ON FUNCTION public.il_sektor_firmalar(text[], text, int, boolean, text, boolean) TO anon, authenticated, service_role;

DROP FUNCTION IF EXISTS public.il_sektor_firmalar_dt(text[], text, int, boolean, text);
CREATE OR REPLACE FUNCTION public.il_sektor_firmalar_dt(
  p_il_folds text[], p_kategori text DEFAULT NULL, p_limit int DEFAULT 8,
  p_son_yil boolean DEFAULT false, p_olcut text DEFAULT 'bedel', p_kamu_dahil boolean DEFAULT false)
RETURNS TABLE(ad text, sozlesme bigint, toplam_bedel numeric)
LANGUAGE sql STABLE SECURITY DEFINER SET search_path = public AS $$
  SELECT ad, sozlesme, toplam_bedel FROM (
    SELECT (array_agg(ad ORDER BY son_tarih DESC NULLS LAST))[1] AS ad,
           sum(CASE WHEN p_son_yil THEN sozlesme_1y ELSE sozlesme END)::bigint AS sozlesme,
           sum(CASE WHEN p_son_yil THEN bedel_1y   ELSE toplam_bedel END)      AS toplam_bedel
    FROM public.il_sektor_firma_dt_mv
    WHERE il_fold = ANY(p_il_folds) AND (p_kategori IS NULL OR kategori = p_kategori)
    GROUP BY firma_norm
    HAVING sum(CASE WHEN p_son_yil THEN sozlesme_1y ELSE sozlesme END) > 0
  ) t
  WHERE p_kamu_dahil OR NOT public.firma_kurum_mu(ad)
  ORDER BY CASE WHEN p_olcut='sozlesme' THEN sozlesme::numeric ELSE toplam_bedel END DESC, sozlesme DESC
  LIMIT GREATEST(1, LEAST(COALESCE(p_limit, 8), 50));
$$;
ALTER FUNCTION public.il_sektor_firmalar_dt(text[], text, int, boolean, text, boolean) SET statement_timeout = '20s';
REVOKE EXECUTE ON FUNCTION public.il_sektor_firmalar_dt(text[], text, int, boolean, text, boolean) FROM public, anon;
GRANT  EXECUTE ON FUNCTION public.il_sektor_firmalar_dt(text[], text, int, boolean, text, boolean) TO authenticated, service_role;

-- ── 3) firma-analiz "Katıldığı Doğrudan Teminler" listesi (bireysel DT kazanımları) ──
--    firma_dt_ozet ile AYNI eşleşme (tr_fold(kazanan_firma)=tr_fold(ad), idx_dt_sonuc_kazanan_fold).
--    Toplam sayı zaten firma_dt_ozet.dt_sayisi'nde → burada yalnız sayfa döner. dt_no ile
--    v1-dt-detay'a link. idare anon'a kapalı ama bu RPC authenticated + SECURITY DEFINER.
CREATE OR REPLACE FUNCTION public.firma_dt_liste(
  p_firma_ad text, p_limit int DEFAULT 20, p_offset int DEFAULT 0)
RETURNS TABLE(dt_no text, baslik text, il text, kategori text, tur text,
              tarih date, kazanan_bedel numeric, idare text)
LANGUAGE sql STABLE SECURITY DEFINER SET search_path = public AS $$
  SELECT s.dt_no, i.baslik, i.il, i.kategori, i.tur, i.tarih, s.kazanan_bedel, i.idare
  FROM public.dogrudan_temin_sonuclari s
  JOIN public.dogrudan_temin_ilanlari i ON i.dt_no = s.dt_no
  WHERE s.kazanan_firma IS NOT NULL
    AND public.tr_fold(s.kazanan_firma) = public.tr_fold(p_firma_ad)
  ORDER BY i.tarih DESC NULLS LAST, s.kazanan_bedel DESC NULLS LAST
  LIMIT LEAST(GREATEST(p_limit, 1), 100) OFFSET GREATEST(p_offset, 0);
$$;
ALTER FUNCTION public.firma_dt_liste(text, int, int) SET statement_timeout = '15s';
REVOKE EXECUTE ON FUNCTION public.firma_dt_liste(text, int, int) FROM public, anon;
GRANT  EXECUTE ON FUNCTION public.firma_dt_liste(text, int, int) TO authenticated, service_role;

NOTIFY pgrst, 'reload schema';

-- Doğrulama:
--   SELECT public.firma_kurum_mu('KALECİK AÇIK CEZAEVİ MÜDÜRLÜĞÜ');   -- t
--   SELECT public.firma_kurum_mu('SELES MEDİKAL SANAYİ VE TİCARET LİMİTED ŞİRKETİ'); -- f
--   SELECT public.firma_kurum_mu('DEVLET MALZEME OFİSİ GENEL MÜDÜRLÜĞÜ'); -- t
--   SELECT ad,sozlesme FROM il_sektor_firmalar_dt(ARRAY['ankara'],NULL,8,true,'sozlesme',false); -- kamu YOK
--   SELECT count(*) FROM firma_dt_liste('METRO GROSMARKET BAKIRKÖY ALIŞVERİŞ HİZMETLERİ TİCARET LİMİTED ŞİRKETİ',20,0);
