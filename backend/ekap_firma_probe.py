# -*- coding: utf-8 -*-
"""
EKAP firma-veri PROBE (tek seferlik keşif — DB'ye DOKUNMAZ).

Amaç: ekap_sonuc_backfill.py'nin ATTIĞI zengin firma verisinin (teklif veren TÜM
istekliler=roster, VKN, ortak girişim üyeleri, adres) EKAP yanıtının neresinde
olduğunu doğrulamak. Çalışan liste→detay akışını (durum=[5] → item['id'] →
GetByIhaleIdIhaleDetay) replike eder, sozlesmeBilgiList tam yapısını ve SONUÇ İLANI
veriHtml'inin roster kısmını stdout'a döker.

Çalıştırma (VDS'te — EKAP API'si yalnızca oradan erişilebilir):
  cd /opt/ihale-platform && python3 backend/ekap_firma_probe.py
"""
import asyncio, base64, json, os, re, ssl, sys, time, uuid
import httpx
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad
try:
    from dotenv import load_dotenv
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))
except Exception:
    pass
try:
    from proxy_config import rastgele_proxy_url  # EKAP artık direkt 404; Webshare proxy şart
except Exception:
    def rastgele_proxy_url():
        return None

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

BASE = "https://ekapv2.kik.gov.tr"
CRYPTO_KEY = b"Qm2LtXR0aByP69vZNKef4wMJ"
H = {"Accept": "application/json", "Content-Type": "application/json", "api-version": "v1",
     "Origin": BASE, "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36"}


def ssl_ctx():
    c = ssl.create_default_context(); c.set_ciphers("DEFAULT@SECLEVEL=1")
    c.check_hostname = False; c.verify_mode = ssl.CERT_NONE; return c


def crypto_headers():
    g = str(uuid.uuid4()); iv = get_random_bytes(16); ts = str(int(time.time() * 1000))
    def e(p): return base64.b64encode(AES.new(CRYPTO_KEY, AES.MODE_CBC, iv).encrypt(pad(p.encode(), 16))).decode()
    return {"X-Custom-Request-Guid": g, "X-Custom-Request-Siv": base64.b64encode(iv).decode(),
            "X-Custom-Request-R8id": e(g), "X-Custom-Request-Ts": e(ts)}


async def post(client, ep, data):
    try:
        r = await client.post(f"{BASE}{ep}", json=data, headers={**H, **crypto_headers()}, timeout=30.0)
        if r.status_code != 200:
            return (str(r.status_code), None)
        return ("ok", r.json())
    except Exception as ex:
        return (f"ERR:{type(ex).__name__}", None)


def mojibake(s):
    if not s:
        return s
    try:
        f = s.encode("latin-1").decode("utf-8")
        return f if any(c in f for c in "çğıöşüÇĞİÖŞÜ") else s
    except Exception:
        return s


def strip_tags(html):
    t = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", html, flags=re.I | re.S)
    t = t.replace("</td>", " | ").replace("</tr>", "\n").replace("</th>", " | ")
    t = re.sub(r"<[^>]+>", "", t)
    t = t.replace("&nbsp;", " ").replace("&amp;", "&")
    return re.sub(r"[ \t]+", " ", re.sub(r"\n\s*\n+", "\n", t)).strip()


FIRMA_RE = re.compile(r"[A-ZÇĞİÖŞÜ0-9][^\n|]{3,90}?(?:A\.?\s?Ş\.?|LTD|LİMİTED|ŞTİ|SAN\.?\s?VE|TİC\.?\s|İNŞAAT|MÜHENDİSLİK|SANAYİ)[^\n|]{0,45}", re.I)
VKN_RE = re.compile(r"\b\d{10,11}\b")
ROSTER_KELIME = re.compile(r"istekli|teklif edilen|teklif bedeli|uygun bulunan|değerlendirme dışı|ekonomik açıdan", re.I)


async def detay_incele(client, item, idx):
    hid = item.get("id"); ikn = item.get("ikn")
    print(f"\n{'='*74}\n### {idx}) IKN {ikn}  idare='{mojibake(item.get('idareAdi') or '')[:48]}'")
    d, veri = await post(client, "/b_ihalearama/api/IhaleDetay/GetByIhaleIdIhaleDetay", {"ihaleId": hid})
    print(f"detay → {d}")
    if not veri:
        return
    it = veri.get("item") or {}
    sbl = it.get("sozlesmeBilgiList") or []
    print(f"sozlesmeBilgiList: {len(sbl)}")
    if sbl:
        print("  [0] anahtarlar:", sorted(sbl[0].keys()))
        for k, v in sbl[0].items():
            if re.search(r"vergi|vkn|ortak|adres|istekli|teklif|kimlik|firma", k, re.I):
                print(f"    · {k} = {json.dumps(v, ensure_ascii=False, default=str)[:160]}")
    firma_anahtar = set()
    def gez(o):
        if isinstance(o, dict):
            for k, v in o.items():
                if re.search(r"istekli|teklif|vergi|vkn|ortak|adres|firma|yuklenici|kimlik", k, re.I):
                    firma_anahtar.add(k)
                gez(v)
        elif isinstance(o, list):
            for x in o[:6]:
                gez(x)
    gez(veri)
    print("  firma-ilişkili anahtarlar (tüm JSON):", sorted(firma_anahtar))

    il = it.get("ilanList") or []
    print(f"ilanList: {len(il)} belge")
    for e in il:
        fixed = mojibake(e.get("veriHtml") or "") or ""
        if not fixed:
            continue
        is_sonuc = bool(re.search(r"SONU[ÇC]\s*[İI]LANI", fixed, re.I))
        text = strip_tags(fixed)
        firmalar = list(dict.fromkeys(m.group(0).strip() for m in FIRMA_RE.finditer(text)))
        vkns = list(dict.fromkeys(VKN_RE.findall(text)))
        sinyal = [b for b in ["İstekli", "Teklif Edilen", "Teklif Bedeli", "Vergi", "T.C. Kimlik",
                              "Ortak Girişim", "Uygun Bulunan", "Değerlendirme"] if b.lower() in fixed.lower()]
        print(f"  belge sonuç={is_sonuc} tablo={fixed.count('<table')} len={len(fixed)} "
              f"firma_adayı={len(firmalar)} vkn_adayı={len(vkns)} sinyal={sinyal}")
        if is_sonuc or len(firmalar) > 1:
            print("    ── firma adayları ──")
            for fa in firmalar[:20]:
                print("      •", fa[:78])
            m = ROSTER_KELIME.search(text)
            if m:
                bas = max(0, m.start() - 200)
                print("    ── roster civarı metin (İstekli/Teklif etrafı) ──")
                print("   ", text[bas:bas + 1400].replace("\n", "\n    "))


async def liste_cek(durum, denemeler=6):
    """404'te farklı proxy ile tekrar dene (havuzda bloklu IP olabilir)."""
    for i in range(denemeler):
        proxy = rastgele_proxy_url()
        async with httpx.AsyncClient(verify=ssl_ctx(), http2=False, timeout=30.0, proxy=proxy) as client:
            d, veri = await post(client, "/b_ihalearama/api/Ihale/GetListByParameters", {
                "searchText": "", "paginationSkip": 0, "paginationTake": 100,
                "ihaleDurumIdList": durum, "searchType": "GirdigimGibi"})
            pxy = proxy.split('@')[-1] if proxy else 'direkt'
            print(f"  durum={durum} proxy={pxy} → {d}" + (f" toplam={veri.get('totalCount')}" if veri else ""))
            if veri and veri.get("list"):
                return veri
        await asyncio.sleep(0.5)
    return None


async def main():
    print("=== durum kodu testi (hangisi sonuç listesini veriyor?) ===")
    for durum in ([2], [5], [3], [4]):
        veri = await liste_cek(durum, denemeler=3)
        if durum == [2] and veri:
            print("  ↳ durum=[2] ÇALIŞIYOR → API/proxy sağlıklı")
    print("\n=== durum=[5] sonuç detayı inceleniyor ===")
    veri = await liste_cek([5], denemeler=8)
    if not veri:
        print("durum=[5] hiçbir proxy ile alınamadı."); return
    proxy = rastgele_proxy_url()
    async with httpx.AsyncClient(verify=ssl_ctx(), http2=False, timeout=30.0, proxy=proxy) as client:
        for idx, item in enumerate(veri["list"][:3], 1):
            await detay_incele(client, item, idx)
            await asyncio.sleep(0.4)


if __name__ == "__main__":
    asyncio.run(main())
