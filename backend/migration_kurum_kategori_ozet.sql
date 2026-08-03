-- ============================================================
-- kurum_kategori_ozet() — Kurum Merkezi "Kurumlar" landing (UV-6 Faz A, hibrit) — 3 Ağu 2026
-- ------------------------------------------------------------
-- HEDEF (bkz UV6_KURUM_MERKEZI_TASARIM.md): rakip ihalepro'nun "Kurumlar" düz kategori
-- listesine denk gelen ~36 üst kategori. Kullanıcı kararı: HİBRİT = DETSİS kökleri + yerelleri
-- düzleştir.
--
-- Veri gerçeği (ölçüldü): idare_hiyerarsi_sayim_mv'de 73 kök var; bunlar ZATEN bakanlık düzeyi
-- (ADALET/İÇİŞLERİ/SAĞLIK…) + yargı + düzenleyici + Cumhurbaşkanlığı/TBMM + "YEREL YÖNETİM
-- KURULUŞLARI" (tek kök, 602K ihale) + "Bağlantısız Kurumlar" (215K, DETSİS-dışı). Yerel yönetimler
-- tek kökün altında toplanmış; rakip ise BELEDİYELER / İL ÖZEL / BİRLİKLER'i AYRI kategori yapmış.
--
-- ÇÖZÜM: kökleri döndür AMA "YEREL YÖNETİM KURULUŞLARI"nı (detsis_no 24350161) GİZLE ve onun
-- ÇOCUKLARINI (BELEDİYELER 82150602, İL ÖZEL İDARELERİ 51727839, BİRLİKLER 10014407, MUHTARLIKLAR
-- 56910115) üst kategori olarak AÇ. Çift-sayım YOK: yerel yönetimler bakanlık alt-ağaçlarında değil,
-- ayrı disjoint alt-ağaç. Drill-down mevcut idare_agac_dallar(detsis_no) ile (frontend).
--
-- NOT: tutar (toplam bedel) sayım MV'de yok → kartlar ihale+DT SAYISI + çocuk sayısı ile döner;
-- tutar Faz A.2 (idare_hiyerarsi_sayim_mv'ye bedel agregası eklemek — ayrı iş).
-- Erişim: idare_agac_dallar ile AYNI — idare adı kimlik verisi, anon KAPALI, authenticated açık.
--
-- Çalıştır (superuser):
--   docker exec -i supabase-db psql -U supabase_admin -d postgres < backend/migration_kurum_kategori_ozet.sql
-- ============================================================

CREATE OR REPLACE FUNCTION public.kurum_kategori_ozet()
RETURNS TABLE (
  detsis_no text, ad text, grup text,
  toplam_ihale bigint, toplam_dt bigint, cocuk_sayisi bigint
)
LANGUAGE sql STABLE
AS $$
  -- (1) Kökler — YEREL YÖNETİM KURULUŞLARI hariç (onu çocuklarıyla düzleştiriyoruz)
  SELECT s.detsis_no, s.ad,
         CASE WHEN s.ad = 'Bağlantısız Kurumlar' THEN 'diger' ELSE 'merkezi' END AS grup,
         s.toplam_ihale, s.toplam_dt, s.cocuk_sayisi
    FROM public.idare_hiyerarsi_sayim_mv s
   WHERE s.ust_detsis_no IS NULL
     AND s.detsis_no <> '24350161'                 -- YEREL YÖNETİM kökünü gizle
  UNION ALL
  -- (2) YEREL YÖNETİM'in çocuklarını üst kategori olarak aç (BELEDİYELER / İL ÖZEL / BİRLİKLER / MUHTARLIKLAR)
  SELECT s.detsis_no, s.ad, 'yerel'::text AS grup,
         s.toplam_ihale, s.toplam_dt, s.cocuk_sayisi
    FROM public.idare_hiyerarsi_sayim_mv s
   WHERE s.ust_detsis_no = '24350161'
  ORDER BY toplam_ihale DESC, toplam_dt DESC, ad;
$$;

REVOKE EXECUTE ON FUNCTION public.kurum_kategori_ozet() FROM PUBLIC, anon;
GRANT  EXECUTE ON FUNCTION public.kurum_kategori_ozet() TO authenticated, service_role;

NOTIFY pgrst, 'reload schema';

-- Kontrol (rakibin ~36 kategorisine benzer düz liste dönmeli — bakanlıklar + BELEDİYELER/İL ÖZEL/BİRLİKLER):
--   SELECT ad, grup, toplam_ihale, toplam_dt, cocuk_sayisi FROM kurum_kategori_ozet() LIMIT 40;
