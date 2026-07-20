-- ============================================================================
-- İhaleGlobal — rekabet_ozet + kurum_ozet: trend ekseni ve kpi.aktif düzeltmesi
--                                                              (20 Tem 2026)
--
-- SORUN (canlı REST ile bağımsız ölçüldü, 20 Tem):
--   ilanlar toplam        357.207
--   ilan_tarihi dolu       15.245  (%4,27)   ← iki RPC'nin trend ekseni buydu
--   son_teklif_tarihi dolu 16.669  (%4,67)   ← kpi.aktif'in tabanı buydu
--   etkin_tarih dolu      351.883  (%98,51)
--   durum='aktif'           4.954
--
--   Yani "Aylık Trend" ve "Yıllık Dağılım" grafikleri verinin ~%5'ine dayanıyordu;
--   kurum_ozet.kpi.aktif ise %4,67 dolu bir kolona `> now()` uygulayıp neredeyse
--   her kurumda 0'a yakın "aktif ihale" gösteriyordu. İkisi de YANLIŞ RAKAM —
--   eksik özellik değil.
--
--   Kök neden: 356.904 ihalenin %95'inde üç tarih alanı da boş (sonuç-backfill'inden
--   gelen geçmiş kayıtlar). migration_etkin_tarih.sql bunu 19 Tem'de `etkin_tarih`
--   ekseniyle çözdü ama bu iki RPC eski eksende kaldı.
--
-- ── DEĞİŞEN İKİ ŞEY ────────────────────────────────────────────────────────
--   1) trend/yıllık ekseni:  COALESCE(ilan_tarihi, son_teklif_tarihi) → etkin_tarih
--   2) kurum_ozet.kpi.aktif: son_teklif_tarihi > now()  →  durum = 'aktif'
--
-- ⚠️ ANLAM DEĞİŞİYOR — ARAYÜZ ETİKETİ DE DEĞİŞMELİ:
--   `etkin_tarih` = "eldeki en iyi tarih" (öncelik: son_teklif > ilan > ihale >
--   sonuç). 335K geçmiş kayıtta bu SONUÇ tarihidir, ilan tarihi değil. Dolayısıyla
--   grafik artık "ne zaman ilan edildi" değil "ne zaman hareket oldu" demektir.
--   `etkin_tarih_kaynak` kolonu hangisi olduğunu satır satır söylüyor.
--   → rekabet-analizi.html ve kurum-analiz.html'de başlık "İlan Trendi" DEĞİL,
--     "Aylık İhale Hareketi" gibi olmalı (aynı commit'te yapıldı).
--   Eski ekseni korumak da bir seçenekti ama o grafiğin %95'i boş kalıyordu —
--   "az ama doğru" değil, "neredeyse hiç" durumuydu.
--
-- ⚠️ kpi.aktif neden durum='aktif':
--   son_teklif_tarihi yalnız %4,67 dolu → `> now()` çoğu kurumda 0 verir.
--   `durum` kolonu gece `ilan_durum_bayatlat()` ile bakımlı ve %100 dolu.
--   NOT: kurum_ozet'te zaten bir `durum.aktif` alanı vardı ve DOĞRU tanımı
--   kullanıyordu (durum='aktif'). Yani aynı RPC içinde iki çelişkili "aktif"
--   vardı; bu düzeltme ikisini hizalıyor.
--
-- ── ÜÇ TUZAK (bu dosya hepsini ele alıyor) ─────────────────────────────────
--   A) CREATE OR REPLACE FUNCTION, fonksiyonun proconfig'ini SIFIRLAR →
--      migration_rekabet_ozet_timeout.sql'in koyduğu `SET statement_timeout='20s'`
--      UÇAR ve rekabet-analizi aralıklı 3s timeout'a geri döner (o hata bir kez
--      yaşandı). Bu yüzden ALTER FUNCTION en sonda TEKRAR uygulanıyor.
--   B) Orijinal dosyalar `GRANT EXECUTE ... TO anon` içeriyor. O satırlar BURAYA
--      KOPYALANMADI: migration_anon_maske.sql:90-96 her iki fonksiyonu anon'dan
--      REVOKE edip yalnız authenticated+service_role'e vermişti (isim/kurum
--      döndürdükleri için). Kopyalansaydı MASKE GERİ AÇILIRDI.
--      CREATE OR REPLACE aynı OID'yi koruduğu için mevcut ACL zaten korunur;
--      yine de sonda doğrulanıyor.
--   C) kurum_ozet SECURITY DEFINER, rekabet_ozet DEĞİL. Bu asimetri korunuyor —
--      rekabet_ozet çağıranın yetkisiyle koştuğu için gövdesine anon'a kapalı
--      bir kolon/tablo eklenirse misafirde 42501 verir. Bu dosya yeni kolon
--      eklemiyor (etkin_tarih anon'a açık: migration_anon_maske kolon listesinde).
--
-- Çalıştırma:
--   docker exec -i supabase-db psql -U postgres -d postgres < backend/migration_analiz_eksen_fix.sql
-- Idempotent. Şema değişmiyor, yalnız iki fonksiyon gövdesi.
-- ============================================================================

BEGIN;

-- ── 1) rekabet_ozet — yalnız `tarih` ifadesi değişti, gerisi birebir aynı ────
CREATE OR REPLACE FUNCTION public.rekabet_ozet(
  p_durum text DEFAULT NULL, p_il text DEFAULT NULL, p_kategori text DEFAULT NULL
)
RETURNS jsonb
LANGUAGE sql STABLE
AS $$
  WITH f AS (
    SELECT tur, il, idare, usul, yaklasik_maliyet_min AS m, kategori,
           -- ESKİDEN: COALESCE(ilan_tarihi, son_teklif_tarihi) → %4,27 dolu eksen.
           -- COALESCE zinciri korundu ki etkin_tarih'in boş olduğu ~%1,5 satır
           -- da eski davranışa düşsün (regresyon değil, saf kazanç).
           COALESCE(etkin_tarih, ilan_tarihi, son_teklif_tarihi) AS tarih
    FROM public.ilanlar
    WHERE (p_durum    IS NULL OR durum    = p_durum)
      AND (p_il       IS NULL OR il       = p_il)
      AND (p_kategori IS NULL OR kategori = p_kategori)
  )
  SELECT jsonb_build_object(
    'toplam',       (SELECT count(*) FROM f),
    'ort_maliyet',  (SELECT COALESCE(round(avg(m)),0) FROM f WHERE m > 0),
    'maliyet_adet', (SELECT count(*) FROM f WHERE m > 0),
    'tur',      (SELECT COALESCE(jsonb_agg(jsonb_build_object('k',k,'n',n) ORDER BY n DESC),'[]'::jsonb)
                 FROM (SELECT tur k, count(*) n FROM f WHERE tur IS NOT NULL GROUP BY tur) x),
    'il',       (SELECT COALESCE(jsonb_agg(jsonb_build_object('k',k,'n',n) ORDER BY n DESC),'[]'::jsonb)
                 FROM (SELECT il k, count(*) n FROM f WHERE il IS NOT NULL GROUP BY il) x),
    'usul',     (SELECT COALESCE(jsonb_agg(jsonb_build_object('k',k,'n',n) ORDER BY n DESC),'[]'::jsonb)
                 FROM (SELECT usul k, count(*) n FROM f WHERE usul IS NOT NULL GROUP BY usul ORDER BY count(*) DESC LIMIT 60) x),
    'kategori', (SELECT COALESCE(jsonb_agg(jsonb_build_object('k',k,'n',n) ORDER BY n DESC),'[]'::jsonb)
                 FROM (SELECT kategori k, count(*) n FROM f WHERE kategori IS NOT NULL GROUP BY kategori) x),
    'idare',    (SELECT COALESCE(jsonb_agg(jsonb_build_object('k',k,'n',n) ORDER BY n DESC),'[]'::jsonb)
                 FROM (SELECT idare k, count(*) n FROM f WHERE idare IS NOT NULL GROUP BY idare ORDER BY count(*) DESC LIMIT 20) x),
    'tur_maliyet', (SELECT COALESCE(jsonb_agg(jsonb_build_object('k',k,'sayi',sayi,'ort',ort) ORDER BY ort DESC NULLS LAST),'[]'::jsonb)
                 FROM (SELECT tur k, count(*) sayi, round(avg(m) FILTER (WHERE m > 0)) ort
                       FROM f WHERE tur IS NOT NULL GROUP BY tur) x),
    'trend', (SELECT COALESCE(jsonb_object_agg(ay, n),'{}'::jsonb)
                 FROM (SELECT to_char(tarih, 'YYYY-MM') ay, count(*) n
                       FROM f WHERE tarih IS NOT NULL AND tarih >= (now() - interval '24 months')
                       GROUP BY 1) x),
    'butce', jsonb_build_object(
      'b0',   (SELECT count(*) FROM f WHERE m > 0 AND m <  500000),
      'b1',   (SELECT count(*) FROM f WHERE m >= 500000    AND m < 2000000),
      'b2',   (SELECT count(*) FROM f WHERE m >= 2000000   AND m < 10000000),
      'b3',   (SELECT count(*) FROM f WHERE m >= 10000000  AND m < 50000000),
      'b4',   (SELECT count(*) FROM f WHERE m >= 50000000  AND m < 200000000),
      'b5',   (SELECT count(*) FROM f WHERE m >= 200000000),
      'byok', (SELECT count(*) FROM f WHERE m IS NULL OR m <= 0)
    )
  );
$$;

-- ── 2) kurum_ozet — `tarih` ekseni + kpi.aktif tabanı ───────────────────────
CREATE OR REPLACE FUNCTION public.kurum_ozet(p_idare text)
RETURNS jsonb
LANGUAGE sql STABLE SECURITY DEFINER
SET search_path = public, pg_temp
AS $$
  WITH f AS (
    SELECT tur, il, usul, kategori, durum,
           yaklasik_maliyet_min AS m,
           son_teklif_tarihi,
           COALESCE(etkin_tarih, ilan_tarihi, son_teklif_tarihi) AS tarih
    FROM public.ilanlar
    WHERE idare ILIKE '%' || p_idare || '%'
  )
  SELECT jsonb_build_object(
    'kpi', jsonb_build_object(
      'toplam',       (SELECT count(*) FROM f),
      -- ESKİDEN: son_teklif_tarihi > now() — %4,67 dolu kolon, çoğu kurumda 0.
      -- Artık `durum` (gece ilan_durum_bayatlat() ile bakımlı, %100 dolu).
      -- Aşağıdaki 'durum'.'aktif' ile bilinçli olarak AYNI tanım.
      'aktif',        (SELECT count(*) FROM f WHERE durum = 'aktif'),
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

COMMIT;

-- ── TUZAK A: proconfig'i geri koy ───────────────────────────────────────────
-- CREATE OR REPLACE bunu sildi. Uygulanmazsa rekabet-analizi aralıklı 3s
-- statement_timeout'a geri döner (migration_rekabet_ozet_timeout.sql'in çözdüğü hata).
ALTER FUNCTION public.rekabet_ozet(text, text, text) SET statement_timeout = '20s';

NOTIFY pgrst, 'reload schema';

-- ── DOĞRULAMA ──────────────────────────────────────────────────────────────
DO $$
DECLARE
  v_timeout text;
  v_anon_rek boolean;
  v_anon_kur boolean;
  v_auth_rek boolean;
BEGIN
  -- A) timeout override geri geldi mi?
  SELECT array_to_string(proconfig, ',') INTO v_timeout
  FROM pg_proc WHERE oid = 'public.rekabet_ozet(text,text,text)'::regprocedure;
  IF v_timeout IS NULL OR v_timeout NOT LIKE '%statement_timeout=20s%' THEN
    RAISE EXCEPTION 'DOGRULAMA BASARISIZ: rekabet_ozet statement_timeout override yok (proconfig=%)', v_timeout;
  END IF;

  -- B) maske korundu mu? anon HER İKİSİNE de kapalı olmalı
  v_anon_rek := has_function_privilege('anon', 'public.rekabet_ozet(text,text,text)', 'EXECUTE');
  v_anon_kur := has_function_privilege('anon', 'public.kurum_ozet(text)', 'EXECUTE');
  IF v_anon_rek THEN
    RAISE EXCEPTION 'DOGRULAMA BASARISIZ: anon rekabet_ozet calistirabiliyor — maske delindi';
  END IF;
  IF v_anon_kur THEN
    RAISE EXCEPTION 'DOGRULAMA BASARISIZ: anon kurum_ozet calistirabiliyor — maske delindi';
  END IF;

  -- C) üyeler hâlâ çalıştırabiliyor mu? (aksi halde iki analiz sayfası da ölür)
  v_auth_rek := has_function_privilege('authenticated', 'public.rekabet_ozet(text,text,text)', 'EXECUTE');
  IF NOT v_auth_rek THEN
    RAISE EXCEPTION 'DOGRULAMA BASARISIZ: authenticated rekabet_ozet calistiramiyor';
  END IF;
  IF NOT has_function_privilege('authenticated', 'public.kurum_ozet(text)', 'EXECUTE') THEN
    RAISE EXCEPTION 'DOGRULAMA BASARISIZ: authenticated kurum_ozet calistiramiyor';
  END IF;

  RAISE NOTICE 'OK: timeout override yerinde, anon kapali, authenticated acik';
END $$;

-- ── ETKİ ÖLÇÜMÜ (çıktıyı gözle kontrol et) ─────────────────────────────────
-- trend_eski = düzeltmeden önceki eksenin gördüğü satır sayısı
-- trend_yeni = yeni eksenin gördüğü satır sayısı (çok daha büyük olmalı)
SELECT
  count(*) FILTER (WHERE COALESCE(ilan_tarihi, son_teklif_tarihi) IS NOT NULL) AS trend_eski,
  count(*) FILTER (WHERE COALESCE(etkin_tarih, ilan_tarihi, son_teklif_tarihi) IS NOT NULL) AS trend_yeni,
  count(*) FILTER (WHERE son_teklif_tarihi > now())  AS kpi_aktif_eski,
  count(*) FILTER (WHERE durum = 'aktif')            AS kpi_aktif_yeni,
  count(*)                                           AS toplam
FROM public.ilanlar;
