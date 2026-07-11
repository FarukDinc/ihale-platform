"""
İhaleGlobal — İyzico Ödeme Entegrasyonu
Webhook ile Supabase kredi güncelleme

Kurulum:
    pip install iyzipay requests

İyzico Dashboard:
    https://merchant.iyzipay.com
    Ayarlar → API Anahtarları → API Key + Secret Key
    Ayarlar → Webhook → URL: https://ihale-api.onrender.com/webhook/iyzico

.env'e ekle:
    IYZICO_API_KEY=xxxiyzicoAPIkeyxxx
    IYZICO_SECRET_KEY=xxxiyzicoSECRETkeyxxx
    IYZICO_BASE_URL=https://sandbox.iyzipay.com  (test)
    # Canlıya geçince: https://api.iyzipay.com
"""

import os
import calendar
import hashlib
import hmac
import json
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Request, HTTPException, Header
from pydantic import BaseModel
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

router = APIRouter()

# ── Yapılandırma ──────────────────────────────────────────
IYZICO_API_KEY    = os.environ.get("IYZICO_API_KEY", "xxxiyzicoAPIkeyxxx")
IYZICO_SECRET_KEY = os.environ.get("IYZICO_SECRET_KEY", "xxxiyzicoSECRETkeyxxx")
IYZICO_BASE_URL   = os.environ.get("IYZICO_BASE_URL", "https://sandbox.iyzipay.com")

SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ── Plan tanımları ────────────────────────────────────────
PLANLAR = {
    "standart": {
        "ad":           "Standart Plan",
        "fiyat_tl":     1490,
        "kredi":        50,
        "sure_gun":     30
    },
    "kurumsal": {
        "ad":           "Kurumsal Plan",
        "fiyat_tl":     3990,
        "kredi":        250,
        "sure_gun":     30
    }
}


# ── Request Modelleri ─────────────────────────────────────
class KuponKullan(BaseModel):
    kod: str


class OdemeBaslat(BaseModel):
    plan_kodu: str          # 'standart' | 'kurumsal'
    kart_sahibi_ad: str
    kart_sahibi_soyad: str
    kart_no: str
    son_kullanma_ay: str    # "12"
    son_kullanma_yil: str   # "2026"
    cvc: str
    taksit: int = 1


# ── İyzico İmza Oluştur ───────────────────────────────────
def iyzico_imza_olustur(params: dict) -> str:
    """
    İyzico PKI imza formatı:
    apiKey + randomKey + her parametre alfabetik sırayla
    """
    pki = f"apiKey={IYZICO_API_KEY}&randomKey={params['locale']}"
    for k in sorted(params.keys()):
        if k not in ("apiKey", "locale"):
            pki += f"&{k}={params[k]}"

    imza = hmac.new(
        IYZICO_SECRET_KEY.encode("utf-8"),
        pki.encode("utf-8"),
        hashlib.sha1
    ).hexdigest()

    return imza


# ── Ödeme Başlat ──────────────────────────────────────────
import iyzipay

def iyzico_odeme_yap(
    kullanici_id: str,
    kullanici_email: str,
    plan_kodu: str,
    kart_bilgileri: dict
) -> dict:
    """
    İyzico üzerinden ödeme başlatır.
    Başarılıysa Supabase'i günceller.
    """
    if plan_kodu not in PLANLAR:
        raise ValueError(f"Geçersiz plan: {plan_kodu}")

    plan = PLANLAR[plan_kodu]
    siparis_id = f"IHP-{kullanici_id[:8]}-{uuid.uuid4().hex[:8].upper()}"

    # İyzico seçenekleri
    options = {
        "api_key":    IYZICO_API_KEY,
        "secret_key": IYZICO_SECRET_KEY,
        "base_url":   IYZICO_BASE_URL
    }

    # Ödeme isteği
    request_data = {
        "locale":       "tr",
        "conversationId": siparis_id,
        "price":        str(plan["fiyat_tl"]),
        "paidPrice":    str(plan["fiyat_tl"]),
        "currency":     "TRY",
        "installment":  str(kart_bilgileri.get("taksit", 1)),
        "paymentChannel": "WEB",
        "paymentGroup": "SUBSCRIPTION",

        "paymentCard": {
            "cardHolderName": f"{kart_bilgileri['ad']} {kart_bilgileri['soyad']}",
            "cardNumber":     kart_bilgileri["kart_no"].replace(" ", ""),
            "expireMonth":    kart_bilgileri["ay"],
            "expireYear":     kart_bilgileri["yil"],
            "cvc":            kart_bilgileri["cvc"],
            "registerCard":   "0"
        },

        "buyer": {
            "id":                 kullanici_id,
            "name":               kart_bilgileri["ad"],
            "surname":            kart_bilgileri["soyad"],
            "email":              kullanici_email,
            "identityNumber":     "11111111111",  # Gerçek sistemde kullanıcıdan al
            "registrationAddress": "Türkiye",
            "city":               "İstanbul",
            "country":            "Turkey",
            "ip":                 "85.34.78.112"  # Gerçek sistemde request.client.host
        },

        "shippingAddress": {
            "contactName": f"{kart_bilgileri['ad']} {kart_bilgileri['soyad']}",
            "city":        "İstanbul",
            "country":     "Turkey",
            "address":     "Türkiye"
        },

        "billingAddress": {
            "contactName": f"{kart_bilgileri['ad']} {kart_bilgileri['soyad']}",
            "city":        "İstanbul",
            "country":     "Turkey",
            "address":     "Türkiye"
        },

        "basketItems": [{
            "id":        plan_kodu,
            "name":      plan["ad"],
            "category1": "Yazılım",
            "itemType":  "VIRTUAL",
            "price":     str(plan["fiyat_tl"])
        }]
    }

    # İyzico'ya gönder
    odeme = iyzipay.Payment().create(request_data, options)
    sonuc = json.loads(odeme.read().decode("utf-8"))

    if sonuc.get("status") == "success":
        # Supabase güncelle
        kredi_yukle(
            kullanici_id=kullanici_id,
            plan_kodu=plan_kodu,
            kredi_miktari=plan["kredi"],
            siparis_id=siparis_id,
            odeme_miktari=plan["fiyat_tl"]
        )
        return {
            "basari": True,
            "siparis_id": siparis_id,
            "mesaj": f"{plan['ad']} aktifleştirildi. {plan['kredi']} kredi yüklendi."
        }
    else:
        hata = sonuc.get("errorMessage", "Ödeme başarısız")
        return {"basari": False, "hata": hata}


# ── Supabase Kredi Yükleme ────────────────────────────────
def kredi_yukle(
    kullanici_id: str,
    plan_kodu: str,
    kredi_miktari: int,
    siparis_id: str,
    odeme_miktari: int,
    plan_bitis: str = None
):
    """Başarılı ödemeden (veya kupon kullanımından) sonra Supabase'i günceller.
    plan_bitis verilirse (kupon akışı) plana bir bitiş tarihi eklenir;
    kart ödemesinde (plan_bitis=None) mevcut davranış değişmez."""
    plan = PLANLAR[plan_kodu]

    # Kredi güncelle
    mevcut = supabase.table("kullanici_krediler").select(
        "toplam_kredi"
    ).eq("kullanici_id", kullanici_id).single().execute()

    yeni_toplam = (mevcut.data.get("toplam_kredi", 0) if mevcut.data else 0) + kredi_miktari

    guncelleme = {
        "toplam_kredi":  yeni_toplam,
        "plan":          plan_kodu,
        "plan_baslangic": datetime.now().isoformat()
    }
    if plan_bitis:
        guncelleme["plan_bitis"] = plan_bitis

    supabase.table("kullanici_krediler").update(guncelleme).eq("kullanici_id", kullanici_id).execute()

    # Hareket kaydı
    supabase.table("kredi_hareketleri").insert({
        "kullanici_id": kullanici_id,
        "miktar":       kredi_miktari,
        "islem_turu":   "yukleme",
        "aciklama":     f"{plan['ad']} — Sipariş: {siparis_id} — {odeme_miktari} TL"
    }).execute()

    # Bildirim
    supabase.table("bildirimler").insert({
        "kullanici_id": kullanici_id,
        "baslik":       "Kredi yüklendi! 🎉",
        "icerik":       f"{plan['ad']} aktivasyonu: {kredi_miktari} kredi hesabınıza eklendi.",
        "tur":          "kredi"
    }).execute()


# ── FastAPI Endpoint'leri ─────────────────────────────────
from fastapi import Depends

def kullanici_dogrula_payment(authorization: str = Header(None)) -> str:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token gerekli")
    token = authorization.replace("Bearer ", "")
    try:
        user = supabase.auth.get_user(token)
        return user.user.id, user.user.email
    except Exception:
        raise HTTPException(status_code=401, detail="Geçersiz token")


@router.post("/odeme/baslat")
async def odeme_baslat(
    istek: OdemeBaslat,
    authorization: str = Header(None)
):
    """
    Frontend'den ödeme isteği gelir.
    Kart bilgileri burada İyzico'ya gönderilir.
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Token gerekli")

    token = authorization.replace("Bearer ", "")
    try:
        user = supabase.auth.get_user(token)
        kullanici_id = user.user.id
        email = user.user.email
    except Exception:
        raise HTTPException(status_code=401, detail="Geçersiz token")

    if istek.plan_kodu not in PLANLAR:
        raise HTTPException(status_code=400, detail="Geçersiz plan")

    sonuc = iyzico_odeme_yap(
        kullanici_id=kullanici_id,
        kullanici_email=email,
        plan_kodu=istek.plan_kodu,
        kart_bilgileri={
            "ad":      istek.kart_sahibi_ad,
            "soyad":   istek.kart_sahibi_soyad,
            "kart_no": istek.kart_no,
            "ay":      istek.son_kullanma_ay,
            "yil":     istek.son_kullanma_yil,
            "cvc":     istek.cvc,
            "taksit":  istek.taksit
        }
    )

    if not sonuc["basari"]:
        raise HTTPException(status_code=402, detail=sonuc["hata"])

    return sonuc


@router.post("/webhook/iyzico")
async def iyzico_webhook(request: Request):
    """
    İyzico'dan gelen webhook bildirimi.
    Abonelik yenileme, iptal vb. için.
    """
    body = await request.body()
    veri = json.loads(body)

    # İmza doğrula
    gelen_imza = request.headers.get("x-iyz-signature", "")
    beklenen = hmac.new(
        IYZICO_SECRET_KEY.encode(),
        body,
        hashlib.sha256
    ).hexdigest()

    if gelen_imza != beklenen:
        raise HTTPException(status_code=400, detail="Geçersiz imza")

    # Olay tipine göre işle
    olay = veri.get("eventType", "")

    if olay == "SUBSCRIPTION_ORDER_SUCCESS":
        # Abonelik yenilendi
        kullanici_id = veri.get("merchantMemberId")
        plan_kodu    = veri.get("subscriptionProductName", "").lower()
        if kullanici_id and plan_kodu in PLANLAR:
            plan = PLANLAR[plan_kodu]
            kredi_yukle(
                kullanici_id=kullanici_id,
                plan_kodu=plan_kodu,
                kredi_miktari=plan["kredi"],
                siparis_id=veri.get("conversationId", "webhook"),
                odeme_miktari=plan["fiyat_tl"]
            )

    return {"status": "ok"}


@router.post("/plan-iptal")
async def plan_iptal(authorization: str = Header(None)):
    """Kullanıcının planını ücretsize düşürür. service_role ile yazar çünkü
    kullanici_krediler RLS'i client yazımını engeller (güvenlik gereği salt-okur)."""
    kullanici_id, _email = kullanici_dogrula_payment(authorization)
    try:
        supabase.table("kullanici_krediler").update({
            "plan": "free",
            "plan_bitis": datetime.now().isoformat(),
        }).eq("kullanici_id", kullanici_id).execute()
        supabase.table("bildirimler").insert({
            "kullanici_id": kullanici_id,
            "baslik": "Plan iptal edildi",
            "icerik": "Aboneliğiniz ücretsiz plana düşürüldü.",
            "tur": "sistem",
        }).execute()
        return {"basari": True, "mesaj": "Planınız ücretsize düşürüldü"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _ay_ekle(dt: datetime, ay: int) -> datetime:
    """dt'ye takvim ayı ekler (31 Oca + 1 ay → 28/29 Şub gibi taşmaları düzeltir)."""
    ay_toplam = dt.month - 1 + ay
    yil = dt.year + ay_toplam // 12
    ay_yeni = ay_toplam % 12 + 1
    gun = min(dt.day, calendar.monthrange(yil, ay_yeni)[1])
    return dt.replace(year=yil, month=ay_yeni, day=gun)


@router.post("/kupon-kullan")
async def kupon_kullan(istek: KuponKullan, authorization: str = Header(None)):
    """Kullanıcı bir kupon kodu girer; geçerliyse planı service_role ile
    doğrudan aktifleştirir (kullanici_krediler RLS salt-okur, bkz. plan-iptal)."""
    kullanici_id, _email = kullanici_dogrula_payment(authorization)
    kod = istek.kod.strip().upper()
    if not kod:
        raise HTTPException(status_code=400, detail="Kupon kodu girin")

    sonuc = supabase.table("kuponlar").select("*").eq("kod", kod).limit(1).execute()
    satirlar = sonuc.data or []
    if not satirlar:
        raise HTTPException(status_code=404, detail="Kupon kodu bulunamadı")
    kupon = satirlar[0]

    if not kupon.get("aktif", True):
        raise HTTPException(status_code=400, detail="Bu kupon devre dışı bırakılmış")
    if kupon.get("kullanim_sayisi", 0) >= kupon.get("max_kullanim", 1):
        raise HTTPException(status_code=400, detail="Bu kupon kullanım limitine ulaşmış")

    bitis_str = kupon.get("son_kullanma_tarihi")
    if bitis_str:
        bitis_dt = datetime.fromisoformat(bitis_str.replace("Z", "+00:00"))
        if bitis_dt < datetime.now(timezone.utc):
            raise HTTPException(status_code=400, detail="Bu kuponun süresi dolmuş")

    zaten_kullanildi = supabase.table("kupon_kullanimlari").select("id") \
        .eq("kupon_id", kupon["id"]).eq("kullanici_id", kullanici_id).execute()
    if zaten_kullanildi.data:
        raise HTTPException(status_code=400, detail="Bu kuponu zaten kullandınız")

    plan_kodu = kupon["plan_kodu"]
    plan = PLANLAR[plan_kodu]
    plan_bitis = _ay_ekle(datetime.now(timezone.utc), kupon["sure_ay"]).isoformat()

    kredi_yukle(
        kullanici_id=kullanici_id,
        plan_kodu=plan_kodu,
        kredi_miktari=plan["kredi"],
        siparis_id=f"KUPON-{kod}",
        odeme_miktari=0,
        plan_bitis=plan_bitis,
    )

    supabase.table("kuponlar").update({
        "kullanim_sayisi": kupon.get("kullanim_sayisi", 0) + 1
    }).eq("id", kupon["id"]).execute()
    supabase.table("kupon_kullanimlari").insert({
        "kupon_id": kupon["id"],
        "kullanici_id": kullanici_id,
    }).execute()

    return {
        "basari": True,
        "mesaj": f"{plan['ad']} — {kupon['sure_ay']} ay ücretsiz aktifleştirildi!",
        "plan": plan_kodu,
        "plan_bitis": plan_bitis,
    }


@router.get("/planlar")
def planlari_getir():
    """Mevcut planları döndürür — herkese açık."""
    return {
        "basari": True,
        "planlar": [
            {
                "kod":       k,
                "ad":        v["ad"],
                "fiyat_tl":  v["fiyat_tl"],
                "kredi":     v["kredi"],
                "sure_gun":  v["sure_gun"]
            }
            for k, v in PLANLAR.items()
        ]
    }
