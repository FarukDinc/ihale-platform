"""
İhalePlatform FastAPI — Backend API
Frontend'den gelen istekleri karşılar

Çalıştırma:
    uvicorn api:app --reload
"""

import os
from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from supabase import create_client, Client
from worker import kullanici_analiz_isle
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="İhalePlatform API", version="1.0.0")

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
    Kredi kontrolü, cache, Gemini analizi.
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

    import asyncio
    from worker import scraper_cron

    # Background'da çalıştır (timeout vermez)
    asyncio.create_task(scraper_cron())

    return {"basari": True, "mesaj": "Scraper arka planda başlatıldı"}
