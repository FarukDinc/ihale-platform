-- =============================================================================
-- migration_idare_dal_ihaleler.sql — Kurum Ağacı: "dalın son ihaleleri" RPC'si
-- =============================================================================
--
-- AMAÇ: kurum-analiz.html Kurum Ağacı sekmesindeki "📋 Son ihaleler" modalı.
-- Önceki tasarım İKİ adımdı: idare_alt_agac_detsis dalın TÜM detsis_no'larını
-- istemciye indirir, istemci ilanlar üzerinde `detsis_no=in.(...)` GET filtresi
-- kurardı.
--
-- NEDEN DEĞİŞTİ (20 Tem inceleme bulgusu): in.() listesi URL'e yazılır.
-- 8 haneli DETSİS + URL-encoded virgül (%2C) ≈ 11 karakter/anahtar →
-- migration_idare_agac_rpc.sql'in KENDİ ÖRNEĞİ olan EGM dalı (1.090 düğüm)
-- tek başına ~12 KB istek satırı demek. Kong/nginx varsayılan istek-satırı
-- sınırı 8 KB ve bu stack'te in.() listeleri daha önce 414 verdi
-- (YAPILACAKLAR.md: kategori_backfill CHUNK=60 UUID'ye ~2,4 KB'a düşürülmek
-- zorunda kaldı). İstemcideki `liste.length > 1500` koruması da eşiği gerçek
-- sınırın ÜSTÜNE koyuyordu: ~700-1500 düğümlü dallarda buton 414 yer,
-- kullanıcıya yanıltıcı "tekrar deneyin" düşerdi. Kalıcı çözüm: JOIN'i sunucuya
-- taşı — URL sabit ve kısa (rpc POST gövdesi), eşik ve "alt dal seçin" çıkmazı
-- tamamen kalkar.
--
-- ÖNKOŞUL: migration_idare_agac_rpc.sql uygulanmış olmalı (idare_ata_torun +
-- ilanlar.detsis_no + idx_ilanlar_detsis). O dosya prod'a UYGULANMIŞ ve içinde
-- ALTER TABLE olduğu için TEKRAR KOŞULMAZ (19 Tem ACCESS EXCLUSIVE dersi) —
-- bu yüzden yeni RPC bu AYRI dosyada. idare_alt_agac_detsis yerinde kalıyor;
-- istemci artık onu çağırmıyor.
--
-- ANON'A KAPALI: idare-ihale bağı kimlik verisi; fonksiyon PUBLIC EXECUTE ile
-- doğar → REVOKE AÇIKÇA yazıldı (18 Tem dersi, migration_dt_anon_fix.sql).
--
-- Uygulama:
--   docker exec -i supabase-db psql -U postgres -d postgres < backend/migration_idare_dal_ihaleler.sql
-- =============================================================================

BEGIN;

-- ---------------------------------------------------------------------------
-- idare_dal_son_ihaleler(detsis, limit) — dalın (kendisi + tüm alt birimleri)
-- en güncel ihaleleri. Kapanış tablosu sayesinde tek JOIN; mesafe 0 satırı
-- dalın kendisini de kapsar. Sıralama istemcideki eski davranışla birebir:
-- etkin_tarih DESC NULLS LAST.
-- ---------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION public.idare_dal_son_ihaleler(
  p_detsis text, p_limit integer DEFAULT 20
)
RETURNS TABLE (
  id uuid, baslik text, il text, tur text,
  etkin_tarih timestamptz, son_teklif_tarihi timestamptz
)
LANGUAGE sql STABLE
AS $$
  SELECT i.id, i.baslik, i.il, i.tur, i.etkin_tarih, i.son_teklif_tarihi
    FROM public.idare_ata_torun at
    JOIN public.ilanlar i ON i.detsis_no = at.torun_no
   WHERE at.ata_no = p_detsis
   ORDER BY i.etkin_tarih DESC NULLS LAST
   LIMIT LEAST(COALESCE(p_limit, 20), 100);
$$;

-- Kök dallar on binlerce torun × idx_ilanlar_detsis taraması demek; sıralama
-- 3s varsayılanın kenarına gelebilir (bkz. hafıza statement-timeout-edge).
-- idare_agac_bagsiz_ozet ile aynı desen: pay bırak.
ALTER FUNCTION public.idare_dal_son_ihaleler(text, integer) SET statement_timeout = '15s';

REVOKE EXECUTE ON FUNCTION public.idare_dal_son_ihaleler(text, integer) FROM PUBLIC, anon;
GRANT  EXECUTE ON FUNCTION public.idare_dal_son_ihaleler(text, integer) TO authenticated, service_role;

COMMIT;

NOTIFY pgrst, 'reload schema';

-- =============================================================================
-- KURULUM SONRASI DOĞRULAMA
-- =============================================================================
-- psql (superuser):
--   -- Büyük dal (EGM ~1.090 düğüm — eski tasarımın 414 yiyeceği örnek):
--   -- detsis'i ağaçtan bul: SELECT detsis_no FROM idare_hiyerarsi WHERE ad ILIKE '%emniyet genel%';
--   SELECT * FROM public.idare_dal_son_ihaleler('<EGM_detsis>', 20);
--   EXPLAIN ANALYZE SELECT * FROM public.idare_dal_son_ihaleler('<EGM_detsis>', 20);
--   -- Kök düğümde de süreyi ölç (en geniş dal = en kötü durum).
--
-- ANON DOĞRULAMASI (deploy sonrası ŞART — bkz. hafıza anon-maske):
--   curl -s -o /dev/null -w '%{http_code}\n' \
--     -H "apikey: $ANON" -H "Authorization: Bearer $ANON" \
--     -X POST https://ihaleglobal.com/rest/v1/rpc/idare_dal_son_ihaleler \
--     -H 'Content-Type: application/json' -d '{"p_detsis":"0"}'
--   -- beklenen: 401/403/404 (200 DÖNMEMELİ)
