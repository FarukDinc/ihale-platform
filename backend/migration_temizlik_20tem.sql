-- ============================================================================
-- 20 Tem temizlik turu — iki bağımsız küçük iş
--
-- (1) `idare_tur` tablosu + idare_tur_* fonksiyonları anon'dan REVOKE.
--     DURUM: anon şu an 200 alıyor ama RLS satırları kesip [] döndürüyor
--     (curl ile ölçüldü). Yani sızıntı YOK — bu SAVUNMA DERİNLİĞİ işi:
--     maskeleme bu projede üç kez sessizce delindi ve her seferinde tek
--     katmana güvenilmişti. RLS politikası bir gün gevşetilirse tablo
--     anında açılır; açık REVOKE o riski kapatır.
--     KIRILMA RİSKİ YOK: frontend'de `from('idare_tur')` ve `idare_tur_liste`
--     kullanımı SIFIR (grep ile doğrulandı). idare_tur_kapsama'yı
--     idare_tur_kural_backfill.py SERVICE anahtarıyla, idare_tur_bosluk'u
--     run_scraper.sh psql'den (postgres) çağırıyor — ikisi de anon değil.
--
-- (2) idx_ilanlar_olusturulma — "Sisteme Yeni Düşen" sıralamasının tek eksik
--     parçası. İndekssiz ORDER BY olusturulma DESC 555K satırda timeout
--     kenarında (bu projede 3s statement_timeout duvarı biliniyor).
--
-- Çalıştırma (VDS) — İKİ AYRI komut, çünkü CONCURRENTLY transaction içinde
-- çalışmaz; bu dosyanın tamamını tek psql'e vermek CONCURRENTLY'yi düşürür:
--   docker exec -i supabase-db psql -U postgres -d postgres < migration_temizlik_20tem.sql
-- (aşağıdaki CONCURRENTLY satırı dosyanın sonunda, BEGIN/COMMIT dışında)
-- ============================================================================

BEGIN;

-- ── (1) idare_tur yüzeyini anon'dan kapat ───────────────────────────────────
REVOKE ALL ON TABLE public.idare_tur FROM anon;

DO $$
DECLARE f record;
BEGIN
  FOR f IN
    SELECT p.oid::regprocedure AS imza
    FROM pg_proc p JOIN pg_namespace n ON n.oid = p.pronamespace
    WHERE n.nspname = 'public'
      AND p.proname IN ('idare_tur_liste','idare_tur_sayim',
                        'idare_tur_kapsama','idare_tur_bosluk','idare_tur_tazele')
  LOOP
    EXECUTE format('REVOKE ALL ON FUNCTION %s FROM anon', f.imza);
    RAISE NOTICE 'REVOKE: % → anon', f.imza;
  END LOOP;
END $$;

-- ── DOĞRULAMA: yanlışsa COMMIT ETMEZ ────────────────────────────────────────
DO $$
BEGIN
  IF has_table_privilege('anon', 'public.idare_tur', 'SELECT') THEN
    RAISE EXCEPTION 'DOGRULAMA BASARISIZ: anon hala idare_tur okuyabiliyor';
  END IF;

  -- Yan etki kontrolü: ilanlar.idare_tur KOLONU anon'a AÇIK KALMALI.
  -- (19 Tem'de bu kolon kapalı olduğu için misafirde iki sayfa 42501 ile
  --  ölmüştü — tablo REVOKE'u kazara kolonu etkilerse hemen yakala.)
  IF NOT has_column_privilege('anon', 'public.ilanlar', 'idare_tur', 'SELECT') THEN
    RAISE EXCEPTION 'DOGRULAMA BASARISIZ: ilanlar.idare_tur kolonu anona kapandi — filtre kirilir';
  END IF;
  IF NOT has_column_privilege('anon', 'public.dogrudan_temin_ilanlari', 'idare_tur', 'SELECT') THEN
    RAISE EXCEPTION 'DOGRULAMA BASARISIZ: DT.idare_tur kolonu anona kapandi — filtre kirilir';
  END IF;

  RAISE NOTICE 'OK: idare_tur yuzeyi anona kapali, idare_tur KOLON filtresi saglam';
END $$;

COMMIT;

NOTIFY pgrst, 'reload schema';

-- ── (2) "Sisteme Yeni Düşen" indeksi — transaction DIŞINDA ──────────────────
-- Kolon yoksa sessizce atlamak yerine gürültülü hata versin (yanlış kolon adı
-- varsayımı bu projede daha önce sessiz 0-sonuca yol açtı).
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_ilanlar_olusturulma
  ON public.ilanlar (olusturulma DESC NULLS LAST);

-- Uygulama sonrası teyit (elle):
--   SELECT to_regclass('public.idx_ilanlar_olusturulma');            -- NOT NULL beklenir
--   SELECT has_table_privilege('anon','public.idare_tur','SELECT');  -- false beklenir
