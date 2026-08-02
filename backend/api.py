"""
İhaleGlobal FastAPI — Backend API
Frontend'den gelen istekleri karşılar

Çalıştırma:
    uvicorn api:app --reload

AI SINIRI (29 Tem — sağlayıcı taşıması)
---------------------------------------
Bu dosya HİÇBİR AI sağlayıcısını doğrudan çağırmaz; iki farklı katmana devreder:

  · METİN/CHAT  → worker.kullanici_analiz_isle · firma_ai_yorum.firma_yorum_uret ·
    teklif_ai.teklif_taslak_uret / teklif_strateji_uret. Bu modüller metni artık
    ai_ortak (ai_metin/ai_cagir) üzerinden üretir: sağlayıcı env ile seçilir
    (AI_SAGLAYICI, öntanım DeepSeek; Gemini yedek). api.py yalnız bu fonksiyonların
    SÖZLEŞMESİNE bağlıdır — sağlayıcı değişimi buradaki kodu etkilemez:
        firma_yorum_uret   -> {"basari", "metin", "hata"}
        teklif_taslak_uret -> {"basari", "kapsam", "neden", "yontem", "hata"}
        teklif_strateji_uret -> {"basari", "metin", "hata"}
    ⚠️ Bu anahtarlar endpoint yanıt şemalarına birebir yansıyor; değiştirilirse frontend kırılır.

  · EMBEDDING   → embed_ortak.embed_uret (PUT /profil içinde). ⛔ GEMİNİ'DE KALIR,
    ai_ortak'a TAŞINMAZ (bkz. aşağıdaki not).
"""

import json
import os
from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from supabase import create_client, Client
from worker import kullanici_analiz_isle
from firma_ai_yorum import firma_yorum_uret, firma_kirilim_topla, firma_veri_hash, AI_YORUM_GECERLILIK_GUN
from teklif_ai import teklif_taslak_uret, teklif_strateji_uret, sartname_oku
from payment import router as payment_router
from dotenv import load_dotenv
from datetime import datetime, timedelta, timezone

load_dotenv()

app = FastAPI(title="İhaleGlobal API", version="1.0.0")
app.include_router(payment_router)

# CORS — Netlify frontend'e izin ver
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://ihaleglobal.com",
        "https://www.ihaleglobal.com",
        "https://astounding-speculoos-40e25c.netlify.app",  # Eski Netlify (geçiş süreci)
        "http://localhost:3000",   # Geliştirme
        "http://localhost:5500",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


# ── Yardımcı: Token doğrula ───────────────────────────────
def kullanici_dogrula(authorization: str) -> str:
    """
    Frontend'den gelen Supabase JWT token'ı doğrular.
    Kullanıcı ID'sini döndürür.
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token gerekli")

    token = authorization.replace("Bearer ", "")

    try:
        user = supabase.auth.get_user(token)
        return user.user.id
    except Exception:
        raise HTTPException(status_code=401, detail="Geçersiz token")


# ── Request Modelleri ─────────────────────────────────────
class AnalizIstek(BaseModel):
    ihale_id: str

class ProfilGuncelle(BaseModel):
    firma_adi: Optional[str] = None
    faaliyet_alanlari: Optional[list] = None
    calisma_illeri: Optional[list] = None
    calisani_sayisi: Optional[int] = None
    yillik_ciro_tl: Optional[int] = None
    belgeler: Optional[list] = None
    referanslar: Optional[list] = None
    kacinilanlar: Optional[list] = None

class TakipEkle(BaseModel):
    ihale_id: str
    notlar: Optional[str] = None

class FirmaYorumIstek(BaseModel):
    firma: str

class KurumYorumIstek(BaseModel):
    idare: str

class FirmaIletisimIstek(BaseModel):
    firma: str


# ── Endpoint'ler ──────────────────────────────────────────

@app.get("/")
def root():
    return {"durum": "çalışıyor", "versiyon": "1.0.0"}


@app.get("/ihaleler")
def ihaleleri_listele(
    il: Optional[str] = None,
    tur: Optional[str] = None,
    arama: Optional[str] = None,
    sayfa: int = 1,
    boyut: int = 20
):
    """
    İhale listesi — herkese açık, auth gerekmez.
    """
    try:
        sorgu = supabase.table("ilanlar").select(
            "id, ikn, baslik, idare, il, tur, durum, ihale_tarihi, "
            "tahmini_bedel, analiz_tarihi"
        ).eq("durum", "Teklif Vermeye Açık")

        if il:
            sorgu = sorgu.eq("il", il)
        if tur:
            sorgu = sorgu.eq("tur", tur)
        if arama:
            sorgu = sorgu.ilike("baslik", f"%{arama}%")

        # Sayfalama
        baslangic = (sayfa - 1) * boyut
        sonuc = sorgu.order(
            "ihale_tarihi", desc=True
        ).range(baslangic, baslangic + boyut - 1).execute()

        return {
            "basari": True,
            "veri": sonuc.data,
            "sayfa": sayfa,
            "boyut": boyut
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/ihaleler/{ihale_id}")
def ihale_detay(ihale_id: str):
    """Tek ihale detayı."""
    try:
        sonuc = supabase.table("ilanlar").select("*").eq(
            "id", ihale_id
        ).single().execute()
        return {"basari": True, "veri": sonuc.data}
    except Exception as e:
        raise HTTPException(status_code=404, detail="İhale bulunamadı")


@app.post("/analiz")
def analiz_et(
    istek: AnalizIstek,
    authorization: str = Header(None)
):
    """
    Kullanıcı 'Analiz Et' butonuna bastığında çağrılır.
    Kredi kontrolü, cache, AI analizi (worker → analyzer).
    NOT: analyzer'ın METİN dalı ai_ortak üzerinden gider (DeepSeek/Gemini env ile);
    taranmış PDF'in VISION dalı Gemini'de kalır. Bu endpoint'in davranışı ikisinde de aynı.
    """
    kullanici_id = kullanici_dogrula(authorization)

    sonuc = kullanici_analiz_isle(
        kullanici_id=kullanici_id,
        ihale_id=istek.ihale_id
    )

    if not sonuc["basari"]:
        hata = sonuc.get("hata", "Bilinmeyen hata")
        if "kredi" in hata.lower():
            raise HTTPException(status_code=402, detail=hata)
        raise HTTPException(status_code=500, detail=hata)

    return sonuc


@app.get("/profil")
def profil_getir(authorization: str = Header(None)):
    """Kullanıcının firma profilini döndürür."""
    kullanici_id = kullanici_dogrula(authorization)

    try:
        profil = supabase.table("kullanici_profiller").select(
            "*"
        ).eq("id", kullanici_id).single().execute()

        kredi = supabase.table("kullanici_krediler").select(
            "kalan_kredi, toplam_kredi, plan"
        ).eq("kullanici_id", kullanici_id).single().execute()

        return {
            "basari": True,
            "profil": profil.data,
            "kredi": kredi.data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/profil")
def profil_guncelle(
    guncelleme: ProfilGuncelle,
    authorization: str = Header(None)
):
    """Firma profilini günceller."""
    kullanici_id = kullanici_dogrula(authorization)

    try:
        veri = {k: v for k, v in guncelleme.dict().items() if v is not None}
        supabase.table("kullanici_profiller").update(veri).eq(
            "id", kullanici_id
        ).execute()

        # ⛔ EMBEDDING DALI — AI sağlayıcı taşımasının DIŞINDA. embed_ortak (Gemini,
        # models/gemini-embedding-001, 768 boyut) AYNEN kalır; ai_ortak'a bağlanmaz.
        # Vektör uzayı değişirse kullanici_profiller.embedding / ilanlar.embedding
        # (vector(768) + hnsw) ve uygun_firmalar_v3 semantik eşleme RPC'leri bozulur.
        # Faz D3 — semantik eşleşme: profil değiştiğinde firma embedding'ini tazele.
        # embedding kolonu (migration_semantik_esleme.sql) yoksa sessizce geç, kaydı bozmaz.
        # ⚠️ Bu istek PARÇALI bir güncelleme olabilir (sadece 1-2 alan gönderilmiş) — embedding'i
        # sadece bu isteğin gövdesinden değil, güncel TAM satırdan üretiyoruz; yoksa örn. sadece
        # calisani_sayisi güncellenince firma_adi/referanslar embedding'den düşüp daralırdı.
        try:
            guncel = supabase.table("kullanici_profiller").select(
                "firma_adi, faaliyet_alanlari, referanslar"
            ).eq("id", kullanici_id).limit(1).execute()
            satir = (guncel.data or [{}])[0]

            def _metin_yap(deger):
                if isinstance(deger, list):
                    return " ".join(str(x) for x in deger if x)
                return str(deger or "")

            metin = " ".join(p for p in (
                _metin_yap(satir.get("firma_adi")),
                _metin_yap(satir.get("faaliyet_alanlari")),
                _metin_yap(satir.get("referanslar")),
            ) if p).strip()
            if metin:
                from embed_ortak import embed_uret
                vec = embed_uret(metin)
                if vec is not None:
                    supabase.table("kullanici_profiller").update({
                        "embedding": vec,
                    }).eq("id", kullanici_id).execute()
        except Exception as e:
            print(f"  ⚠ profil embedding tazeleme atlandı: {e}")

        return {"basari": True, "mesaj": "Profil güncellendi"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/takipler")
def takipleri_getir(authorization: str = Header(None)):
    """Kullanıcının takip listesi."""
    kullanici_id = kullanici_dogrula(authorization)

    try:
        sonuc = supabase.table("takipler").select(
            "*, ilanlar(ikn, baslik, idare, il, ihale_tarihi, durum)"
        ).eq("kullanici_id", kullanici_id).eq("durum", "aktif").execute()
        return {"basari": True, "veri": sonuc.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/takipler")
def takip_ekle(
    istek: TakipEkle,
    authorization: str = Header(None)
):
    """İhaleyi takip listesine ekler."""
    kullanici_id = kullanici_dogrula(authorization)

    try:
        supabase.table("takipler").upsert({
            "kullanici_id": kullanici_id,
            "ilan_id": istek.ihale_id,
            "notlar": istek.notlar,
            "durum": "aktif"
        }, on_conflict="kullanici_id,ilan_id").execute()
        return {"basari": True, "mesaj": "Takibe alındı"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/takipler/{ihale_id}")
def takip_kaldir(
    ihale_id: str,
    authorization: str = Header(None)
):
    """Takipten çıkar."""
    kullanici_id = kullanici_dogrula(authorization)

    try:
        supabase.table("takipler").update({"durum": "arsivlendi"}).eq(
            "kullanici_id", kullanici_id
        ).eq("ilan_id", ihale_id).execute()
        return {"basari": True, "mesaj": "Takipten çıkarıldı"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/bildirimler")
def bildirimleri_getir(authorization: str = Header(None)):
    """Kullanıcının bildirimlerini döndürür."""
    kullanici_id = kullanici_dogrula(authorization)

    try:
        sonuc = supabase.table("bildirimler").select("*").eq(
            "kullanici_id", kullanici_id
        ).order("olusturulma", desc=True).limit(50).execute()
        return {"basari": True, "veri": sonuc.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/bildirimler/{bildirim_id}/okundu")
def bildirim_okundu(
    bildirim_id: str,
    authorization: str = Header(None)
):
    """Bildirimi okundu işaretle."""
    kullanici_id = kullanici_dogrula(authorization)

    try:
        supabase.table("bildirimler").update({"okundu": True}).eq(
            "id", bildirim_id
        ).eq("kullanici_id", kullanici_id).execute()
        return {"basari": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/analiz-gecmisi")
def analiz_gecmisi_getir(authorization: str = Header(None)):
    """Kullanıcının analiz geçmişi."""
    kullanici_id = kullanici_dogrula(authorization)

    try:
        sonuc = supabase.table("analiz_gecmisi").select(
            "*, ilanlar(ikn, baslik)"
        ).eq("kullanici_id", kullanici_id).order(
            "olusturulma", desc=True
        ).limit(20).execute()
        return {"basari": True, "veri": sonuc.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ai/firma-yorum")
def firma_ai_yorum(
    istek: FirmaYorumIstek,
    authorization: str = Header(None)
):
    """
    ÖNCELİK 10 Faz D1 — bir firma için AI rekabet yorumu üretir.
    Sayılar analiz_pivot RPC'sinden (SQL), yorum AI'dan (firma_ai_yorum → ai_ortak:
    DeepSeek birincil, Gemini yedek — sağlayıcı env ile). 7 gün cache'lenir
    (yukleniciler.ai_yorum / ai_yorum_tarih — bkz. migration_yuklenici_agg.sql).
    ⚠️ Bu endpoint, analiz_pivot RPC'si ve yukleniciler.ai_yorum kolonları DB'de
    kurulana kadar 500 döner (migration bekliyor, bkz. YAPILACAKLAR.md ÖNCELİK 10 Faz C/D).
    """
    kullanici_id = kullanici_dogrula(authorization)
    firma = istek.firma.strip()
    if not firma:
        raise HTTPException(status_code=400, detail="Firma adı gerekli")

    try:
        # 1. Cache kontrolü (yukleniciler.normalize_ad ile eşleşen kayıt).
        # NOT: fake supabase wrapper'da .maybe_single() yok, sadece .single() (0 satırda hata
        # fırlatır) — bu yüzden düz .select() + liste kontrolü kullanıyoruz (0 satır = boş liste).
        norm = supabase.rpc("normalize_firma", {"ham_ad": firma}).execute()
        normalize_ad = norm.data
        mevcut_liste = supabase.table("yukleniciler").select(
            "id, ad, ai_yorum, ai_yorum_tarih, toplam_sozlesme_sayisi, toplam_ciro, il, sektor, "
            "seg_parlayan, seg_sonen, seg_ilk_kez, seg_150mn, ciro_son_12ay, ciro_onceki_12ay, "
            "buyume_yuzde, ortak_girisim"
        ).eq("normalize_ad", normalize_ad).limit(1).execute()
        mevcut_kayit = (mevcut_liste.data or [None])[0]

        if mevcut_kayit and mevcut_kayit.get("ai_yorum"):
            tarih = mevcut_kayit.get("ai_yorum_tarih")
            if tarih:
                try:
                    yas = datetime.now(timezone.utc) - datetime.fromisoformat(tarih.replace("Z", "+00:00"))
                    if yas < timedelta(days=AI_YORUM_GECERLILIK_GUN):
                        return {"basari": True, "metin": mevcut_kayit["ai_yorum"], "cache": True}
                except ValueError:
                    pass  # tarih parse edilemedi, tazele

        # 2. Kredi ön kontrolü
        kredi_bilgi = supabase.table("kullanici_krediler").select(
            "kalan_kredi"
        ).eq("kullanici_id", kullanici_id).single().execute()
        if (kredi_bilgi.data or {}).get("kalan_kredi", 0) < 1:
            raise HTTPException(status_code=402, detail="Yetersiz kredi")

        # 3. Kırılımları topla (idare/kategori/il/yil + DT kazanımları + firma profili/segmentler) —
        #    tek kaynak firma_kirilim_topla (gece tazeleme ai_yorum_tazele.py de AYNI fonksiyonu
        #    kullanır → veri-hash birebir tutarlı). İhale ve DT AYRI evren; AI ikisini birlikte değerlendirir.
        kirilimlar = firma_kirilim_topla(supabase, firma, mevcut_kayit)

        # 4. AI yorumu üret (sağlayıcıyı firma_ai_yorum/ai_ortak seçer)
        sonuc = firma_yorum_uret(firma_adi=firma, kirilimlar=kirilimlar)
        if not sonuc["basari"]:
            raise HTTPException(status_code=500, detail=sonuc["hata"])

        # 5. Kredi düş (ihale-bağımsız — p_referans_id=None; gerçek RPC imzası
        #    p_kullanici_id/p_miktar/p_referans_id/p_referans_tip/p_islem_turu/p_aciklama —
        #    önceden yanlışlıkla var olmayan p_ihale_id kullanılıyordu, PostgREST'in fonksiyonu
        #    hiç bulamamasına (dolayısıyla kredinin hiç düşmemesine) yol açıyordu)
        try:
            kredi_sonuc = supabase.rpc("kredi_dus", {
                "p_kullanici_id": kullanici_id,
                "p_miktar": 1,
                "p_referans_id": None,
                "p_referans_tip": "firma",
                "p_islem_turu": "analiz",
                "p_aciklama": f"AI Firma Yorumu: {firma[:50]}"
            }).execute()
        except Exception as e:
            print(f"  ⚠ kredi_dus (firma-yorum) hatası: {e}")
            raise HTTPException(status_code=500, detail="Kredi işlemi tamamlanamadı, lütfen tekrar deneyin")
        # Sessizce yutup bedava AI verme (worker.py deseni): düşme başarısız/yetersizse hata dön
        if not getattr(kredi_sonuc, "data", None):
            raise HTTPException(status_code=402, detail="Yetersiz kredi")

        # 6. Cache'e yaz (+ veri-hash → gece tazeleme veri değişince yorumu geçersiz kılar)
        supabase.table("yukleniciler").update({
            "ai_yorum": sonuc["metin"],
            "ai_yorum_tarih": datetime.now(timezone.utc).isoformat(),
            "ai_yorum_hash": firma_veri_hash(kirilimlar),
        }).eq("normalize_ad", normalize_ad).execute()

        return {"basari": True, "metin": sonuc["metin"], "cache": False}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/teklif-olustur")
def teklif_olustur(
    istek: AnalizIstek,
    authorization: str = Header(None)
):
    """
    Faz D4 — AI teklif taslağı üretir (teklif-olustur.html "✨ AI ile Oluştur" butonu).
    İhale detayı + kullanıcının firma profili + aynı idare/kategoride geçmişte kazanan
    firmaların ortalama tenzilatı (analiz_pivot) AI'ya bağlam olarak veriliyor
    (teklif_ai → ai_ortak; sağlayıcı env ile: DeepSeek birincil, Gemini yedek) —
    "piyasa farkında" taslak (bkz. YAPILACAKLAR.md Faz D4).
    """
    kullanici_id = kullanici_dogrula(authorization)
    ihale_id = istek.ihale_id

    try:
        ilan_sonuc = supabase.table("ilanlar").select(
            "id, baslik, idare, il, kategori, tur, isin_yapilacagi_yer, ilan_metni"
        ).eq("id", ihale_id).limit(1).execute()
        ilan = (ilan_sonuc.data or [None])[0]
        if not ilan:
            raise HTTPException(status_code=404, detail="İhale bulunamadı")

        # Kredi ön kontrolü
        kredi_bilgi = supabase.table("kullanici_krediler").select(
            "kalan_kredi"
        ).eq("kullanici_id", kullanici_id).single().execute()
        if (kredi_bilgi.data or {}).get("kalan_kredi", 0) < 1:
            raise HTTPException(status_code=402, detail="Yetersiz kredi")

        # Firma profili (defensif — .maybe_single() yok, .select().limit(1) + liste kontrolü)
        profil_liste = supabase.table("kullanici_profiller").select(
            "firma_adi, yillik_ciro_tl, calisma_illeri, referanslar"
        ).eq("id", kullanici_id).limit(1).execute()
        firma_profil = (profil_liste.data or [{}])[0]

        # Piyasa bağlamı — aynı idare/kategoride geçmişte kazanan firmalar (RPC yoksa sessizce boş).
        # ⚠️ analiz_pivot'ta p_idare/p_kategori NULL ise o filtre uygulanmaz (bkz. migration_analiz_rpc.sql
        # "$2 IS NULL OR i.idare = $2") — yani ilan.idare/kategori boşsa RPC TÜM Türkiye'deki en sık
        # kazanan firmaları döndürür, ama prompt bunu "bu idare/sektörde" diye sunar. İkisi de eksikse
        # RPC'yi hiç çağırma; boş bağlam (teklif_ai.py zaten "geçmiş kayıt bulunamadı" diye ele alıyor).
        piyasa_baglami = []
        if ilan.get("idare") and ilan.get("kategori"):
            try:
                piv = supabase.rpc("analiz_pivot", {
                    "p_grup": "firma", "p_idare": ilan.get("idare"), "p_kategori": ilan.get("kategori"),
                }).execute()
                piyasa_baglami = piv.data or []
            except Exception as e:
                print(f"  ⚠ analiz_pivot (teklif-olustur) atlandı: {e}")

        sonuc = teklif_taslak_uret(ilan=ilan, firma_profil=firma_profil, piyasa_baglami=piyasa_baglami)
        if not sonuc["basari"]:
            raise HTTPException(status_code=500, detail=sonuc["hata"])

        try:
            kredi_sonuc = supabase.rpc("kredi_dus", {
                "p_kullanici_id": kullanici_id,
                "p_miktar": 1,
                "p_referans_id": ihale_id,
                "p_referans_tip": "ihale",
                # ⚠️ 'teklif_taslak' kredi_hareketleri_islem_turu_check'i İHLAL EDİYORDU (23514) →
                #    kredi hiç düşmüyor, endpoint 500 veriyordu. İzinli değer: 'analiz'/'yukleme'.
                "p_islem_turu": "analiz",
                "p_aciklama": f"AI Teklif Taslağı: {(ilan.get('baslik') or '')[:50]}"
            }).execute()
        except Exception as e:
            print(f"  ⚠ kredi_dus (teklif-olustur) hatası: {e}")
            raise HTTPException(status_code=500, detail="Kredi işlemi tamamlanamadı, lütfen tekrar deneyin")
        if not getattr(kredi_sonuc, "data", None):
            raise HTTPException(status_code=402, detail="Yetersiz kredi")

        return {
            "basari": True,
            "kapsam": sonuc["kapsam"],
            "neden": sonuc["neden"],
            "yontem": sonuc["yontem"],
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ai/teklif-strateji")
def ai_teklif_strateji(
    istek: AnalizIstek,
    authorization: str = Header(None)
):
    """
    AI Fiyat/Teklif Stratejisi — teklif-olustur.html fiyat paneli için.
    İhalenin kategori/il kırılımındaki GERÇEK ortalama tenzilatı (analiz_pivot, tek-lot filtreli)
    AI'ya bağlam verip veri-temelli bir TEKLİF BANDI önerir. 1 kredi (teklif_strateji).
    (Metin teklif_ai → ai_ortak'tan gelir: DeepSeek birincil, Gemini yedek — env ile seçilir.)
    """
    kullanici_id = kullanici_dogrula(authorization)
    ihale_id = istek.ihale_id

    try:
        ilan_sonuc = supabase.table("ilanlar").select(
            "id, baslik, il, kategori, tur, yaklasik_maliyet_min, yaklasik_maliyet_max, tahmini_bedel, ilan_metni"
        ).eq("id", ihale_id).limit(1).execute()
        ilan = (ilan_sonuc.data or [None])[0]
        if not ilan:
            raise HTTPException(status_code=404, detail="İhale bulunamadı")

        # Kredi ön kontrolü
        kredi_bilgi = supabase.table("kullanici_krediler").select(
            "kalan_kredi"
        ).eq("kullanici_id", kullanici_id).single().execute()
        if (kredi_bilgi.data or {}).get("kalan_kredi", 0) < 1:
            raise HTTPException(status_code=402, detail="Yetersiz kredi")

        # Benzer geçmiş tenzilat (ort_tenzilat tek-lot filtreli — çok-lot bug'ı analiz_pivot içinde elenir).
        # ⚠️ 28 Tem ölçüm: analiz_pivot p_grup='kategori' 20sn'de TIMEOUT eder (2,2M sonuç satırı),
        #    p_grup='il' ~10sn'de döner. Kategori kırılımı yerine MV tabanlı sonuc_ozet (0,0sn) ile
        #    ülke geneli tenzilat tabanı veriliyor. Kategori kırılımı için MV gerekir (v2).
        kirilimlar = {}
        if ilan.get("il"):
            try:
                r = supabase.rpc("analiz_pivot", {"p_grup": "il", "p_il": ilan.get("il")}).execute()
                kirilimlar["il"] = (r.data or [])[:1]
            except Exception as e:
                print(f"  ⚠ analiz_pivot il (teklif-strateji) atlandı: {e}")
        try:
            r = supabase.rpc("sonuc_ozet", {}).execute()
            genel = (r.data or [])
            if genel:
                g = genel[0]
                kirilimlar["genel"] = [{
                    "grup_deger": "Türkiye geneli",
                    "ihale_sayisi": g.get("toplam"),
                    "ort_tenzilat": g.get("ort_tenzilat"),
                }]
        except Exception as e:
            print(f"  ⚠ sonuc_ozet (teklif-strateji) atlandı: {e}")

        # UV-1: şartname/ilan metnini AI'a okut → ihaleye ÖZGÜ kapsam/kalem/ölçek. Tenzilat verisi
        # zayıf/boş olsa bile kapsam-temelli strateji üretilebilir (kullanıcının "band veremiyorum" derdi).
        sartname_ozet = None
        try:
            so = sartname_oku(ilan.get("ilan_metni"),
                              {"baslik": ilan.get("baslik"), "kategori": ilan.get("kategori")})
            if so.get("basari"):
                sartname_ozet = so.get("veri")
        except Exception as e:
            print(f"  ⚠ sartname_oku (teklif-strateji) atlandı: {e}")

        # UV-1 Faz 1.5: şartname KONUSUYLA eşleşen geçmiş ihalelerin GERÇEK tenzilatı (il/genel'den
        # isabetli). En spesifik (uzun) konu kelimesinden başla; ilk anlamlı eşleşmeyi (≥3 ihale) al.
        # JENERİK terimler ('satın alma', 'malzeme'...) elenir → konuya-özgü eşleşme, generik tenzilat değil.
        _KONU_GENERIK = {
            "satın alma", "satin alma", "satınalma", "mal alımı", "mal alimi", "hizmet alımı",
            "hizmet alimi", "yapım işi", "yapim isi", "malzeme", "malzemesi", "alım", "alim",
            "alımı", "alimi", "temin", "hizmet", "yapım", "yapim", "işi", "isi", "ihale", "ihalesi",
        }
        if sartname_ozet and sartname_ozet.get("konu_kelimeler"):
            kelimeler = sorted(
                {k.strip() for k in sartname_ozet["konu_kelimeler"]
                 if k and len(k.strip()) >= 4 and k.strip().lower() not in _KONU_GENERIK},
                key=len, reverse=True)
            for kel in kelimeler[:4]:
                try:
                    kr = supabase.rpc("konu_tenzilat", {"p_kelime": kel}).execute()
                    if kr.data:
                        kirilimlar["konu"] = kr.data[:1]
                        break
                except Exception as e:
                    print(f"  ⚠ konu_tenzilat ({kel}) atlandı: {e}")

        sonuc = teklif_strateji_uret(ihale=ilan, kirilimlar=kirilimlar, sartname_ozet=sartname_ozet)
        if not sonuc["basari"]:
            raise HTTPException(status_code=500, detail=sonuc["hata"])

        try:
            kredi_sonuc = supabase.rpc("kredi_dus", {
                "p_kullanici_id": kullanici_id,
                "p_miktar": 1,
                "p_referans_id": ihale_id,
                "p_referans_tip": "ihale",
                # ⚠️ kredi_hareketleri_islem_turu_check YALNIZ 'analiz'/'yukleme' kabul eder
                #    (28 Tem: 'teklif_strateji' 23514 ile reddedildi → kredi düşmedi, endpoint 500).
                "p_islem_turu": "analiz",
                "p_aciklama": f"AI Fiyat Stratejisi: {(ilan.get('baslik') or '')[:50]}"
            }).execute()
        except Exception as e:
            print(f"  ⚠ kredi_dus (teklif-strateji) hatası: {e}")
            raise HTTPException(status_code=500, detail="Kredi işlemi tamamlanamadı, lütfen tekrar deneyin")
        if not getattr(kredi_sonuc, "data", None):
            raise HTTPException(status_code=402, detail="Yetersiz kredi")

        return {"basari": True, "metin": sonuc["metin"], "kirilimlar": kirilimlar}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ai/sartname-analiz")
def ai_sartname_analiz(istek: AnalizIstek, authorization: str = Header(None)):
    """
    UV-1 Faz 2 — TEKNİK ŞARTNAME ANALİZİ (PREMIUM/kredili). İhalenin teknik şartnamesini + birim fiyat
    cetvelini EKAP'tan İNDİRİR (Playwright, 406 aşımı + Gemini CAPTCHA), parse eder, AI'a okutup ihaleye
    ÖZGÜ teklif stratejisi üretir. İndirilen şartname ilanlar.sartname_metni'ye CACHE'lenir (tekrar
    indirmeyiz — maliyet düşer). Kredi: ilk indirme 3, cache'ten (yeniden indirmesiz) 1.
    ⚠️ YAVAŞ (~20-35 sn, Playwright): frontend "şartname indiriliyor/analiz ediliyor" göstermeli.
    """
    kullanici_id = kullanici_dogrula(authorization)
    ihale_id = istek.ihale_id
    _GENERIK = {"satın alma", "satin alma", "satınalma", "mal alımı", "mal alimi", "hizmet alımı",
                "hizmet alimi", "yapım işi", "yapim isi", "malzeme", "malzemesi", "alım", "alim",
                "alımı", "alimi", "temin", "hizmet", "yapım", "yapim", "işi", "isi", "ihale", "ihalesi"}
    try:
        ilan = (supabase.table("ilanlar").select(
            "id, baslik, il, kategori, tur, yaklasik_maliyet_min, yaklasik_maliyet_max, tahmini_bedel, "
            "ekap_ihale_id, sartname_metni, ilan_metni"
        ).eq("id", ihale_id).limit(1).execute().data or [None])[0]
        if not ilan:
            raise HTTPException(status_code=404, detail="İhale bulunamadı")

        cache_var = bool(ilan.get("sartname_metni"))
        gereken_kredi = 1 if cache_var else 3
        kredi_bilgi = supabase.table("kullanici_krediler").select("kalan_kredi").eq(
            "kullanici_id", kullanici_id).single().execute()
        if (kredi_bilgi.data or {}).get("kalan_kredi", 0) < gereken_kredi:
            raise HTTPException(status_code=402, detail=f"Bu özellik {gereken_kredi} kredi gerektirir")

        # ── Şartname metni: CACHE varsa kullan, yoksa Playwright ile İNDİR + cache'le ──
        sartname_metni = ilan.get("sartname_metni")
        dosyalar = []
        if not sartname_metni:
            if not ilan.get("ekap_ihale_id"):
                raise HTTPException(status_code=422, detail="Bu ihalede indirilebilir doküman kimliği yok")
            import asyncio
            from sartname_indir import indir_parse   # lazy: Playwright import ağır, sadece burada
            r = asyncio.run(indir_parse(str(ilan["ekap_ihale_id"])))
            if not r.get("basari") or not r.get("metin"):
                raise HTTPException(status_code=502, detail=f"Şartname indirilemedi: {r.get('hata')}")
            sartname_metni = r["metin"]
            dosyalar = r.get("dosyalar") or []
            supabase.table("ilanlar").update({
                "sartname_metni": sartname_metni, "sartname_indirildi": datetime.now(timezone.utc).isoformat()
            }).eq("id", ihale_id).execute()

        # ── AI şartnameyi oku (ilan_metni yerine ZENGİN şartname metni) ──
        so = sartname_oku(sartname_metni, {"baslik": ilan.get("baslik"), "kategori": ilan.get("kategori")})
        sartname_ozet = so.get("veri") if so.get("basari") else None

        # ── Kırılımlar: konu (şartname konusuyla) + il + genel ──
        kirilimlar = {}
        if sartname_ozet and sartname_ozet.get("konu_kelimeler"):
            kel = sorted({k.strip() for k in sartname_ozet["konu_kelimeler"]
                          if k and len(k.strip()) >= 4 and k.strip().lower() not in _GENERIK}, key=len, reverse=True)
            for k in kel[:4]:
                try:
                    kr = supabase.rpc("konu_tenzilat", {"p_kelime": k}).execute()
                    if kr.data:
                        kirilimlar["konu"] = kr.data[:1]
                        break
                except Exception as e:
                    print(f"  ⚠ konu_tenzilat ({k}) atlandı: {e}")
        if ilan.get("il"):
            try:
                kirilimlar["il"] = (supabase.rpc("analiz_pivot", {"p_grup": "il", "p_il": ilan["il"]}).execute().data or [])[:1]
            except Exception as e:
                print(f"  ⚠ analiz_pivot il (sartname-analiz) atlandı: {e}")
        try:
            g = (supabase.rpc("sonuc_ozet", {}).execute().data or [])
            if g:
                kirilimlar["genel"] = [{"grup_deger": "Türkiye geneli",
                                        "ihale_sayisi": g[0].get("toplam"), "ort_tenzilat": g[0].get("ort_tenzilat")}]
        except Exception as e:
            print(f"  ⚠ sonuc_ozet (sartname-analiz) atlandı: {e}")

        sonuc = teklif_strateji_uret(ihale=ilan, kirilimlar=kirilimlar, sartname_ozet=sartname_ozet)
        if not sonuc["basari"]:
            raise HTTPException(status_code=500, detail=sonuc["hata"])

        # ── Kredi düş (yalnız başarı sonrası; islem_turu='analiz' — CHECK kısıtı) ──
        try:
            kredi_sonuc = supabase.rpc("kredi_dus", {
                "p_kullanici_id": kullanici_id, "p_miktar": gereken_kredi,
                "p_referans_id": ihale_id, "p_referans_tip": "ihale", "p_islem_turu": "analiz",
                "p_aciklama": f"Şartname Analizi{' (cache)' if cache_var else ''}: {(ilan.get('baslik') or '')[:45]}"
            }).execute()
        except Exception as e:
            print(f"  ⚠ kredi_dus (sartname-analiz) hatası: {e}")
            raise HTTPException(status_code=500, detail="Kredi işlemi tamamlanamadı, lütfen tekrar deneyin")
        if not getattr(kredi_sonuc, "data", None):
            raise HTTPException(status_code=402, detail="Yetersiz kredi")

        return {"basari": True, "metin": sonuc["metin"], "sartname_ozet": sartname_ozet,
                "kirilimlar": kirilimlar, "dosyalar": dosyalar, "cache": cache_var, "dusulen_kredi": gereken_kredi}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/admin/scraper-cron")
async def scraper_tetikle(
    authorization: str = Header(None)
):
    """
    EKAP scraper'ı manuel tetikler.
    Sadece service key ile çağrılabilir.
    Render free tier'da cron job olmadığı için elle tetiklenir.
    """
    # Basit admin koruması — service key ile doğrula
    if not authorization:
        raise HTTPException(status_code=401, detail="Yetki gerekli")

    token = authorization.replace("Bearer ", "")
    if token != SUPABASE_KEY:
        raise HTTPException(status_code=403, detail="Yetkisiz")

    # NOT: worker.scraper_cron kaldırılmış sembolleri import ettiği için bozuktu (çağrıldığında ImportError→500).
    # Scraping artık VDS gece cron'u (run_scraper.sh) ile yapılıyor; bu endpoint kullanımdan kaldırıldı.
    raise HTTPException(status_code=503,
                        detail="Bu endpoint kullanımdan kaldırıldı — scraping VDS gece cron'u (run_scraper.sh) ile çalışıyor.")


@app.post("/ai/kurum-yorum")
def ai_kurum_yorum(istek: KurumYorumIstek, authorization: str = Header(None)):
    """
    AI Yorum Modülü — KURUM (kamu idaresi) değerlendirmesi (PREMIUM/kredili, 1 kredi).
    kurum_ozet + tekrar-kazanan firmalara (analiz_pivot) dayalı GROUNDED yorum; ai_yorumlari'na
    cache (veri değişmedikçe aynı yorum → tutarlılık). Metin DeepSeek (ai_ortak). anon-KAPALI.
    """
    kullanici_id = kullanici_dogrula(authorization)
    idare = (istek.idare or "").strip()
    if len(idare) < 3:
        raise HTTPException(status_code=400, detail="Kurum adı gerekli")
    kredi_bilgi = supabase.table("kullanici_krediler").select("kalan_kredi").eq(
        "kullanici_id", kullanici_id).single().execute()
    if (kredi_bilgi.data or {}).get("kalan_kredi", 0) < 1:
        raise HTTPException(status_code=402, detail="Bu özellik 1 kredi gerektirir")
    try:
        from ai_yorum import kurum_yorumla
        r = kurum_yorumla(supabase, idare)
        if not r.get("basari"):
            hata = r.get("hata") or "Yorum üretilemedi"
            raise HTTPException(status_code=404 if "veri yok" in hata else 500, detail=hata)
        try:
            kredi_sonuc = supabase.rpc("kredi_dus", {
                "p_kullanici_id": kullanici_id, "p_miktar": 1, "p_referans_id": None,
                "p_referans_tip": "kurum", "p_islem_turu": "analiz",
                "p_aciklama": f"Kurum Yorumu: {idare[:50]}"
            }).execute()
        except Exception as e:
            print(f"  ⚠ kredi_dus (kurum-yorum) hatası: {e}")
            raise HTTPException(status_code=500, detail="Kredi işlemi tamamlanamadı, lütfen tekrar deneyin")
        if not getattr(kredi_sonuc, "data", None):
            raise HTTPException(status_code=402, detail="Yetersiz kredi")
        return {"basari": True, "yorum": r["yorum"], "kaynak": r.get("kaynak")}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ai/firma-iletisim")
def ai_firma_iletisim(istek: FirmaIletisimIstek, authorization: str = Header(None)):
    """
    AI Firma İletişim Bilgileri (PREMIUM/kredili, 1 kredi) — Gemini + Google Search GROUNDING ile
    firmanın telefon/e-posta/adres/web/yetkili bilgisini WEB'DEN derler (firma_iletisim.py).
    KALICI cache: ai_yorumlari(varlik_tip='firma_iletisim') — aynı firma tekrar istenirse Gemini'ye
    GİTMEDEN + KREDİ DÜŞMEDEN döner (kota/maliyet tasarrufu, firma-yorum deseniyle tutarlı).
    ⚠️ Sonuç kesin değildir; frontend "AI web'den derledi, doğrulayın" uyarısını DAİMA gösterir.
    """
    kullanici_id = kullanici_dogrula(authorization)
    firma = (istek.firma or "").strip()
    if not firma:
        raise HTTPException(status_code=400, detail="Firma adı gerekli")
    try:
        # 0. Cache anahtarı (normalize) — normalize edilemezse ham ad
        try:
            anahtar = supabase.rpc("normalize_firma", {"ham_ad": firma}).execute().data or firma
        except Exception:
            anahtar = firma

        # 1. KALICI cache kontrolü (iletişim bilgisi nadir değişir → süresiz sakla)
        cache = supabase.table("ai_yorumlari").select("yorum").eq(
            "varlik_tip", "firma_iletisim").eq("varlik_anahtar", anahtar).limit(1).execute()
        onbellek = (cache.data or [None])[0]
        if onbellek and onbellek.get("yorum"):
            try:
                return {"basari": True, "cache": True, **json.loads(onbellek["yorum"])}
            except (ValueError, TypeError):
                pass  # bozuk cache → yeniden üret

        # 2. Kredi ön kontrolü (yalnız TAZE çekimde düşer)
        kredi_bilgi = supabase.table("kullanici_krediler").select("kalan_kredi").eq(
            "kullanici_id", kullanici_id).single().execute()
        if (kredi_bilgi.data or {}).get("kalan_kredi", 0) < 1:
            raise HTTPException(status_code=402, detail="Bu özellik 1 kredi gerektirir")

        # 3. Gemini grounding ile web'den çek
        from firma_iletisim import firma_iletisim_getir
        sonuc = firma_iletisim_getir(firma)
        if not sonuc["basari"]:
            raise HTTPException(status_code=500, detail=sonuc["hata"] or "İletişim bilgisi alınamadı")

        # 4. Kredi düş
        try:
            kredi_sonuc = supabase.rpc("kredi_dus", {
                "p_kullanici_id": kullanici_id, "p_miktar": 1, "p_referans_id": None,
                "p_referans_tip": "firma", "p_islem_turu": "analiz",
                "p_aciklama": f"AI Firma İletişim: {firma[:50]}"
            }).execute()
        except Exception as e:
            print(f"  ⚠ kredi_dus (firma-iletisim) hatası: {e}")
            raise HTTPException(status_code=500, detail="Kredi işlemi tamamlanamadı, lütfen tekrar deneyin")
        if not getattr(kredi_sonuc, "data", None):
            raise HTTPException(status_code=402, detail="Yetersiz kredi")

        # 5. KALICI cache'e yaz (veri + kaynaklar)
        govde = {"veri": sonuc["veri"], "kaynaklar": sonuc["kaynaklar"]}
        try:
            supabase.table("ai_yorumlari").upsert({
                "varlik_tip": "firma_iletisim", "varlik_anahtar": anahtar,
                "yorum": json.dumps(govde, ensure_ascii=False),
                "veri_hash": "web-grounding",
                "uretildi": datetime.now(timezone.utc).isoformat(),
            }, on_conflict="varlik_tip,varlik_anahtar").execute()
        except Exception as e:
            print(f"  ⚠ firma-iletisim cache yazılamadı: {e}")

        return {"basari": True, "cache": False, **govde}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
