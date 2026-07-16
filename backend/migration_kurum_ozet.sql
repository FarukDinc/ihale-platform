-- ============================================================
-- İhaleGlobal — kurum_ozet(p_idare) RPC
--
-- Kök neden: kurum-analiz.html topluCek() bir idarenin TÜM ilanlarını
-- .ilike('idare','%KURUM%') + 1000'erli range döngüsüyle client'a indirip
-- 8 breakdown'ı (aylık trend / yıllık / tür / il / kategori / usul / durum
-- + KPI'lar) JS'te hesaplıyordu. En büyük idare 7.072 ilan → worst-case
-- 8 ardışık fetch + client aggregation (client-load-all kalıbı, bkz.
-- rekabet_ozet reçetesi: migration_rekabet_ozet.sql).
--
-- Tek RPC, idare ILIKE filtresine göre KPI + tüm gruplamaları jsonb döndürür.
-- idare üzerinde trgm GIN index mevcut (ILIKE'ı karşılar, seq-scan yok).
-- Şekiller client'taki eski hesaplamalarla BİREBİR aynı:
--   kpi.aktif        = son_teklif_tarihi > now()          (durum kolonu DEĞİL)
--   kpi.toplam_butce = sum(yaklasik_maliyet_min)
--   aylik_trend      = son 24 ay, COALESCE(ilan_tarihi, son_teklif_tarihi)
--   tur 'Diğer' / kategori 'Kategorisiz' (top 12) / usul 'Belirtilmemiş' fallback'leri
--   durum.aktif      = durum='aktif', kapandi = geri kalan (NULL dahil)
--
-- Additive/güvenli: CREATE OR REPLACE (idempotent) + sadece EXECUTE GRANT.
-- SECURITY DEFINER: yalnızca aggregate döndürür, satır ifşası yok.
--
-- Çalıştırma: docker exec -i supabase-db psql -U postgres -d postgres -f - < backend/migration_kurum_ozet.sql
-- ============================================================

BEGIN;

CREATE OR REPLACE FUNCTION public.kurum_ozet(p_idare text)
RETURNS jsonb
LANGUAGE sql STABLE SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
  WITH f AS (
    SELECT tur, il, usul, kategori, durum,
           yaklasik_maliyet_min AS m,
           son_teklif_tarihi,
           COALESCE(ilan_tarihi, son_teklif_tarihi) AS tarih
    FROM public.ilanlar
    WHERE idare ILIKE '%' || p_idare || '%'
  )
  SELECT jsonb_build_object(
    'kpi', jsonb_build_object(
      'toplam',       (SELECT count(*) FROM f),
      'aktif',        (SELECT count(*) FROM f WHERE son_teklif_tarihi > now()),
      'toplam_butce', (SELECT COALESCE(sum(m), 0) FROM f),
      'il_sayisi',    (SELECT count(DISTINCT il) FROM f WHERE il IS NOT NULL)
    ),
    'aylik_trend', (SELECT COALESCE(jsonb_object_agg(ay, n), '{}'::jsonb)
                    FROM (SELECT to_char(tarih, 'YYYY-MM') ay, count(*) n
                          FROM f WHERE tarih IS NOT NULL AND tarih >= (now() - interval '24 months')
                          GROUP BY 1) x),
    'yillik',   (SELECT COALESCE(jsonb_agg(jsonb_build_object('k', k, 'n', n) ORDER BY k), '[]'::jsonb)
                 FROM (SELECT to_char(tarih, 'YYYY') k, count(*) n
                       FROM f WHERE tarih IS NOT NULL GROUP BY 1) x),
    'tur',      (SELECT COALESCE(jsonb_agg(jsonb_build_object('k', k, 'n', n) ORDER BY n DESC), '[]'::jsonb)
                 FROM (SELECT COALESCE(NULLIF(tur, ''), 'Diğer') k, count(*) n FROM f GROUP BY 1) x),
    'il',       (SELECT COALESCE(jsonb_agg(jsonb_build_object('k', k, 'n', n) ORDER BY n DESC), '[]'::jsonb)
                 FROM (SELECT il k, count(*) n FROM f WHERE il IS NOT NULL GROUP BY il) x),
    'kategori', (SELECT COALESCE(jsonb_agg(jsonb_build_object('k', k, 'n', n) ORDER BY n DESC), '[]'::jsonb)
                 FROM (SELECT COALESCE(NULLIF(kategori, ''), 'Kategorisiz') k, count(*) n
                       FROM f GROUP BY 1 ORDER BY count(*) DESC LIMIT 12) x),
    'usul',     (SELECT COALESCE(jsonb_agg(jsonb_build_object('k', k, 'n', n) ORDER BY n DESC), '[]'::jsonb)
                 FROM (SELECT COALESCE(NULLIF(usul, ''), 'Belirtilmemiş') k, count(*) n FROM f GROUP BY 1) x),
    'durum', jsonb_build_object(
      'aktif',   (SELECT count(*) FROM f WHERE durum = 'aktif'),
      'kapandi', (SELECT count(*) FROM f WHERE durum IS DISTINCT FROM 'aktif')
    )
  );
$$;

GRANT EXECUTE ON FUNCTION public.kurum_ozet(text) TO anon, authenticated, service_role;

COMMIT;

NOTIFY pgrst, 'reload schema';

-- Kontrol (en büyük idare ~7.072 ilan ile)
-- SELECT kurum_ozet('İl Sağlık Müdürlüğü')->'kpi';
