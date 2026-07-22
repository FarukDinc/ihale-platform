"""
EKAP Scraper v2 — httpx tabanlı, Playwright gerektirmez

Akış:
  1. httpx + crypto headers ile doğrudan EKAP API'ye bağlanır
  2. Tüm aktif ihaleleri çeker (GetListByParameters)
  3. Her ihale için:
     - İtirazen şikayet bedeli → yaklaşık maliyet aralığı
     - Detay bilgileri + ilan HTML
     - Doküman listesi (GetDokumanListByIhaleId)
     - Doküman URL'leri (GetDokumanUrl) → Eski EKAP CAPTCHA → Supabase Storage
  4. Supabase 'ilanlar' tablosuna upsert eder

Env:
    SUPABASE_URL, SUPABASE_SERVICE_KEY
    EKAP_BELGE_INDIR=1    (belge indirme aktif)
    EKAP_DETAY_LIMIT      (test: kaç ihale için detay çekilsin, 0=hepsi)
    GEMINI_API_KEY        (CAPTCHA çözme için, zorunlu)
    EKAP_HAVUZ=0          (KAÇIŞ KAPISI: proxy havuzunu kapat, eski tek-client
                           davranışına dön — gece cron'u havuz yüzünden kırılırsa)
    EKAP_ESZAMANLI        (detay çekme eşzamanlılığı; boşsa havuzda 4, havuzsuz 8)
    PROXY_LIST vb.        (istek başına IP rotasyonu — bkz. proxy_havuz.py)
"""

import asyncio
import base64
import hashlib
import io
import json
import os
import re
import ssl
import time
import uuid
from datetime import datetime, timezone

import httpx
from PIL import Image
from supabase import create_client
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad
from Crypto.Random import get_random_bytes

# ── Konfigürasyon ─────────────────────────────────────────
SUPABASE_URL  = os.environ.get("SUPABASE_URL",  "https://lpgelwfoarhouollhwur.supabase.co")
SUPABASE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")

BELGE_INDIR   = os.environ.get("EKAP_BELGE_INDIR", "0") == "1"   # ağır: indir + Gemini CAPTCHA + Storage (ileride müşteri başına)
BELGE_LINK    = os.environ.get("EKAP_BELGE_LINK",  "1") == "1"   # hafif: sadece EKAP indirme linkini sakla (varsayılan)
DETAY_LIMIT   = int(os.environ.get("EKAP_DETAY_LIMIT", "0"))
GEMINI_KEY    = os.environ.get("GEMINI_API_KEY", "")

# Proxy havuzu (istek başına IP rotasyonu) VARSAYILAN AÇIK.
# EKAP_HAVUZ=0 → kaçış kapısı: eski tek-AsyncClient davranışı (VDS IP'sinden).
# Gece cron'u (run_scraper.sh) havuz yüzünden kırılırsa .env'e EKAP_HAVUZ=0
# yazmak yeterli — run_scraper.sh'e DOKUNMADAN eski davranışa dönülür.
HAVUZ_AKTIF   = os.environ.get("EKAP_HAVUZ", "1").strip().lower() not in ("0", "hayir", "false")

# Eşzamanlılık havuz tavanına uydurulur: havuzun küresel tavanı 600 istek/dk
# (=10/sn), IP başına soğuma 3sn. Eski sabit 8 görev × ihale başına 2-3 istek
# tavanın üstünde üretim yapar; havuz bekleterek frenler ama async yolda
# küresel bekleme yarışa açık (eşzamanlı görevler bayat _son_kuresel görüp aynı
# anda ateşleyebilir → anlık patlama ≈ görev sayısı). Fazla üretimi kaynağında
# kısıyoruz: havuz modunda 4 görev (~3-4 istek/sn, patlama ≤4 — tavanın güvenli
# altında), havuzsuz eski davranış 8.
ESZAMANLI     = int(os.environ.get("EKAP_ESZAMANLI", "") or ("4" if HAVUZ_AKTIF else "8"))
SAYFA_BOYUTU  = 100
STORAGE_BUCKET = "belgeler"

BASE = "https://ekapv2.kik.gov.tr"

ENDPOINTS = {
    "liste":    "/b_ihalearama/api/Ihale/GetListByParameters",
    "itiraz":   "/b_ihalearama/api/IhaleDetay/GetByIdItirazenSikayetBasvuruBedel",
    "detay":    "/b_ihalearama/api/IhaleDetay/GetByIhaleIdIhaleDetay",
    "dok_liste":"/b_ihalearama/api/IhaleDetay/GetDokumanListByIhaleId",
    "dok_url":  "/b_ihalearama/api/EkapDokumanYonlendirme/GetDokumanUrl",
}

CRYPTO_KEY = b"Qm2LtXR0aByP69vZNKef4wMJ"

BASE_HEADERS = {
    "Accept":       "application/json",
    "Content-Type": "application/json",
    "api-version":  "v1",
    # ⚠️ ŞART — bu başlık yoksa EKAP açıklama alanlarını ÇEVİRMEDEN döndürür:
    #   usul  -> 'TENDER_SEARCH.MAIN.PAGEITEM.TENDER_TYPE TENDER_SEARCH.ENUM'  (i18n anahtarı)
    #   durum -> 'Tender Canceled'                                             (İngilizce)
    # Başlıkla: 'İhale Usulü: Açık' / 'İhale İptal Edilmiş'.
    # Ölçüldü 20 Tem: bu eksiklik yüzünden ilanlar.usul'de 1.297 satır ham
    # i18n anahtarıyla dolmuş. YALNIZ Accept-Language işe yarıyor — lang,
    # culture, X-Culture denendi, hiçbiri etkilemiyor.
    "Accept-Language": "tr-TR,tr;q=0.9",
    "Origin":       BASE,
    "User-Agent":   (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/138.0.0.0 Safari/537.36"
    ),
}


# ── SSL context (EKAP eski cipher gerektiriyor) ───────────
def ssl_ctx():
    ctx = ssl.create_default_context()
    ctx.set_ciphers("DEFAULT@SECLEVEL=1")
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


# ── Eski EKAP SSL context ────────────────────────────────
def old_ekap_ssl():
    ctx = ssl.create_default_context()
    ctx.set_ciphers("DEFAULT@SECLEVEL=1")
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


# ── Gemini CAPTCHA çözücü ─────────────────────────────────
def _captcha_temizle(img_bytes: bytes) -> bytes:
    """
    EKAP CAPTCHA'sını gürültüden arındırır.
    Arka planda kırmızı ihale metni (gürültü) var; soru/sayı koyu renkte.
    Sadece koyu pikselleri tutup 2x büyüterek okunabilirliği artırır.
    Çıktı her zaman PNG'dir (Gemini BMP desteklemez).
    """
    import numpy as np

    im = Image.open(io.BytesIO(img_bytes)).convert("RGB")
    arr = np.asarray(im).astype(int)
    R, G, B = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]
    # Eşiği adaptif seç: çok az koyu piksel kalırsa eşiği yükselt
    dark = (R < 110) & (G < 110) & (B < 110)
    for thr in (140, 170, 200):
        if dark.mean() >= 0.01:
            break
        dark = (R < thr) & (G < thr) & (B < thr)
    out = np.full(arr.shape[:2], 255, dtype=np.uint8)
    out[dark] = 0
    clean = Image.fromarray(out, "L").resize((im.width * 2, im.height * 2), Image.LANCZOS)
    buf = io.BytesIO()
    clean.save(buf, "PNG")
    return buf.getvalue()


_CAPTCHA_PROMPT = (
    "Bu temizlenmiş bir EKAP (Türk kamu ihalesi) CAPTCHA resmidir.\n"
    "SOL tarafta Türkçe bir soru/ifade, SAĞ tarafta rakamlarla bir sayı var.\n"
    "SOL bölümü çöz:\n"
    "  - Matematik ise hesapla (örn '7 + dört' → 11)\n"
    "  - 'Yedi yüz on üç sayısını rakamla yazınız' gibi ise sayıya çevir (→ 713)\n"
    "  - 'Hangisi büyük/küçük harfle yazılmıştır? KIRMIZI, on' gibi ise doğru KELİMEYİ seç\n"
    "  - 'N. sıradaki sayı kaçtır? 9 1 5' gibi ise ilgili sayıyı seç\n"
    "Cevap bir SAYI ise rakamla, bir KELİME ise küçük harfle yaz.\n"
    "SAĞ taraftaki sayıyı olduğu gibi oku.\n"
    "SADECE şu formatta yanıt ver, başka hiçbir şey yazma:\n"
    "SOL: <soldaki cevap>\n"
    "SAĞ: <sağdaki sayı>"
)


def captcha_coz_gemini(img_bytes: bytes) -> str | None:
    """
    Gemini multimodal ile EKAP CAPTCHA'yı çözer.
    Gürültü temizleme + SOL(soru cevabı)+SAĞ(doğrulama sayısı) birleştirme.
    Doğru cevap formatı: '<soru_cevabı><sağdaki_sayı>' (örn 'zil87075', '71351945').
    """
    if not GEMINI_KEY:
        return None
    try:
        from google import genai
        from google.genai import types
    except ImportError:
        print("    ⚠ google-genai kurulu değil: pip install google-genai")
        return None

    png_bytes = _captcha_temizle(img_bytes)

    client_g = genai.Client(api_key=GEMINI_KEY)
    for model in ["gemini-2.5-flash", "gemini-2.5-flash-lite"]:
        try:
            resp = client_g.models.generate_content(
                model=model,
                contents=[
                    types.Part.from_bytes(data=png_bytes, mime_type="image/png"),
                    _CAPTCHA_PROMPT,
                ],
            )
            raw = resp.text.strip()
            sol_m = re.search(r"SOL\s*:\s*(\S+)", raw, re.I)
            sag_m = re.search(r"SA[ĞG]\s*:\s*(\S+)", raw, re.I)
            if not (sol_m and sag_m):
                continue
            sol = sol_m.group(1).strip(".\"'").lower()
            sag = re.sub(r"\D", "", sag_m.group(1))
            cevap = f"{sol}{sag}"
            return cevap if (sol and sag) else None
        except Exception as e:
            err = str(e)
            if "429" in err or "503" in err or "RESOURCE_EXHAUSTED" in err:
                time.sleep(3)
                continue
            print(f"    ✗ Gemini {model}: {err[:80]}")
    return None


# ── Eski EKAP CAPTCHA akışı ───────────────────────────────
def _hidden_fields(text: str) -> dict:
    """ASP.NET WebForms sayfasındaki tüm hidden input'ları çıkarır (ViewState dahil)."""
    fd: dict = {}
    for m in re.finditer(r'<input[^>]+type="hidden"[^>]+>', text):
        tag = m.group()
        nm = re.search(r'name="([^"]+)"', tag)
        vl = re.search(r'value="([^"]*)"', tag)
        if nm and nm.group(1) not in fd:
            fd[nm.group(1)] = (vl.group(1) if vl else "").replace("&amp;", "&")
    return fd


def _dosya_mi(resp) -> bytes | None:
    """Yanıt gerçek bir belge (ZIP/PDF/octet-stream) ise içeriğini döndürür."""
    magic = resp.content[:4]
    ct = resp.headers.get("content-type", "").lower()
    cd = resp.headers.get("content-disposition", "")
    if magic == b"PK\x03\x04" or magic == b"%PDF":
        return resp.content
    if ("zip" in ct or "pdf" in ct or "octet-stream" in ct or cd) and len(resp.content) > 1000:
        return resp.content
    return None


async def ekap_captcha_indir(captcha_url: str) -> bytes | None:
    """
    EKAP belge indirme — CAPTCHA korumalı 3 adımlı akış:
      1) GET VatandasIlanGoruntuleme → IlanDokumanDownload.aspx'e yönlenir (CAPTCHA sayfası)
      2) CAPTCHA çöz + POST → "İhale Dokümanı başarıyla indirilmiştir" onay sayfası
      3) btnTmpNormal postback (yeni ViewState ile) → gerçek ZIP/PDF dosyası
    CAPTCHA başarısızsa 4 deneme yapılır (her denemede taze sayfa+kota dostu).
    """
    from urllib.parse import urljoin

    headers_html = {
        "User-Agent":      "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/138.0.0.0",
        "Accept":          "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "tr-TR,tr;q=0.9",
    }
    origin = "https://ekap.kik.gov.tr"

    async with httpx.AsyncClient(
        verify=old_ekap_ssl(), timeout=90.0, follow_redirects=True
    ) as old_cl:
        for deneme in range(4):
            # ── ADIM 1: CAPTCHA sayfasını yükle (redirect zinciri izlenir) ──
            try:
                r = await old_cl.get(captcha_url, headers=headers_html)
            except Exception as e:
                print(f"      ✗ CAPTCHA GET hatası: {e}")
                return None

            # Yönlendirme sonrası GERÇEK sayfa URL'i — form action bunu baz almalı
            final_url = str(r.url)
            text = r.text

            # Direkt dosya geldiyse (CAPTCHA bypass — nadiren)
            direkt = _dosya_mi(r)
            if direkt:
                print(f"      ✓ Direkt indirildi ({len(direkt)//1024}KB)")
                return direkt

            # Form action (final_url'e göre çöz — /EKAP/Ilan/ path'i kritik)
            fa_m = re.search(r'<form[^>]+action="([^"]+)"', text)
            form_action = urljoin(final_url, fa_m.group(1).replace("&amp;", "&")) if fa_m else final_url

            form_data = _hidden_fields(text)
            form_data["__EVENTTARGET"]   = "ctl00$btnCaptchaProtect"
            form_data["__EVENTARGUMENT"] = ""

            # CAPTCHA resmini çıkar (capImg <img src="data:...">)
            idx = text.find("capImg")
            if idx < 0:
                print("      ✗ CAPTCHA resmi bulunamadı")
                return None
            src_m = re.search(r'src="(data:image/[^"]+)"',
                              text[text.rfind("<img", 0, idx):text.find(">", idx) + 1])
            if not src_m:
                print("      ✗ CAPTCHA src bulunamadı")
                return None
            img_bytes = base64.b64decode(src_m.group(1).split(",", 1)[1])

            # Gemini ile çöz (sync → thread pool)
            loop  = asyncio.get_event_loop()
            cevap = await loop.run_in_executor(None, captcha_coz_gemini, img_bytes)
            if not cevap:
                print(f"      ✗ CAPTCHA çözülemedi (deneme {deneme+1})")
                await asyncio.sleep(2)
                continue
            print(f"      ⚡ CAPTCHA ({deneme+1}. deneme): '{cevap}'")
            form_data["ctl00$capEkapMaster$txtCaptcha"] = cevap

            # ── ADIM 2: CAPTCHA POST → onay sayfası ──
            try:
                r2 = await old_cl.post(
                    form_action, data=form_data,
                    headers={**headers_html, "Content-Type": "application/x-www-form-urlencoded",
                             "Referer": final_url, "Origin": origin},
                )
            except Exception as e:
                print(f"      ✗ CAPTCHA POST hatası: {e}")
                return None

            # Bazı durumlarda dosya doğrudan gelir
            direkt2 = _dosya_mi(r2)
            if direkt2:
                print(f"      ✓ Dosya (adım 2) {len(direkt2)//1024}KB")
                return direkt2

            onay = ("başarıyla indir" in r2.text) or ("basariyla indir" in r2.text.lower())
            if not onay:
                yanlis = any(k in r2.text.lower() for k in ("güvenlik kod", "hatalı", "geçersiz", "yanlış"))
                print(f"      ✗ CAPTCHA {'reddedildi' if yanlis else 'onay yok'} (deneme {deneme+1})")
                await asyncio.sleep(2)
                continue

            # ── ADIM 3: btnTmpNormal postback → gerçek dosya ──
            final2 = str(r2.url)
            fa2 = re.search(r'<form[^>]+action="([^"]+)"', r2.text)
            action2 = urljoin(final2, fa2.group(1).replace("&amp;", "&")) if fa2 else final2
            fd2 = _hidden_fields(r2.text)
            fd2["__EVENTTARGET"]   = "ctl00$ContentPlaceHolder1$UcIhaleDokumanDownload1$btnTmpNormal"
            fd2["__EVENTARGUMENT"] = ""
            try:
                r3 = await old_cl.post(
                    action2, data=fd2,
                    headers={**headers_html, "Content-Type": "application/x-www-form-urlencoded",
                             "Referer": final2, "Origin": origin},
                )
            except Exception as e:
                print(f"      ✗ Belge postback hatası: {e}")
                return None

            dosya = _dosya_mi(r3)
            if dosya:
                cd = r3.headers.get("content-disposition", "")
                ad = re.search(r'filename=([^;]+)', cd)
                print(f"      ✓ Belge indirildi ({len(dosya)//1024//1024 or len(dosya)//1024}{'MB' if len(dosya)>1_000_000 else 'KB'})"
                      f"{' — ' + ad.group(1).strip() if ad else ''}")
                return dosya

            print(f"      ✗ Belge postback dosya döndürmedi ({r3.status_code}, {len(r3.content)}B)")
            await asyncio.sleep(2)

    return None


# ── Crypto header üretimi ─────────────────────────────────
def crypto_headers():
    guid = str(uuid.uuid4())
    iv   = get_random_bytes(16)
    ts   = str(int(time.time() * 1000))

    def enc(plaintext):
        cipher = AES.new(CRYPTO_KEY, AES.MODE_CBC, iv)
        return base64.b64encode(cipher.encrypt(pad(plaintext.encode(), 16))).decode()

    return {
        "X-Custom-Request-Guid": guid,
        "X-Custom-Request-Siv":  base64.b64encode(iv).decode(),
        "X-Custom-Request-R8id": enc(guid),
        "X-Custom-Request-Ts":   enc(ts),
    }


# ── Tek HTTP POST ─────────────────────────────────────────
async def post(baglanti, endpoint: str, data: dict) -> dict:
    """
    İlk parametre İKİ TİPTEN biri olabilir — çalışma anında ayırt edilir:
      · httpx.AsyncClient   → eski davranış, doğrudan bağlantı
      · AsyncProxyHavuzu    → istek başına IP rotasyonu (proxy_havuz)

    NEDEN ÇALIŞMA-ANI AYRIMI: bu fonksiyonu iki dış script import ediyor
    (ilan_metni_backfill.py:44, ekap_ilan_metni_sonda.py:27) ve ikisi de
    AsyncClient geçiyor. İmzayı doğrudan havuza çevirmek onları IMPORT anında
    değil ÇALIŞMA anında kırardı: 'AsyncClient' object has no attribute 'istek'.
    Geriye dönük uyumlu tutup çağıranları tek tek geçiriyoruz.
    """
    headers = {**BASE_HEADERS, **crypto_headers()}
    havuz_mu = hasattr(baglanti, "istek")
    try:
        if havuz_mu:
            async with baglanti.istek() as ist:
                r = await ist.client.post(f"{BASE}{endpoint}", json=data,
                                          headers=headers, timeout=30.0)
                ist.yanit(r)      # yalnız 403/407/429/5xx ucu cezalandırır
            # raise_for_status BLOĞUN DIŞINDA: içeride atılsaydı context manager
            # HER 4xx'i (404 dahil) istisna sayıp ucu cezalandırırdı. Oysa 404
            # bir uygulama yanıtı ("kayıt yok"); ceza kararını yalnız ist.yanit()
            # verir — aksi halde havuz kendi kendini yer (bkz. proxy_havuz
            # _Kiralama.yanit docstring'i).
            r.raise_for_status()
            return r.json()
        r = await baglanti.post(f"{BASE}{endpoint}", json=data, headers=headers, timeout=30.0)
        r.raise_for_status()
        return r.json()
    except RuntimeError:
        # Havuz arızası ("TÜM PROXY IP'LERİ DÜŞTÜ" vb.) RuntimeError ile gelir.
        # YUTMA — yutulursa her istek sessizce {} döner, cron 0 kayıtla biter ve
        # arıza log selinde kaybolur (geçmişte sessiz cron arızası yaşandı).
        # Gürültülü ölüm doğru: main() çöker, run_scraper.sh exit≠0 görür.
        raise
    except httpx.HTTPStatusError as e:
        print(f"    ✗ HTTP {e.response.status_code} — {endpoint}")
    except Exception as e:
        print(f"    ✗ {endpoint}: {e}")
    return {}


# ── KİK eşik tablosu ─────────────────────────────────────
MALIYET_TABLOSU = {
    64652:  (0,          10_785_492),
    129385: (10_785_492, 43_142_132),
    194085: (43_142_132, 323_566_103),
    258810: (323_566_103, None),
}

def itiraz_parse(s):
    if not s: return None
    try: return int(s.split(",")[0].replace(".", "").strip())
    except: return None

def maliyet_araligi(b):
    return MALIYET_TABLOSU.get(b, (None, None)) if b else (None, None)

# Yapım işi ilanlarında ilan metninin sonunda geçer. Gerçek formatlar (canlı veriden):
#   "...Sınır Değer Katsayısı (N) = 1,00" / "...Sınır Değer Katsayısı (N) : 1" / "(N) : 1,20"
# ÖNEMLİ: değer çoğu zaman ONDALIKSIZ tam sayı ("1") olarak yazılıyor — eski regex zorunlu
# ondalık (\d+[.,]\d+) istediği için bu ihalelerin ~2/3'ünü kaçırıyordu. Ondalık artık opsiyonel.
ESIK_KATSAYI_RE = re.compile(r"sınır\s*değer\s*katsayısı\s*\(?\s*n\s*\)?\s*[:=;]\s*(\d+(?:[.,]\d+)?)", re.IGNORECASE)

def esik_katsayi_parse(metin):
    if not metin: return None
    m = ESIK_KATSAYI_RE.search(metin)
    if not m: return None
    try: return float(m.group(1).replace(",", "."))
    except: return None


# ── HTML → yapılı metin ───────────────────────────────────
def html_temizle(html):
    if not html: return ""
    txt = re.sub(r"<br\s*/?>",                "\n",   html, flags=re.I)
    txt = re.sub(r"</p>|</div>|</h\d>|</tr>|<hr[^>]*>", "\n", txt, flags=re.I)
    txt = re.sub(r"<li[^>]*>",               "\n• ",  txt,  flags=re.I)
    txt = re.sub(r"</td>\s*<td[^>]*>",       " | ",   txt,  flags=re.I)
    txt = re.sub(r"<[^>]+>",                 "",      txt)
    txt = re.sub(r"&nbsp;",  " ", txt)
    txt = re.sub(r"&amp;",   "&", txt)
    txt = re.sub(r"&lt;",    "<", txt)
    txt = re.sub(r"&gt;",    ">", txt)
    txt = re.sub(r"&#?\w+;", " ", txt)
    txt = re.sub(r"[^\S\n]+", " ", txt)
    txt = re.sub(r" *\n *",   "\n", txt)
    txt = re.sub(r"\n{3,}",  "\n\n", txt)
    return txt.strip()


# ── Belge nesnesi normalleştirici ────────────────────────
def belge_isle(b: dict) -> dict:
    doc_id = b.get("id") or b.get("dokumanId") or b.get("belgId")
    ad = (
        b.get("dokumanAdi") or b.get("ad") or b.get("adi")
        or b.get("baslik") or b.get("fileName") or b.get("dosyaAdi") or ""
    ).strip() or None
    tur = (
        b.get("dokumanTuru") or b.get("tur") or b.get("turu")
        or b.get("type") or b.get("fileType") or b.get("dosyaTuru") or ""
    ).strip() or None
    url = (
        b.get("url") or b.get("downloadUrl")
        or (f"{BASE}/b_ihalearama/api/Dokuman/GetFile?id={doc_id}" if doc_id else None)
    )
    return {
        "id":    doc_id,
        "ad":    ad,
        "tur":   tur,
        "url":   url,
        "tarih": b.get("tarih") or b.get("olusturmaTarihi"),
    }


# ── İhale detayı çek ─────────────────────────────────────
async def detay_cek(client, ihale_id: str, dokuman_sayisi: int = 0) -> dict:
    # client: httpx.AsyncClient | AsyncProxyHavuzu — post() ikisini de kabul eder
    sonuc = {
        "itiraz_bedeli": None, "yaklasik_maliyet_min": None, "yaklasik_maliyet_max": None,
        "isin_yapilacagi_yer": None, "ihale_yeri": None, "okas": None,
        "ilan_metni": None, "ilan_html": None, "belgeler": None,
        "ilan_tarihi": None, "esik_katsayi": None, "kalemler": None,
    }

    # 1) İtiraz bedeli → yaklaşık maliyet
    veri = await post(client, ENDPOINTS["itiraz"], {"ihaleId": ihale_id})
    if veri:
        ib = itiraz_parse(veri.get("itirazenSikayetBedeli"))
        mn, mx = maliyet_araligi(ib)
        sonuc.update(itiraz_bedeli=ib, yaklasik_maliyet_min=mn, yaklasik_maliyet_max=mx)

    # 2) Detay bilgileri
    veri = await post(client, ENDPOINTS["detay"], {"ihaleId": ihale_id})
    if veri:
        item  = veri.get("item") or {}
        bilgi = item.get("ihaleBilgi") or {}
        sonuc["isin_yapilacagi_yer"] = (bilgi.get("isinYapilacagiYer") or "").strip() or None
        sonuc["ihale_yeri"]          = (bilgi.get("ihaleYeri") or "").strip() or None
        sonuc["okas"]                = (bilgi.get("okas") or "").strip() or None
        # Malzeme/kalem listesi (rakip "Malzeme Listesi (N)") — [{adi,kodu,koduAdi}].
        kl = item.get("ihtiyacKalemiOkasList")
        sonuc["kalemler"]            = kl if kl else None

        ilanlar = item.get("ilanList") or []
        if ilanlar:
            ilan0 = ilanlar[0]
            ham_html = ilan0.get("veriHtml") or ""
            sonuc["ilan_html"]  = ham_html or None
            sonuc["ilan_metni"] = html_temizle(ham_html) or None
            sonuc["esik_katsayi"] = esik_katsayi_parse(sonuc["ilan_metni"])
            # İlan yayım tarihi — field adı API'ye göre değişebilir
            tarih_ham = (
                ilan0.get("ilanTarihi") or ilan0.get("tarih")
                or ilan0.get("yayimTarihi") or ilan0.get("baslangicTarihi")
                or bilgi.get("ilanTarihi") or bilgi.get("yayimTarihi")
            )
            sonuc["ilan_tarihi"] = tarih_iso(tarih_ham)

        # Belgeler — önce item içinde
        raw = (
            item.get("dokumanListe") or item.get("belgeList")
            or veri.get("dokumanListe") or []
        )
        if raw:
            sonuc["belgeler"] = [belge_isle(b) for b in raw]

    # NOT: GetDokumanListByIhaleId endpoint'i artık 404 veriyor (kaldırıldı).
    # Belge bilgisi GetDokumanUrl linkinden (aşağıda) geliyor.

    # 3) EKAP indirme linki (hafif — dosya indirmez, CAPTCHA çözmez).
    #    Frontend bu linki "EKAP'ta Aç" olarak gösterir; kullanıcı CAPTCHA'yı kendi çözer.
    #    Ağır indirme (Gemini + Storage) ileride main()'de BELGE_INDIR ile ayrı yürür.
    if BELGE_LINK and dokuman_sayisi and not sonuc["belgeler"]:
        link = await dokuman_url_al(client, ihale_id, "1")
        if link:
            sonuc["belgeler"] = [{
                "id": "1",
                "tur": "İhale Dokümanı",
                "ad": "İhale Dokümanı",
                "url": link,            # frontend href: "EKAP'ta Aç"
                "storage_url": None,    # ileride indirilirse doldurulur
            }]

    return sonuc


# ── Doküman URL'si al (EkapDokumanYonlendirme) ───────────
async def dokuman_url_al(client, ihale_id: str, islem_id: str = "1") -> str | None:
    """GetDokumanUrl endpoint → belge indirme linki döndürür."""
    veri = await post(client, ENDPOINTS["dok_url"], {"islemId": islem_id, "ihaleId": ihale_id})
    return (veri or {}).get("url")


# ── İhale listesi çek ─────────────────────────────────────
async def sayfa_cek(client, skip: int = 0) -> dict:
    return await post(client, ENDPOINTS["liste"], {
        "searchText": "", "paginationSkip": skip, "paginationTake": SAYFA_BOYUTU,
        "ihaleDurumIdList": [2], "searchType": "GirdigimGibi",
    }) or {}

async def tum_ihaleleri_cek(client) -> list:
    print("\n  → Aktif ihaleler çekiliyor...")
    ilk    = await sayfa_cek(client, 0)
    toplam = ilk.get("totalCount", 0)
    liste  = ilk.get("list", [])
    print(f"  Toplam: {toplam} | İlk sayfa: {len(liste)}")

    sayfa = 1
    while len(liste) < toplam:
        await asyncio.sleep(0.3)
        sonuc = await sayfa_cek(client, sayfa * SAYFA_BOYUTU)
        yeni  = sonuc.get("list", [])
        if not yeni: break
        liste.extend(yeni)
        print(f"  Sayfa {sayfa+1}: {len(liste)}/{toplam}")
        sayfa += 1

    return liste


# ── Tüm detayları çek ─────────────────────────────────────
async def tum_detaylari_cek(client, ham_liste: list) -> dict:
    # main() zaten DETAY_LIMIT'e göre dilinmiş 'hedef'i geçirir; buradaki dilim
    # o durumda no-op olur ve başka bir çağıran tam liste verirse güvence sağlar.
    hedef = ham_liste if DETAY_LIMIT <= 0 else ham_liste[:DETAY_LIMIT]
    print(f"\n  → {len(hedef)} ihale için detay çekiliyor (eşzamanlı={ESZAMANLI})...")
    sem     = asyncio.Semaphore(ESZAMANLI)
    detaylar = {}
    sayac    = {"n": 0}

    async def gorev(ihale):
        ihale_id = ihale.get("id")
        if not ihale_id: return
        async with sem:
            detaylar[ihale_id] = await detay_cek(client, ihale_id, ihale.get("dokumanSayisi", 0))
            await asyncio.sleep(0.1)
            sayac["n"] += 1
            if sayac["n"] % 50 == 0:
                print(f"    {sayac['n']}/{len(hedef)} tamam")

    await asyncio.gather(*(gorev(i) for i in hedef))
    print(f"  ✓ {len(detaylar)} detay çekildi")
    return detaylar


# ── Belge indirme + Supabase Storage ──────────────────────
_TR_ASCII = str.maketrans({
    "ç": "c", "Ç": "C", "ğ": "g", "Ğ": "G", "ı": "i", "İ": "I",
    "ö": "o", "Ö": "O", "ş": "s", "Ş": "S", "ü": "u", "Ü": "U",
})

def dosya_adi_temizle(s):
    # Supabase Storage anahtarı ASCII olmalı: Türkçe harfleri çevir, kalanı _ yap
    s = (s or "belge").translate(_TR_ASCII)
    return re.sub(r"[^A-Za-z0-9\-.]", "_", s)[:80]

async def belge_indir_yukle(client, ekap_id: str, ihale_id: str, sb) -> list:
    """
    1. GetDokumanUrl ile EKAP yönlendirme URL'sini al
    2. Eski EKAP VatandasIlanGoruntuleme.aspx CAPTCHA'sını Gemini ile çöz
    3. Dosya içeriğini indir
    4. Supabase Storage'a yükle
    Returns: güncellenmiş belgeler listesi

    client: httpx.AsyncClient | AsyncProxyHavuzu.
    NOT: CAPTCHA akışı (ekap_captcha_indir) BİLEREK havuzdan geçmez — 3 adımlı
    ViewState/çerez oturumu tek bağlantıya bağlı; adımlar farklı IP'lerden
    giderse eski EKAP oturumu tanımaz.
    """
    havuz_mu = hasattr(client, "istek")
    TUR_ADLARI = {
        "1": "İhale Dokümanı",
        "2": "İdari Şartname",
        "3": "Teknik Şartname",
        "4": "Sözleşme Tasarısı",
    }
    belgeler = []

    gorulen: dict = {}  # içerik hash → {"ad", "url"} — aynı dosyayı iki kez yüklemeyi önler

    # İslemId 1-4: farklı doküman türleri
    for islem_id in ["1", "2", "3", "4"]:
        ekap_url = await dokuman_url_al(client, ihale_id, islem_id)
        if not ekap_url:
            continue

        tur_ad = TUR_ADLARI.get(islem_id, f"Doküman {islem_id}")

        # VatandasIlanGoruntuleme.aspx → CAPTCHA akışı
        if "VatandasIlanGoruntuleme" in ekap_url:
            icerik = await ekap_captcha_indir(ekap_url)
        else:
            # Direkt indirilebilir URL (nadiren)
            try:
                if havuz_mu:
                    async with client.istek() as ist:
                        r = await ist.client.get(ekap_url, timeout=60.0, follow_redirects=True)
                        ist.yanit(r)
                else:
                    r = await client.get(ekap_url, timeout=60.0, follow_redirects=True)
                icerik = r.content if r.is_success and len(r.content) > 200 else None
            except RuntimeError:
                raise  # havuz arızası — sessizce belge atlamak yerine gürültüyle dur
            except Exception as e:
                print(f"      ✗ Direkt GET hatası: {e}")
                icerik = None

        if not icerik or len(icerik) < 200:
            continue

        # Aynı içerik daha önce yüklendiyse tekrar yükleme, mevcut URL'i paylaş
        icerik_hash = hashlib.md5(icerik).hexdigest()
        if icerik_hash in gorulen:
            onceki = gorulen[icerik_hash]
            belgeler.append({
                "id": islem_id, "ad": onceki["ad"], "tur": tur_ad,
                "url": ekap_url, "storage_url": onceki["url"],
            })
            print(f"      ↺ {tur_ad} — aynı içerik ({onceki['ad']}), tekrar yüklenmedi")
            await asyncio.sleep(1)
            continue

        # Dosya uzantısını belirle
        if icerik[:4] == b"PK\x03\x04":
            uzanti, ct = ".zip", "application/zip"
        elif icerik[:4] == b"%PDF":
            uzanti, ct = ".pdf", "application/pdf"
        else:
            uzanti, ct = ".bin", "application/octet-stream"

        dosya_adi = f"{islem_id}_{dosya_adi_temizle(tur_ad)}{uzanti}"
        path = f"{ekap_id}/{dosya_adi}"

        try:
            sb.storage.from_(STORAGE_BUCKET).upload(
                path, icerik,
                file_options={"content-type": ct, "upsert": "true"},
            )
            storage_url = sb.storage.from_(STORAGE_BUCKET).get_public_url(path)
            belgeler.append({
                "id":          islem_id,
                "ad":          dosya_adi,
                "tur":         tur_ad,
                "url":         ekap_url,
                "storage_url": storage_url,
            })
            gorulen[icerik_hash] = {"ad": dosya_adi, "url": storage_url}
            print(f"      ✓ {tur_ad} — {len(icerik)//1024}KB → Storage")
        except Exception as e:
            print(f"      ✗ Storage yükleme hatası ({tur_ad}): {e}")

        await asyncio.sleep(1)  # EKAP rate limit

    return belgeler


# ── Veri dönüşümü ─────────────────────────────────────────
def tur_donustur(tip):
    tip = (tip or "").strip()
    for k, v in [("Mal", "Mal"), ("Hizmet", "Hizmet"), ("Yapım", "Yapım"),
                 ("Danışmanlık", "Danışmanlık"), ("Kiralama", "Kiralama")]:
        if k.lower() in tip.lower(): return v
    return tip or "Diğer"

# Eşleşmeyen EKAP durum metinleri — eşlemeyi KANITLA tamamlamak için sayılıyor.
# (Tahminle genişletmek yanlış: hangi metinlerin geldiğini bilmiyoruz.)
BILINMEYEN_DURUMLAR = {}


def durum_donustur(d, son_teklif_iso=None):
    """EKAP durum metnini kanonik duruma çevirir.

    ⚠️ 20 Tem 2026 — BLANKET `return "aktif"` KALDIRILDI.
    Eski hâlinde eşleşmeyen HER durum "aktif" oluyordu. ekap_ihale_backfill.py
    bunu 1,6M geçmiş ihalede çağırınca canlıda 163.464 kayıt "aktif" göründü
    (gerçekte açık olan 4.856) — idareler dizinindeki "aktif" sütunu ve
    kurum_ozet durum kırılımı şişti.

    `son_teklif_iso` verilirse TANINMAYAN durumda tarihe bakılır. Bu, körlemesine
    "kapandi" yazmaktan güvenli: canlı scraper da aynı fonksiyonu kullanıyor ve
    tanınmayan bir metin yüzünden GERÇEK aktif ihaleyi gizlemek, ters yönde ama
    daha sinsi bir hata olurdu. Tarih varsa gerçeği tarih söyler.
    """
    ham = (d or "").strip()
    dl = ham.lower()
    if "açık" in dl or "devam" in dl or "katılım" in dl:
        return "aktif"
    if "sonuçland" in dl or "tamamland" in dl:
        return "sonuclandi"

    BILINMEYEN_DURUMLAR[ham] = BILINMEYEN_DURUMLAR.get(ham, 0) + 1

    if son_teklif_iso:
        try:
            t = datetime.fromisoformat(str(son_teklif_iso).replace("Z", "+00:00"))
            if t.tzinfo is None:
                t = t.replace(tzinfo=timezone.utc)
            # 'kapali' — 'kapandi' DEĞİL. ilanlar_durum_check yalnız
            # ('taslak','aktif','kapali','iptal','sonuclandi') kabul ediyor;
            # 'kapandi' yazınca PostgREST 400 döndürüp backfill'i çökertti (20 Tem).
            # migration_uygun_firmalar_v3_1.sql 'kapandi' diyor ama v3_3 onu
            # düzeltmiş — canlı fonksiyon 'kapali' yazıyor. v3_1 BAYAT, okumayın.
            return "aktif" if t > datetime.now(timezone.utc) else "kapali"
        except (ValueError, TypeError):
            pass
    # Tarih de yoksa eski davranış korunur (canlıda böyle yalnız 2 kayıt var).
    return "aktif"


def bilinmeyen_durum_raporu():
    """Eşleşmeyen durum metinlerini sıklığa göre yazdırır — eşlemeyi bu çıktıya
    bakarak tamamlayacağız. Tur sonunda çağrılır."""
    if not BILINMEYEN_DURUMLAR:
        return
    # ASCII başlık bilinçli: Windows konsolu (cp1254) emoji'de UnicodeEncodeError
    # veriyor ve bu, raporun tamamını kaybettiriyor.
    print(f"\n[!] ESLESMEYEN DURUM METINLERI ({len(BILINMEYEN_DURUMLAR)} farkli):", flush=True)
    for metin, adet in sorted(BILINMEYEN_DURUMLAR.items(), key=lambda x: -x[1])[:25]:
        print(f"     {adet:>8,}  {metin!r}", flush=True)
    print("   -> Bunlar tarihten turetildi. durum_donustur() eslemesi bu listeye"
          " bakilarak tamamlanmali.", flush=True)

# CPV/OKAS kodunun ilk 2 hanesi → ana kategori
# Yeni iş-dostu kategori sınıflandırıcı (ihaleciler.com tarzı, OKAS açıklaması + başlık keyword).
# Eski _CPV_KATEGORI/kategori_tur artık kullanılmıyor ama fallback referansı için tutuluyor.
from kategori_siniflandir import kategori_belirle

_CPV_KATEGORI = {
    "03": "Tarım & Ormancılık", "09": "Enerji", "14": "Madencilik",
    "15": "Gıda & İçecek", "16": "Tarım Makineleri", "18": "Giyim & Tekstil",
    "19": "Deri & Kauçuk", "22": "Basın & Yayın", "24": "Kimyasal Ürünler",
    "30": "BT Ekipmanları", "31": "Elektrik Malzemeleri", "32": "İletişim",
    "33": "Tıbbi Cihazlar", "34": "Ulaşım Araçları", "35": "Güvenlik",
    "37": "Spor & Eğlence", "38": "Laboratuvar", "39": "Mobilya & Temizlik",
    "41": "Su", "42": "Sanayi Makineleri", "43": "Madencilik Ekipmanı",
    "44": "İnşaat Malzemeleri", "45": "İnşaat & Yapım", "48": "Yazılım",
    "50": "Bakım & Onarım", "51": "Montaj", "55": "Konaklama & Yemek",
    "60": "Ulaşım Hizmetleri", "63": "Lojistik", "64": "Posta & İletişim",
    "65": "Kamu Hizmetleri", "66": "Sigorta & Finans", "70": "Gayrimenkul",
    "71": "Mimarlık & Mühendislik", "72": "Bilişim Hizmetleri",
    "73": "Ar-Ge", "75": "Kamu Yönetimi", "76": "Petrol & Gaz",
    "77": "Bahçe & Çevre", "79": "İdari Hizmetler", "80": "Eğitim",
    "85": "Sağlık", "90": "Çevre Hizmetleri", "92": "Kültür & Medya",
    "98": "Diğer Hizmetler",
}

def kategori_tur(okas: str | None, tur: str | None, baslik: str | None) -> str | None:
    """OKAS/CPV kodundan kategori türet; yoksa ihale türünden fallback."""
    if okas:
        prefix = "".join(filter(str.isdigit, okas))[:2]
        if prefix in _CPV_KATEGORI:
            return _CPV_KATEGORI[prefix]
    # OKAS yoksa ihale türünden genel kategori
    t = (tur or "").lower()
    if "yapım" in t:        return "İnşaat & Yapım"
    if "bilgi" in t or "yazılım" in t: return "Bilişim Hizmetleri"
    if "mal" in t:          return "Mal Alımı"
    if "hizmet" in t:       return "Hizmet Alımı"
    if "danışmanlık" in t:  return "Danışmanlık"
    return None

# EKAP ham enum → okunabilir Türkçe (ham: "TENDER_SEARCH.ENUMERATIONS.OPEN" vb.)
_USUL_HARITA = [
    ("OPEN",                   "Açık İhale"),
    ("AMONG_CERTAIN_BIDDERS",  "Belli İstekliler Arasında"),
    ("BARGAIN",                "Pazarlık Usulü"),
    ("DESIGN_COMPETITION",     "Tasarım Yarışması"),
    ("DIRECT_PROCUREMENT",     "Doğrudan Temin"),
    ("FRAMEWORK_AGREEMENT",    "Çerçeve Anlaşma"),
    ("DIGER",                  "Diğer / İstisna"),
]

# 4734 sayılı Kanun md.3 istisna bentleri (3-b, 3-g, 3-i…). Ham API bazen çeviri
# anahtarı + madde referansını birlikte döndürüyor: "...TENDER_TYPE 4734 / 3-g".
_MADDE_RE = re.compile(r"4734\s*/\s*(3\s*-\s*[a-zçğıöşü])", re.IGNORECASE)

def usul_donustur(s):
    s = (s or "").strip()
    if not s:
        return None
    s_upper = s.upper()
    for frag, label in _USUL_HARITA:
        if frag in s_upper:
            return label
    # "4734 / 3-g" gibi istisna madde referansı — anlamlı, oku­nabilir hale getir
    m = _MADDE_RE.search(s)
    if m:
        return "İstisna (4734 md. " + re.sub(r"\s+", "", m.group(1)).lower() + ")"
    # Ham i18n anahtarı kalmışsa (TENDER_SEARCH/PAGEITEM/ENUMERATIONS) → kullanıcıya çöp
    # gösterme, "Diğer / İstisna" ver.
    if any(k in s_upper for k in ("TENDER_SEARCH", "PAGEITEM", "ENUMERATIONS")):
        return "Diğer / İstisna"
    # Zaten okunabilir metin (örn. "Açık İhale Usulü" → "Açık İhale Usulü")
    return s.replace("İhale Usulü:", "").strip() or None

def mojibake_duzelt(s: str | None) -> str | None:
    """UTF-8 metin yanlışlıkla Latin-1 olarak decode edilmişse onarır (Türkçe karakter bozulması)."""
    if not s:
        return s
    try:
        fixed = s.encode("latin-1").decode("utf-8")
        # Yalnızca gerçekten Türkçe harf içeriyorsa uygula (fazla agresif olmasın)
        if any(c in fixed for c in "çğıöşüÇĞİÖŞÜ"):
            return fixed
    except (UnicodeEncodeError, UnicodeDecodeError):
        pass
    return s

def tarih_iso(s):
    """EKAP tarihini ISO'ya çevirir. 'GG.AA.YYYY SS:DD' → ISO; zaten ISO ise dokunmaz."""
    if not s:
        return None
    s = str(s).strip()
    if not s:
        return None
    m = re.match(r"^(\d{1,2})\.(\d{1,2})\.(\d{4})(?:[ T](\d{1,2}):(\d{2}))?", s)
    if m:
        g, a, y, sa, dk = m.groups()
        return f"{y}-{int(a):02d}-{int(g):02d}T{int(sa or 0):02d}:{dk or '00'}:00"
    return s  # zaten ISO veya bilinmeyen format — olduğu gibi bırak

def ihaleleri_isle(ham_liste: list, detaylar: dict) -> list:
    now = datetime.now(timezone.utc).isoformat()
    kayitlar = []
    _debug_done = False
    for i in ham_liste:
        if not i.get("ihaleAdi"): continue
        d = detaylar.get(i.get("id"), {})
        if not _debug_done:
            print(f"  [DEBUG-LIST-KEYS] {list(i.keys())}")
            if d:
                print(f"  [DEBUG-DETAY-KEYS] ilanList[0] fields araştır — ilan_tarihi={d.get('ilan_tarihi')}")
            _debug_done = True
        kayitlar.append({
            "ekap_id":              str(i.get("ikn") or i.get("id") or ""),
            "ikn":                  str(i.get("ikn") or ""),
            "baslik":               mojibake_duzelt((i.get("ihaleAdi") or "").strip()),
            "idare":                mojibake_duzelt((i.get("idareAdi") or "").strip()),
            "il":                   mojibake_duzelt((i.get("ihaleIlAdi") or "").strip()),
            "tur":                  tur_donustur(i.get("ihaleTipAciklama")),
            "usul":                 usul_donustur(i.get("ihaleUsulAciklama")),
            # tarih 2. argüman olarak veriliyor: EKAP'ın tanımadığımız bir durum
            # metni gelirse "aktif" varsaymak yerine tarihten türetilsin.
            "durum":                durum_donustur(i.get("ihaleDurumAciklama"),
                                                   tarih_iso(i.get("ihaleTarihSaat"))),
            "son_teklif_tarihi":    tarih_iso(i.get("ihaleTarihSaat")),
            "ilan_tarihi":          d.get("ilan_tarihi") or tarih_iso(
                                        i.get("ilanTarihi") or i.get("yayimTarihi")
                                        or i.get("ilkIlanTarihi") or i.get("ilanBaslangicTarihi")
                                    ),
            "itiraz_bedeli":        d.get("itiraz_bedeli"),
            "yaklasik_maliyet_min": d.get("yaklasik_maliyet_min"),
            "yaklasik_maliyet_max": d.get("yaklasik_maliyet_max"),
            "tahmini_bedel":        d.get("yaklasik_maliyet_min"),
            "isin_yapilacagi_yer":  d.get("isin_yapilacagi_yer"),
            "ihale_yeri":           d.get("ihale_yeri"),
            "okas":                 d.get("okas"),
            "kategori":             kategori_belirle(d.get("okas"), tur_donustur(i.get("ihaleTipAciklama")),
                                        (i.get("ihaleAdi") or "").strip()),
            "ilan_metni":           d.get("ilan_metni"),
            "ilan_html":            d.get("ilan_html"),
            "esik_katsayi":         d.get("esik_katsayi"),
            "belgeler":             d.get("belgeler"),
            "kalemler":             d.get("kalemler"),   # malzeme/kalem listesi (ihtiyacKalemiOkasList)
            "kaynak":               "ekap",
            "olusturulma":          now,
        })
    return kayitlar

def tekilleştir(liste):
    goruldu, tekil = set(), []
    for i in liste:
        k = i.get("ikn") or i.get("ekap_id")
        if k and k not in goruldu:
            goruldu.add(k)
            tekil.append(i)
    return tekil


# ── Supabase yaz ──────────────────────────────────────────
def supabase_yaz(liste, sb=None):
    if not SUPABASE_KEY:
        dosya = f"ekap_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(dosya, "w", encoding="utf-8") as f:
            json.dump(liste, f, ensure_ascii=False, indent=2)
        print(f"  💾 {len(liste)} ihale → '{dosya}'")
        return
    if not sb:
        sb = create_client(SUPABASE_URL, SUPABASE_KEY)
    toplam = 0
    for i in range(0, len(liste), 50):
        batch = liste[i:i+50]
        try:
            # 1. Yeni kayıtları olusturulma dahil insert et (çakışırsa atla)
            sb.table("ilanlar").upsert(batch, on_conflict="ekap_id", ignore_duplicates=True).execute()
            # 2. Mevcut kayıtları olusturulma'ya dokunmadan güncelle
            update_batch = [{k: v for k, v in r.items() if k != "olusturulma"} for r in batch]
            sb.table("ilanlar").upsert(update_batch, on_conflict="ekap_id").execute()
            toplam += len(batch)
            print(f"  ✓ {toplam}/{len(liste)} yazıldı")
        except Exception as e:
            print(f"  ✗ Yazma hatası: {e}")
    print(f"\n✅ {toplam} ihale Supabase'e aktarıldı")


def storage_hazirla(sb):
    try:
        isimler = [b.name for b in sb.storage.list_buckets()]
        if STORAGE_BUCKET not in isimler:
            sb.storage.create_bucket(STORAGE_BUCKET, options={"public": True, "file_size_limit": 52428800})
            print(f"  ✓ Bucket '{STORAGE_BUCKET}' oluşturuldu")
    except Exception as e:
        print(f"  ⚠ Storage hazırlık: {e}")


def ozet(liste):
    print("\n" + "=" * 55)
    belgeli  = sum(1 for i in liste if i.get("belgeler"))
    metinli  = sum(1 for i in liste if i.get("ilan_metni"))
    maliyetli = sum(1 for i in liste if i.get("itiraz_bedeli"))
    print(f"Toplam: {len(liste)} | Belgeli: {belgeli} | İlan metinli: {metinli} | Maliyetli: {maliyetli}")
    if liste:
        o = liste[0]
        print(f"Örnek: {o['baslik'][:60]}")
        print(f"  IKN: {o['ikn']} | Maliyet: {o['yaklasik_maliyet_min']} – {o['yaklasik_maliyet_max']}")
    print("=" * 55)


# ── ANA ───────────────────────────────────────────────────
async def main():
    print("=" * 55)
    print("EKAP SCRAPER v2 — httpx / Playwrightsiz")
    print(f"Zaman: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}")
    print(f"Belge indirme: {'EVET' if BELGE_INDIR else 'HAYIR'}")
    print(f"Proxy havuzu: {'AKTİF' if HAVUZ_AKTIF else 'KAPALI (EKAP_HAVUZ=0)'} | Eşzamanlı: {ESZAMANLI}")
    print("=" * 55)

    sb = create_client(SUPABASE_URL, SUPABASE_KEY) if SUPABASE_KEY else None
    if sb and BELGE_INDIR:
        storage_hazirla(sb)

    # Bağlantı seçimi:
    #   VARSAYILAN → proxy havuzu (istek başına IP rotasyonu + soğuma + küresel
    #                tavan + karantina; PROXY_LIST boşsa havuz kendi "direkt
    #                mod"una düşer — davranış yine eskiyle eşdeğer).
    #   EKAP_HAVUZ=0 → eski tek AsyncClient (kaçış kapısı; run_scraper.sh'e
    #                dokunmadan .env ile geri dönüş).
    # Import BİLEREK burada: EKAP_HAVUZ=0 iken proxy_havuz hiç yüklenmez, yani
    # kaçış kapısı havuz modülündeki olası bir hatadan bile etkilenmez. Ayrıca
    # worker.py bu modülü import ediyor — top-level import onu da havuza bağlardı.
    if HAVUZ_AKTIF:
        from proxy_havuz import async_havuz_al, ekap_ssl_baglami
        client = async_havuz_al(ssl_baglami=ekap_ssl_baglami())
    else:
        print("⚠ EKAP_HAVUZ=0 — proxy havuzu devre dışı, tüm istekler tek bağlantıdan (VDS IP).")
        client = httpx.AsyncClient(verify=ssl_ctx(), http2=False, timeout=30.0)

    try:
        # 1) Liste
        ham_liste = await tum_ihaleleri_cek(client)

        # DETAY_LIMIT boru hattının TAMAMINI sınırlar: detay + belge + işleme/yazma
        # aşamalarının üçü de aynı 'hedef' diliminden gider. İşleme/yazma da dahil,
        # ÇÜNKÜ detay çekilmeyen satır d={} ile işlenirse supabase_yaz'ın 2. upsert'i
        # (on_conflict=ekap_id) mevcut kaydın itiraz_bedeli / yaklasik_maliyet_min-max /
        # ilan_metni / ilan_html / belgeler / okas / isin_yapilacagi_yer kolonlarını
        # NULL ile ezer — limitli bir test turu binlerce aktif ihalenin detayını
        # gece cron'u tam turla onarana dek silerdi.
        hedef = ham_liste if DETAY_LIMIT <= 0 else ham_liste[:DETAY_LIMIT]
        if DETAY_LIMIT > 0:
            print(f"  ⚠ EKAP_DETAY_LIMIT={DETAY_LIMIT} — {len(ham_liste)} kayıtlık liste "
                  f"{len(hedef)} kayda daraltıldı (detay+belge+YAZMA bu dilimle sınırlı)")

        # 2) Detaylar
        detaylar = await tum_detaylari_cek(client, hedef)

        # 3) Belge indirme
        if BELGE_INDIR and sb:
            # DETAY_LIMIT belge indirmeyi de sınırlar (test + güvenli ilk tur için);
            # dilim yukarıda TEK yerde hesaplanan 'hedef' — aşamalar birbirinden kopamaz.
            print(f"\n  → Belgeler indiriliyor ({len(hedef)} ihale)...")
            id_to_ekap = {i.get("id"): str(i.get("ikn") or i.get("id") or "") for i in hedef}
            for ihale in hedef:
                ihale_id = ihale.get("id")
                if not ihale_id: continue
                ekap_id = id_to_ekap.get(ihale_id, ihale_id)
                mevcut_belgeler = (detaylar.get(ihale_id) or {}).get("belgeler") or []
                yeni_belgeler = await belge_indir_yukle(client, ekap_id, ihale_id, sb)
                if yeni_belgeler:
                    # storage URL'lerini mevcut belgelere ekle, yoksa yeni listeyi kullan
                    if mevcut_belgeler:
                        for nb in yeni_belgeler:
                            existing = next((b for b in mevcut_belgeler if b.get("tur") == nb.get("tur")), None)
                            if existing:
                                existing["storage_url"] = nb["storage_url"]
                            else:
                                mevcut_belgeler.append(nb)
                    else:
                        if ihale_id not in detaylar:
                            detaylar[ihale_id] = {}
                        detaylar[ihale_id]["belgeler"] = yeni_belgeler
    finally:
        # Havuz arızasıyla çökerken bile özet basılsın — teşhis için son görüntü.
        if HAVUZ_AKTIF:
            client.ozet_yaz()
            await client.kapat()
        else:
            await client.aclose()

    # 4) Dönüştür ve yaz — YALNIZ detay çekilen 'hedef' dilimi (ham_liste DEĞİL):
    # limitli turda detaysız satırlar hiç işlenmez, mevcut kayıtlar ezilmez.
    tum = tekilleştir(ihaleleri_isle(hedef, detaylar))
    print(f"\n✓ {len(tum)} tekil ihale")
    if tum:
        ozet(tum)
        supabase_yaz(tum, sb)
    else:
        # Sessiz başarısızlık cron'da 0 kayıtla exit 0 görünüyordu (bayat veriyle notify/bulten çalışıyordu).
        print("❌ Veri çekilemedi (0 kayıt) — cron bunu HATA saymalı.")
        return False
    return True


if __name__ == "__main__":
    # Windows konsolunda (cp1254) Unicode karakterler çökmesin
    try:
        import sys
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass
    import sys as _sys
    _ok = asyncio.run(main())
    _sys.exit(0 if _ok else 1)
