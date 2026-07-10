-- ============================================================
-- İhalePlatform — Yeni kullanıcı otomatik provizyon (kritik launch fix)
--
-- SORUN: kullanici_krediler (id FK → kullanici_profiller.id) hiçbir yerde
-- otomatik oluşturulmuyordu — ne bir trigger, ne bir backend kodu. Sonuç:
-- HİÇBİR kullanıcı (yeni ya da eski) AI analiz kredi kontrolünden geçemiyordu
-- (worker.py'deki .single() sorgusu 0 satırda hata veriyordu). Bu, platformun
-- asıl ücretli özelliğini (AI şartname analizi) baştan itibaren kullanılamaz
-- kılıyordu.
--
-- ÇÖZÜM: auth.users'a INSERT olunca (yeni signup) otomatik olarak hem
-- kullanici_profiller hem kullanici_krediler satırı oluşturan bir trigger +
-- geçmişte kayıt olmuş ama satırı olmayan kullanıcılar için tek seferlik backfill.
--
-- Çalıştırma: docker exec -i supabase-db psql -U postgres -d postgres < backend/migration_yeni_kullanici_kredi.sql
-- ============================================================

CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS trigger
LANGUAGE plpgsql
SECURITY DEFINER
SET search_path = public
AS $$
BEGIN
  INSERT INTO public.kullanici_profiller (id)
  VALUES (NEW.id)
  ON CONFLICT (id) DO NOTHING;

  -- free plan: planlar.kod='free', aylik_kredi=3 (bkz. planlar tablosu)
  INSERT INTO public.kullanici_krediler (kullanici_id, toplam_kredi, plan)
  VALUES (NEW.id, 3, 'free')
  ON CONFLICT (kullanici_id) DO NOTHING;

  RETURN NEW;
END;
$$;

DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;

CREATE TRIGGER on_auth_user_created
  AFTER INSERT ON auth.users
  FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- Geçmiş kullanıcılar için backfill (trigger'dan önce kayıt olanlar)
INSERT INTO public.kullanici_profiller (id)
SELECT u.id FROM auth.users u
LEFT JOIN public.kullanici_profiller kp ON kp.id = u.id
WHERE kp.id IS NULL
ON CONFLICT (id) DO NOTHING;

INSERT INTO public.kullanici_krediler (kullanici_id, toplam_kredi, plan)
SELECT u.id, 3, 'free' FROM auth.users u
LEFT JOIN public.kullanici_krediler kk ON kk.kullanici_id = u.id
WHERE kk.kullanici_id IS NULL
ON CONFLICT (kullanici_id) DO NOTHING;

-- ============================================================
-- Kontrol
SELECT
  (SELECT count(*) FROM auth.users)               AS auth_users,
  (SELECT count(*) FROM public.kullanici_profiller) AS profiller,
  (SELECT count(*) FROM public.kullanici_krediler)  AS krediler;
