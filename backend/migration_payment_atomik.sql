-- ============================================================================
-- HAZIR AMA UYGULANMADI — payment.py atomiklik/idempotency (denetim #12/#19/#27/#28).
-- KULLANICI ONAYIYLA uygulanır: (1) bu migration'ı çalıştır, (2) payment.py'yi aşağıdaki gibi
-- düzenle, (3) git push + VDS pull + `systemctl restart ihale-api.service`.
-- Bu dosya İNERT: çalıştırılana kadar canlı ödeme akışını DEĞİŞTİRMEZ (sadece yeni kolon+fonksiyon ekler).
-- ============================================================================

-- 1) kredi_hareketleri idempotency anahtarı (mevcut satırlar NULL → çakışmaz)
ALTER TABLE public.kredi_hareketleri ADD COLUMN IF NOT EXISTS siparis_id text;
CREATE UNIQUE INDEX IF NOT EXISTS uq_kredi_hareketleri_siparis
  ON public.kredi_hareketleri (siparis_id) WHERE siparis_id IS NOT NULL;

-- 2) Atomik + idempotent kredi yükleme (tek transaction). siparis_id daha önce işlendiyse false döner
--    (iyzico mükerrer webhook → çift kredi ENGELLENİR). toplam_kredi oku-yaz yerine atomik artış (lost-update yok).
CREATE OR REPLACE FUNCTION public.kredi_yukle_atomik(
  p_kullanici_id uuid, p_plan text, p_kredi int, p_siparis_id text,
  p_odeme int, p_plan_ad text, p_plan_bitis timestamptz DEFAULT NULL
) RETURNS boolean
LANGUAGE plpgsql SECURITY DEFINER SET search_path = public
AS $$
DECLARE eklendi int;
BEGIN
  INSERT INTO kredi_hareketleri (kullanici_id, miktar, islem_turu, aciklama, siparis_id)
  VALUES (p_kullanici_id, p_kredi, 'yukleme',
          p_plan_ad || ' — Sipariş: ' || p_siparis_id || ' — ' || p_odeme || ' TL', p_siparis_id)
  ON CONFLICT (siparis_id) WHERE siparis_id IS NOT NULL DO NOTHING;
  GET DIAGNOSTICS eklendi = ROW_COUNT;
  IF eklendi = 0 THEN RETURN false; END IF;   -- zaten işlenmiş → kredi YÜKLEME

  UPDATE kullanici_krediler
     SET toplam_kredi   = COALESCE(toplam_kredi, 0) + p_kredi,
         plan           = p_plan,
         plan_baslangic = now(),
         plan_bitis     = COALESCE(p_plan_bitis, plan_bitis)
   WHERE kullanici_id = p_kullanici_id;

  INSERT INTO bildirimler (kullanici_id, baslik, icerik, tur)
  VALUES (p_kullanici_id, 'Kredi yüklendi! 🎉',
          p_plan_ad || ' aktivasyonu: ' || p_kredi || ' kredi hesabınıza eklendi.', 'kredi');
  RETURN true;
END;
$$;
REVOKE ALL     ON FUNCTION public.kredi_yukle_atomik(uuid,text,int,text,int,text,timestamptz) FROM public, anon;
GRANT  EXECUTE ON FUNCTION public.kredi_yukle_atomik(uuid,text,int,text,int,text,timestamptz) TO service_role;

-- 3) Atomik kupon sayaç artışı — limit aşımını (TOCTOU) önler. 0 satır → limit dolu.
CREATE OR REPLACE FUNCTION public.kupon_kullan_atomik(p_kupon_id uuid)
RETURNS boolean
LANGUAGE sql SECURITY DEFINER SET search_path = public
AS $$
  WITH u AS (
    UPDATE public.kuponlar
       SET kullanim_sayisi = COALESCE(kullanim_sayisi, 0) + 1
     WHERE id = p_kupon_id AND COALESCE(kullanim_sayisi, 0) < COALESCE(max_kullanim, 1)
    RETURNING 1
  )
  SELECT EXISTS(SELECT 1 FROM u);
$$;
REVOKE ALL     ON FUNCTION public.kupon_kullan_atomik(uuid) FROM public, anon;
GRANT  EXECUTE ON FUNCTION public.kupon_kullan_atomik(uuid) TO service_role;

NOTIFY pgrst, 'reload schema';

-- ============================================================================
-- payment.py DÜZENLEMELERİ (bu migration çalıştıktan SONRA):
--
-- A) kredi_yukle(...) gövdesini şununla değiştir (RPC'yi çağır, döndürdüğü bool'u döndür):
--      res = supabase.rpc("kredi_yukle_atomik", {
--        "p_kullanici_id": kullanici_id, "p_plan": plan_kodu, "p_kredi": kredi_miktari,
--        "p_siparis_id": siparis_id, "p_odeme": odeme_miktari,
--        "p_plan_ad": PLANLAR[plan_kodu]["ad"], "p_plan_bitis": plan_bitis
--      }).execute()
--      return bool(res.data)   # False → zaten işlenmiş (mükerrer)
--
-- B) iyzico_webhook: kredi_yukle(...) çağrısı artık idempotent — dönüşü loglamak yeterli
--    (False ise "zaten işlenmiş sipariş" yaz, tekrar kredi yükleme).
--
-- C) kupon_kullan: 395-396'daki ön-kontrol + 422-424'teki manuel UPDATE'i KALDIR; yerine:
--      if not supabase.rpc("kupon_kullan_atomik", {"p_kupon_id": kupon["id"]}).execute().data:
--          raise HTTPException(status_code=400, detail="Bu kupon kullanım limitine ulaşmış")
--    ve kredi_yukle çağrısında siparis_id'yi PER-USER yap (aynı kod farklı kullanıcıda çakışmasın):
--      siparis_id=f"KUPON-{kod}-{kullanici_id}"
--    (kupon_kullanimlari UNIQUE(kupon_id,kullanici_id) zaten aynı kullanıcının tekrarını engelliyor.)
-- ============================================================================
