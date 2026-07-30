-- ============================================================
-- MADDE 6 (v4) — Frekans-ağırlıklı + takip-bonuslu eşleşme (31 Tem 2026)
-- ------------------------------------------------------------
-- KULLANICI ONAYI (tablo):
--   A) Firma-Geçmişi: Sektör 100 + 50×sektör_payı · Kurum +30 · İl +10.
--      sektör_payı = firmanın o kategorideki kazanımı ÷ toplam kazanımı → dominant sektör öne.
--      (Örn. 10 klima/7 gıda/2 inşaat → klima 126 > gıda 118 > inşaat 106; hepsi kurum/il'i ezer.)
--   B) Takip Bonusu (kullanıcının takip listesi): Takip sektör +15 · Takip kurum +15 · Takip firma 0.
--      Additive (çarpan değil) → firmanın geçmişinde olmasa da takip edileni yukarı çeker.
-- Bedel-yakınlığı yalnız AYNI katman içi tiebreaker. İl gerekçede yalnız TEK sinyalse.
--
-- İmza 3→5 arg (p_takip_sektorler, p_takip_idareler eklendi) → DROP + CREATE. PostgREST 3-arg
-- çağrıları da bu 5-arg fonksiyona düşer (yeni argümanlar DEFAULT NULL). Wrapper follows geçirir.
--
-- Çalıştır (superuser):
--   docker exec -i supabase-db psql -U supabase_admin -d postgres < backend/migration_firmam_eslesme_v4.sql
-- ============================================================

DROP FUNCTION IF EXISTS public.firma_icin_acik_ihaleler(uuid,int,numeric);

CREATE OR REPLACE FUNCTION public.firma_icin_acik_ihaleler(
  p_yuklenici_id uuid, p_limit int DEFAULT 12, p_bant numeric DEFAULT 3,
  p_takip_sektorler text[] DEFAULT NULL, p_takip_idareler text[] DEFAULT NULL)
RETURNS TABLE (
  id uuid, baslik text, idare text, il text, kategori text,
  yaklasik_maliyet_min numeric, yaklasik_maliyet_max numeric, tahmini_bedel numeric,
  son_teklif_tarihi timestamptz, skor numeric, eslesme_nedeni text)
LANGUAGE sql STABLE AS $$
  WITH firma AS (
    SELECT
      -- kategori → kazanım SAYISI haritası (frekans için) + toplam
      (SELECT jsonb_object_agg(k, c) FROM (
         SELECT i.kategori k, count(*) c FROM public.ihale_sonuclari s JOIN public.ilanlar i ON i.id=s.ilan_id
         WHERE s.yuklenici_id=p_yuklenici_id AND i.kategori IS NOT NULL
         GROUP BY i.kategori) t)                                          AS kat_say,
      (SELECT count(*) FROM public.ihale_sonuclari s JOIN public.ilanlar i ON i.id=s.ilan_id
         WHERE s.yuklenici_id=p_yuklenici_id AND i.kategori IS NOT NULL)  AS kat_toplam,
      (SELECT array_agg(DISTINCT i.il) FROM public.ihale_sonuclari s JOIN public.ilanlar i ON i.id=s.ilan_id
         WHERE s.yuklenici_id=p_yuklenici_id AND i.il IS NOT NULL)        AS iller,
      (SELECT array_agg(k) FROM (
         SELECT i.idare k FROM public.ihale_sonuclari s JOIN public.ilanlar i ON i.id=s.ilan_id
         WHERE s.yuklenici_id=p_yuklenici_id AND i.idare IS NOT NULL
         GROUP BY i.idare ORDER BY count(*) DESC LIMIT 8) t)              AS idareler,
      (SELECT string_agg(i2.baslik,' ') FROM (
         SELECT i3.baslik FROM public.ihale_sonuclari s2 JOIN public.ilanlar i3 ON i3.id=s2.ilan_id
         WHERE s2.yuklenici_id=p_yuklenici_id LIMIT 50) i2)              AS basliklar,
      (SELECT percentile_cont(0.5) WITHIN GROUP (ORDER BY COALESCE(s.kazanan_teklif,s.sozlesme_bedeli))
         FROM public.ihale_sonuclari s WHERE s.yuklenici_id=p_yuklenici_id) AS bedel
  ),
  aday AS (
    SELECT i.id, i.baslik, i.idare, i.il, i.kategori,
           i.yaklasik_maliyet_min, i.yaklasik_maliyet_max, i.tahmini_bedel, i.son_teklif_tarihi,
           (f.kat_say ? i.kategori)                                                   AS m_kat,
           COALESCE((f.kat_say ->> i.kategori)::numeric, 0)                           AS kat_adet,
           EXISTS (SELECT 1 FROM public.ihale_konu_kelimeleri(f.basliklar) t
                   WHERE public.tr_fold(i.baslik) LIKE '%'||t.kelime||'%')            AS m_kelime,
           (f.idareler IS NOT NULL AND i.idare = ANY(f.idareler))                     AS m_idare,
           (i.il = ANY(f.iller))                                                      AS m_il,
           (p_takip_sektorler IS NOT NULL AND i.kategori = ANY(p_takip_sektorler))    AS m_tsektor,
           (p_takip_idareler  IS NOT NULL AND i.idare    = ANY(p_takip_idareler))     AS m_tkurum,
           f.kat_toplam, f.bedel AS fbedel
    FROM public.ilanlar i, firma f
    WHERE i.durum='aktif'
      AND (i.son_teklif_tarihi IS NULL OR i.son_teklif_tarihi >= now())
      AND ( (f.kat_say ? i.kategori)
         OR (f.idareler IS NOT NULL AND i.idare = ANY(f.idareler))
         OR i.il = ANY(f.iller)
         OR (p_takip_sektorler IS NOT NULL AND i.kategori = ANY(p_takip_sektorler))
         OR (p_takip_idareler  IS NOT NULL AND i.idare    = ANY(p_takip_idareler))
         OR EXISTS (SELECT 1 FROM public.ihale_konu_kelimeleri(f.basliklar) t
                    WHERE public.tr_fold(i.baslik) LIKE '%'||t.kelime||'%') )
  )
  SELECT id, baslik, idare, il, kategori,
         yaklasik_maliyet_min::numeric, yaklasik_maliyet_max::numeric, tahmini_bedel::numeric,
         son_teklif_tarihi::timestamptz,
         ( (CASE WHEN m_kat    THEN 100 + round(50 * kat_adet / NULLIF(kat_toplam,0))
                 WHEN m_kelime THEN 100 ELSE 0 END)
         + (CASE WHEN m_idare  THEN 30 ELSE 0 END)
         + (CASE WHEN m_il     THEN 10 ELSE 0 END)
         + (CASE WHEN m_tsektor THEN 15 ELSE 0 END)
         + (CASE WHEN m_tkurum  THEN 15 ELSE 0 END) )::numeric                         AS skor,
         NULLIF(concat_ws(' · ',
           CASE WHEN m_kat OR m_kelime THEN 'Uzmanlık alanınız' END,
           CASE WHEN m_idare   THEN 'sık çalıştığınız idare' END,
           CASE WHEN m_tsektor THEN 'takip ettiğiniz sektör' END,
           CASE WHEN m_tkurum  THEN 'takip ettiğiniz kurum' END,
           CASE WHEN m_il AND NOT (m_kat OR m_kelime) AND NOT m_idare THEN 'çalıştığınız il' END
         ), '')                                                                         AS eslesme_nedeni
  FROM aday
  ORDER BY
    ( (CASE WHEN m_kat THEN 100 + round(50 * kat_adet / NULLIF(kat_toplam,0))
            WHEN m_kelime THEN 100 ELSE 0 END)
    + (CASE WHEN m_idare THEN 30 ELSE 0 END) + (CASE WHEN m_il THEN 10 ELSE 0 END)
    + (CASE WHEN m_tsektor THEN 15 ELSE 0 END) + (CASE WHEN m_tkurum THEN 15 ELSE 0 END) ) DESC,
    (CASE WHEN fbedel IS NULL OR fbedel<=0 THEN 0
          ELSE 1 - LEAST(abs(ln(GREATEST(
                 COALESCE(NULLIF(yaklasik_maliyet_max,0),NULLIF(tahmini_bedel,0),1),1)::numeric/fbedel))
                 /ln(GREATEST(p_bant,1.0001)),1) END) DESC,
    son_teklif_tarihi ASC NULLS LAST
  LIMIT p_limit;
$$;
REVOKE EXECUTE ON FUNCTION public.firma_icin_acik_ihaleler(uuid,int,numeric,text[],text[]) FROM public, anon;
GRANT  EXECUTE ON FUNCTION public.firma_icin_acik_ihaleler(uuid,int,numeric,text[],text[]) TO authenticated, service_role;

-- Wrapper: kullanıcının takip ettiği sektör + kurumları alıp geçirir (takip firma GEÇMEZ).
CREATE OR REPLACE FUNCTION public.firmam_acik_ihaleler(p_limit int DEFAULT 12)
RETURNS TABLE (
  id uuid, baslik text, idare text, il text, kategori text,
  yaklasik_maliyet_min numeric, yaklasik_maliyet_max numeric, tahmini_bedel numeric,
  son_teklif_tarihi timestamptz, skor numeric, eslesme_nedeni text)
LANGUAGE sql STABLE SECURITY DEFINER SET search_path = public AS $$
  SELECT * FROM public.firma_icin_acik_ihaleler(
    (SELECT firma_id FROM public.kullanici_profiller WHERE id = auth.uid()),
    p_limit, 3,
    (SELECT array_agg(sektor)   FROM public.takip_sektorler WHERE kullanici_id = auth.uid()),
    (SELECT array_agg(idare_ad) FROM public.takip_idareler  WHERE kullanici_id = auth.uid()));
$$;
REVOKE EXECUTE ON FUNCTION public.firmam_acik_ihaleler(int) FROM public, anon;
GRANT  EXECUTE ON FUNCTION public.firmam_acik_ihaleler(int) TO authenticated, service_role;

NOTIFY pgrst, 'reload schema';
