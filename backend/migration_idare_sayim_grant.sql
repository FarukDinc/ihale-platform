-- ============================================================
-- İhaleGlobal — idare_sayim() RPC'sini deploy et + GRANT ekle
--
-- Kök neden: idare_sayim() migration_sonuc_schema.sql içinde tanımlıydı ama
-- fonksiyon prod'da hiç var olmamıştı (PGRST202 — "no matches were found in
-- the schema cache"). Muhtemelen o migration dosyası ilk çalıştırıldığında
-- başka bir ifade (örn. ilanlar_sonuc view çakışması) script'i idare_sayim
-- satırına ulaşmadan durdurmuştu. kategori_sayim/il_sayim'in aksine, bu
-- fonksiyon için ayrı bir GRANT migration'ı da hiç yazılmamıştı.
--
-- idareler.html şu an idare_sayim() KULLANMIYOR — tüm ilanlar tablosunu
-- (80K+ satır) sayfalayarak indirip JS'te grupluyor (çalışıyor ama
-- verimsiz). Bu migration RPC'yi deploy eder; frontend ayrı bir commit'te
-- bu RPC'yi kullanacak şekilde güncellenecek.
--
-- Additive/güvenli: CREATE OR REPLACE (idempotent) + sadece EXECUTE GRANT.
--
-- Çalıştırma: docker exec -i supabase-db psql -U postgres -d postgres < backend/migration_idare_sayim_grant.sql
-- ============================================================

BEGIN;

CREATE OR REPLACE FUNCTION idare_sayim()
RETURNS TABLE (
  idare TEXT,
  toplam BIGINT,
  aktif BIGINT,
  en_yakin_il TEXT
) AS $$
  SELECT
    idare,
    COUNT(*) AS toplam,
    COUNT(*) FILTER (WHERE durum = 'aktif') AS aktif,
    MODE() WITHIN GROUP (ORDER BY il) AS en_yakin_il
  FROM ilanlar
  WHERE idare IS NOT NULL
  GROUP BY idare
  ORDER BY toplam DESC;
$$ LANGUAGE SQL STABLE;

GRANT EXECUTE ON FUNCTION idare_sayim() TO anon, authenticated;

COMMIT;

NOTIFY pgrst, 'reload schema';

-- Kontrol
SELECT * FROM idare_sayim() LIMIT 5;
