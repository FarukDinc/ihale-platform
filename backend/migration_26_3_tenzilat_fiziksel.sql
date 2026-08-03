-- ============================================================================
-- migration_26_3_tenzilat_fiziksel.sql — [26-3] tenzilat FİZİKSEL imkânsız temizliği (3 Ağu 2026)
--
-- migration_qa_26_data_fixes.sql (2 Ağu) tenzilat'ı yalnız |t|>100 için null'ladı;
-- ama YAKIN-BEDAVA (t≥%95, ör. 5₺ sözleşme → %99,8) ve ÇÖP TABAN (<100₺) durumları
-- geçiyordu. Kullanıcı kararı (3 Ağu): "sadece fiziksel imkânsızı gizle" —
--   • kazanan/sözleşme bedeli < 100₺  (ör. 5₺ = imkânsız sözleşme)
--   • yaklaşık maliyet < 100₺          (rakamı eksik parse → sahte devasa tenzilat)
--   • tenzilat ≥ %95                   (teklif ≤ maliyetin %5'i = neredeyse bedava)
--   • tenzilat ≤ -%100                 (teklif ≥ 2× maliyet)
-- ORTA değerler (ör. -%55 aşım, %70 indirim) KORUNUR — gerçek olabilir ("veriyi gizleme" kuralı).
--
-- tenzilat_yuzde VE fallback kazanan_teklif_farki_yuzde İKİSİ de null'lanır (frontend
-- v = tenzilat_yuzde ?? kazanan_teklif_farki_yuzde okuyor). Taban değerler (bedel/maliyet)
-- SİLİNMEZ — yalnız güvenilmez türev % null'lanır (geri döndürülebilir: tabandan yeniden hesap).
--
-- Kalıcılık: scraper de düzeltildi (ekap_sonuc_backfill.py + ekap_sonuc_scraper.py aynı guard)
-- → gece yeni satırlar da çöp tenzilat yazmaz.
--
-- Çalıştırma: docker exec -i supabase-db psql -U supabase_admin -d postgres < backend/migration_26_3_tenzilat_fiziksel.sql
-- ============================================================================
\pset pager off
BEGIN;

\echo '26-3: fiziksel imkansiz tenzilat (null lanacak satir):'
SELECT count(*) FROM public.ihale_sonuclari
 WHERE (tenzilat_yuzde IS NOT NULL OR kazanan_teklif_farki_yuzde IS NOT NULL)
   AND (
        sozlesme_bedeli < 100
     OR yaklasik_maliyet < 100
     OR (yaklasik_maliyet > 0 AND (yaklasik_maliyet - sozlesme_bedeli)::numeric / yaklasik_maliyet * 100 >= 95)
     OR (yaklasik_maliyet > 0 AND (yaklasik_maliyet - sozlesme_bedeli)::numeric / yaklasik_maliyet * 100 <= -100)
     OR tenzilat_yuzde >= 95 OR tenzilat_yuzde <= -100
     OR kazanan_teklif_farki_yuzde >= 95 OR kazanan_teklif_farki_yuzde <= -100
   );

UPDATE public.ihale_sonuclari
   SET tenzilat_yuzde = NULL, kazanan_teklif_farki_yuzde = NULL
 WHERE (tenzilat_yuzde IS NOT NULL OR kazanan_teklif_farki_yuzde IS NOT NULL)
   AND (
        sozlesme_bedeli < 100
     OR yaklasik_maliyet < 100
     OR (yaklasik_maliyet > 0 AND (yaklasik_maliyet - sozlesme_bedeli)::numeric / yaklasik_maliyet * 100 >= 95)
     OR (yaklasik_maliyet > 0 AND (yaklasik_maliyet - sozlesme_bedeli)::numeric / yaklasik_maliyet * 100 <= -100)
     OR tenzilat_yuzde >= 95 OR tenzilat_yuzde <= -100
     OR kazanan_teklif_farki_yuzde >= 95 OR kazanan_teklif_farki_yuzde <= -100
   );

COMMIT;

-- ── Kontrol: lot_sayisi=1'de artık imkânsız tenzilat KALMAMALI ───────────────
\echo '=== KONTROL: lot_sayisi=1 kalan uc tenzilat (0 beklenir) ==='
SELECT count(*) FILTER (WHERE tenzilat_yuzde >= 95 OR tenzilat_yuzde <= -100) AS uc_yuzde,
       count(*) FILTER (WHERE tenzilat_yuzde IS NOT NULL AND (sozlesme_bedeli < 100 OR yaklasik_maliyet < 100)) AS cop_taban
  FROM public.ihale_sonuclari WHERE lot_sayisi = 1;
