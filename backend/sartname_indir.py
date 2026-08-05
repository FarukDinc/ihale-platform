# -*- coding: utf-8 -*-
"""
sartname_indir.py — UV-1 Faz 2: EKAP teknik şartname (+ birim fiyat cetveli) İNDİR + PARSE.

NEDEN Playwright: EKAP belge indirme 406'ya sertleşti (düz httpx 3-adımlı CAPTCHA postback'i
Accept/buton/name=value denemelerinin HEPSİ 406; bkz. hafıza ekap-belge-indirme-captcha). GERÇEK
tarayıcı (Playwright + chromium, VDS'te kurulu) akışı JS/oturumuyla yürütünce dosya iner (spike ile
kanıtlandı: 418KB ZIP, içinde ÖZEL_TEKNİK_ŞARTNAME.pdf 13 sayfa/47.978 char). CAPTCHA Gemini ile çözülür.

AKIŞ (indir_parse):
  1. dokuman_url_al (islemId 1=İhale Dokümanı ZIP; 3=Teknik Şartname) → VatandasIlanGoruntuleme URL
  2. Playwright: sayfaya git → capImg (data:) → Gemini çöz → txtCaptcha doldur → __doPostBack
     btnCaptchaProtect → onay → btnTmpNormal postback → indirme yakala (page.expect_download)
  3. ZIP'i (iç içe) aç → PDF'leri pdfplumber ile, .docx'leri XML'den metne çevir → BİRLEŞİK metin
  4. Metni döndür (çağıran ilanlar.sartname_metni'ye cache'ler; kredi çağıranda düşülür)

⚠️ YAVAŞ (~20-35 sn: chromium başlat + CAPTCHA + indirme). KREDİLİ on-demand kullanılır, batch DEĞİL.
Env: SUPABASE + GEMINI (ekap_scraper/ai_ortak okur). Playwright 1.61 + chromium-1228 VDS'te kurulu.
"""
import asyncio
import base64
import io
import os
import re
import sys
import zipfile

sys.path.insert(0, os.path.dirname(__file__))
import ekap_scraper as E  # sayfa/dokuman_url_al, captcha_coz_gemini, old_ekap_ssl

_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
       "(KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36")
AZAMI_METIN = 24000   # AI'a giden birleşik metin tavanı (DeepSeek bağlamı bol ama gereksiz token yeme)


def _docx_metin(ham: bytes) -> str:
    """python-docx olmadan .docx'ten metin: docx = zip; word/document.xml <w:t> etiketleri."""
    try:
        z = zipfile.ZipFile(io.BytesIO(ham))
        xml = z.read("word/document.xml").decode("utf-8", "ignore")
    except Exception:
        return ""
    # paragraf/satır sonlarını koru, sonra <w:t> içeriklerini birleştir
    xml = xml.replace("</w:p>", "\n").replace("<w:tab/>", "\t")
    parcalar = re.findall(r"<w:t[^>]*>(.*?)</w:t>", xml, re.DOTALL)
    import html as _html
    return _html.unescape(re.sub(r"[ \t]+", " ", "".join(parcalar))).strip()


def _pdf_metin(ham: bytes) -> str:
    """PDF'ten metin (pdfplumber; taranmış/boş ise '' döner — o zaman AI'a gitmez)."""
    try:
        import pdfplumber
        with pdfplumber.open(io.BytesIO(ham)) as p:
            return "".join((pg.extract_text() or "") for pg in p.pages)
    except Exception:
        return ""


def _zip_metinlerini_topla(ham: bytes, derinlik: int = 0) -> dict:
    """ZIP'i (iç içe, en çok 2 seviye) aç; {dosya_adi: metin} — PDF + docx. Boş/parse edilemez atlanır."""
    sonuc = {}
    try:
        z = zipfile.ZipFile(io.BytesIO(ham))
    except Exception:
        return sonuc
    for ad in z.namelist():
        if ad.endswith("/"):
            continue
        alt = ad.lower()
        try:
            icerik = z.read(ad)
        except Exception:
            continue
        if alt.endswith(".zip") and derinlik < 2:
            sonuc.update(_zip_metinlerini_topla(icerik, derinlik + 1))
        elif alt.endswith(".pdf"):
            m = _pdf_metin(icerik)
            if m and len(m) > 40:
                sonuc[ad] = m
        elif alt.endswith(".docx"):
            m = _docx_metin(icerik)
            if m and len(m) > 40:
                sonuc[ad] = m
        # .doc (eski ikili Word) atlanır — antiword/LibreOffice gerekir; teknik şartname genelde PDF.
    return sonuc


async def _playwright_indir(url: str, deneme: int = 3) -> bytes | None:
    """Playwright ile CAPTCHA'lı belge indirme akışı → dosya byte'ları (spike ile kanıtlandı)."""
    from playwright.async_api import async_playwright
    async with async_playwright() as pw:
        br = await pw.chromium.launch(headless=True, args=["--ignore-certificate-errors", "--no-sandbox"])
        try:
            ctx = await br.new_context(accept_downloads=True, ignore_https_errors=True, user_agent=_UA)
            page = await ctx.new_page()
            for d in range(deneme):
                await page.goto(url, wait_until="domcontentloaded", timeout=60000)
                await page.wait_for_timeout(1500)
                src = await page.evaluate(
                    "() => { const im=[...document.querySelectorAll('img')]"
                    ".find(x=>(x.src||'').startsWith('data:image')); return im?im.src:null; }")
                if not src:
                    return None  # CAPTCHA sayfası değil (dosya yok / hata)
                img = base64.b64decode(src.split(",", 1)[1])
                cevap = await asyncio.get_event_loop().run_in_executor(None, E.captcha_coz_gemini, img)
                if not cevap:
                    continue
                await page.fill("input[name='ctl00$capEkapMaster$txtCaptcha']", cevap)
                await page.evaluate("__doPostBack('ctl00$btnCaptchaProtect','')")
                await page.wait_for_load_state("domcontentloaded")
                await page.wait_for_timeout(2000)
                govde = (await page.content()).lower()
                if "başarıyla indir" not in govde and "basariyla indir" not in govde:
                    continue  # CAPTCHA yanlış → yeni tur (taze CAPTCHA)
                try:
                    async with page.expect_download(timeout=35000) as dl_info:
                        await page.evaluate(
                            "__doPostBack('ctl00$ContentPlaceHolder1$UcIhaleDokumanDownload1$btnTmpNormal','')")
                    dl = await dl_info.value
                    yol = await dl.path()
                    with open(yol, "rb") as f:
                        return f.read()
                except Exception:
                    continue
            return None
        finally:
            await br.close()


async def dokuman_indir_ham(ihale_id: str) -> dict:
    """HAM doküman dosyasını indirir (parse ETMEDEN) — kullanıcıya servis için (ihalepro tarzı
    'Doküman İndir'). indir_parse ile aynı EKAP CAPTCHA akışı (_playwright_indir), ama metne
    çevirmez; ham byte + uzantı döner. Döner: {basari, bytes|None, uzanti('zip'|'pdf'|'bin'), hata}."""
    import httpx
    url = None
    try:
        async with httpx.AsyncClient(verify=E.old_ekap_ssl(), timeout=40) as api:
            for islem in ("1", "3"):   # 1=İhale Dokümanı ZIP (cetvel+şartname), 3=Teknik Şartname
                u = await E.dokuman_url_al(api, str(ihale_id), islem)
                if u and "VatandasIlan" in u:
                    url = u
                    break
    except Exception as e:
        return {"basari": False, "bytes": None, "uzanti": None, "hata": f"doküman URL alınamadı: {str(e)[:120]}"}
    if not url:
        return {"basari": False, "bytes": None, "uzanti": None, "hata": "Bu ihalede indirilebilir doküman yok"}
    ham = await _playwright_indir(url)
    if not ham or len(ham) < 200:
        return {"basari": False, "bytes": None, "uzanti": None, "hata": "Belge indirilemedi (CAPTCHA/EKAP)"}
    uz = "zip" if ham[:4] == b"PK\x03\x04" else ("pdf" if ham[:4] == b"%PDF" else "bin")
    return {"basari": True, "bytes": ham, "uzanti": uz, "hata": None}


async def indir_parse(ihale_id: str) -> dict:
    """Bir ihalenin teknik şartname + birim fiyat cetvelini indirir ve metne çevirir.
    Döner: {"basari", "metin"(birleşik, AZAMI_METIN kırpık)|None, "dosyalar"[ad], "hata"}."""
    import httpx
    url = None
    try:
        async with httpx.AsyncClient(verify=E.old_ekap_ssl(), timeout=40) as api:
            for islem in ("1", "3"):   # 1=İhale Dokümanı (ZIP, cetvel+şartname), 3=Teknik Şartname
                u = await E.dokuman_url_al(api, str(ihale_id), islem)
                if u and "VatandasIlan" in u:
                    url = u
                    break
    except Exception as e:
        return {"basari": False, "metin": None, "dosyalar": [], "hata": f"doküman URL alınamadı: {str(e)[:120]}"}
    if not url:
        return {"basari": False, "metin": None, "dosyalar": [], "hata": "Bu ihalede indirilebilir doküman yok"}

    ham = await _playwright_indir(url)
    if not ham or len(ham) < 200:
        return {"basari": False, "metin": None, "dosyalar": [], "hata": "Belge indirilemedi (CAPTCHA/EKAP)"}

    # ZIP mi tek dosya mı
    metinler = {}
    if ham[:4] == b"PK\x03\x04":
        metinler = _zip_metinlerini_topla(ham)
    elif ham[:4] == b"%PDF":
        m = _pdf_metin(ham)
        if m:
            metinler["belge.pdf"] = m
    if not metinler:
        return {"basari": False, "metin": None, "dosyalar": [],
                "hata": "Belge indi ama metin çıkarılamadı (taranmış/boş olabilir)"}

    # Teknik şartname + cetvel öne; birleşik metin
    def _oncelik(ad):
        a = ad.lower()
        if "teknik" in a or "şartname" in a or "sartname" in a:
            return 0
        if "cetvel" in a or "birim" in a:
            return 1
        return 2
    sirali = sorted(metinler.items(), key=lambda kv: _oncelik(kv[0]))
    parcalar = [f"=== {ad} ===\n{metin}" for ad, metin in sirali]
    birlesik = "\n\n".join(parcalar)[:AZAMI_METIN]
    return {"basari": True, "metin": birlesik, "dosyalar": list(metinler.keys()), "hata": None}


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--ihale-id", required=True)
    a = ap.parse_args()
    r = asyncio.run(indir_parse(a.ihale_id))
    print("basari:", r["basari"], "| dosyalar:", r["dosyalar"], "| hata:", r["hata"])
    if r["metin"]:
        print("metin uzunluk:", len(r["metin"]))
        print(r["metin"][:600])
