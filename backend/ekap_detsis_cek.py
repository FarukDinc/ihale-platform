# -*- coding: utf-8 -*-
"""
EKAP/DETSİS → idare_tur eşlemesi (OTORİTER katman, kaynak='ekap-detsis')
=======================================================================
ÇÖZÜLEN ZİNCİR (bkz. ekap_idare_probe.py — bulunması pahalıya mal oldu):

    1) DetsisAgaci           → 87.528 kayıt: idareId + ad + detsisNo + seviye
    2) GetListByParameters   → idareKodList=[idareId] ile O KURUMUN ihaleleri
    3) ihalenin idareAdi'si  → bizim `ilanlar.idare` ile AYNI STRING → eşleşme

Neden bu yol: `idareAdi` çoğu zaman jenerik alt birim adıdır ("BİLGİ İŞLEM DAİRE
BAŞKANLIĞI" DETSİS'te 114 kez geçer) → ad ile join AMBİGÜ. idareId üzerinden
gidince tekil ve kesin oluyor. Tür ise DETSİS'in UZUN adından çıkarılır (üst kurum
zincirini içerir: "… SAĞLIK BAKANLIĞI TÜRKİYE KAMU HASTANELERİ") — kısa addan
çıkarılamayan tür böyle çözülür.

⚠️ İKİ TUZAK (ikisine de düşüldü):
   - "idareKod" DETSİS No DEĞİL, **idareId**'dir (detsisNo/id → 0 sonuç).
   - 0 sonuç "filtre çalıştı" demek DEĞİL; eşleşmeyen değer de 0 döner.

⚠️ 20 Tem: paginationTake 1→300 (her farklı idare yazımı ayrı satır; tek yazım
   kapsamayı %32'de bırakıyordu). ESKİ take=1 checkpoint'iyle --devam ETME —
   kapsama eksik kalır; VDS'te checkpoint'i silip sıfırdan tara.

AĞ POLİTİKASI: tüm istekler proxy havuzundan (backend/proxy_havuz.py) geçer —
VDS'in kendi IP'si EKAP'a yüklenmez. Havuz IP başına soğuma + küresel hız tavanı
uygular, bloklanan IP'yi karantinaya alır. EKAP zayıf TLS kullandığı için
ekap_ssl_baglami() şart (yoksa her istek handshake'te ölür).

Kullanım:
    python ekap_detsis_cek.py --agac-cek            # 1) DETSİS ağacını indir (tek istek)
    python ekap_detsis_cek.py --tara                # 2) tam tarama (87K istek, ~2-4 saat)
    python ekap_detsis_cek.py --tara --limit 200    #    deneme turu
    python ekap_detsis_cek.py --yaz                 # 3) sonucu idare_tur tablosuna yaz
    python ekap_detsis_cek.py --tara --devam        #    kesintiden devam (checkpoint)

Env: SUPABASE_URL, SUPABASE_SERVICE_KEY, PROXY_* (backend/.env)
"""
import argparse
import asyncio
import base64
import json
import os
import sys
import time
import uuid

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

import httpx
from dotenv import load_dotenv
from Crypto.Cipher import AES
from Crypto.Random import get_random_bytes
from Crypto.Util.Padding import pad

sys.path.insert(0, os.path.dirname(__file__))
from proxy_havuz import havuz_al, async_havuz_al, ekap_ssl_baglami   # noqa: E402
from idare_tur_siniflandir import idare_tur_belirle, fold            # noqa: E402

# Eşzamanlı işçi sayısı. Sıralı sürüm 1.6 istek/sn veriyordu (istek gecikmesi
# ~600ms × tek akış) → 85K kurum ≈ 15 saat. Havuzun küresel tavanı 600/dk (=10/sn)
# olduğu için asıl sınır o; 24 işçi tavanı doldurmaya fazlasıyla yeter (~2,5 saat).
ESZAMANLI = int(os.environ.get("DETSIS_ESZAMANLI", "24"))

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")

BASE = "https://ekapv2.kik.gov.tr"
AGAC_URL  = f"{BASE}/b_idare/api/DetsisKurumBirim/DetsisAgaci"
LISTE_URL = f"{BASE}/b_ihalearama/api/Ihale/GetListByParameters"
KEY = b"Qm2LtXR0aByP69vZNKef4wMJ"          # AES-192-CBC (environment.r8fact)

VERI_DIZIN = os.path.join(os.path.dirname(__file__), "veri")
AGAC_DOSYA = os.path.join(VERI_DIZIN, "detsis_agaci.json")
SONUC_DOSYA = os.path.join(VERI_DIZIN, "idare_tur_eslesme.json")
CHECKPOINT = os.path.join(VERI_DIZIN, "detsis_tarama_checkpoint.json")

# DetsisAgaci'nin beklediği (alışılmadık iç içe) gövde — DevTools'tan alındı
AGAC_YUK = {"loadOptions": {"filter": {
    "sort": [], "group": [], "filter": [], "totalSummary": [],
    "groupSummary": [], "select": [], "preSelect": [], "primaryKey": []}}}


def crypto_headers():
    guid = str(uuid.uuid4())
    iv = get_random_bytes(16)
    ts = str(int(time.time() * 1000))
    def enc(pt):
        return base64.b64encode(AES.new(KEY, AES.MODE_CBC, iv).encrypt(pad(pt.encode(), 16))).decode()
    return {
        "X-Custom-Request-Guid": guid,
        "X-Custom-Request-Siv": base64.b64encode(iv).decode(),
        "X-Custom-Request-R8id": enc(guid),
        "X-Custom-Request-Ts": enc(ts),
        "Content-Type": "application/json",
        "Accept": "application/json",
        # ŞART: yoksa açıklama alanları i18n anahtarı/İngilizce döner (bkz. ekap_scraper.py)
        "Accept-Language": "tr-TR,tr;q=0.9",
        "Origin": BASE,
        "Referer": f"{BASE}/ekap/search",
    }


def _dizin():
    os.makedirs(VERI_DIZIN, exist_ok=True)


# ── 1) DETSİS ağacını indir ────────────────────────────────────────────────
def agac_cek(havuz):
    _dizin()
    print("→ DETSİS ağacı indiriliyor (~15 MB)…")
    with havuz.istek() as ist:
        try:
            r = ist.client.post(AGAC_URL, headers=crypto_headers(), json=AGAC_YUK, timeout=180)
            ist.yanit(r)                 # cezalandırma kararını havuz versin
            if r.status_code != 200:
                print(f"✗ ağaç indirilemedi: HTTP {r.status_code} {r.text[:160]}")
                return None
        except Exception as e:
            ist.basarisiz()
            print(f"✗ ağaç indirilemedi: {type(e).__name__} {e}")
            return None
    veri = r.json()["loadResult"]["data"]
    with open(AGAC_DOSYA, "w", encoding="utf-8") as f:
        json.dump(veri, f, ensure_ascii=False)
    print(f"✓ {len(veri):,} DETSİS kaydı → {AGAC_DOSYA}")
    return veri


def agac_yukle():
    if not os.path.exists(AGAC_DOSYA):
        print("✗ ağaç dosyası yok — önce --agac-cek çalıştırın")
        return None
    with open(AGAC_DOSYA, encoding="utf-8") as f:
        return json.load(f)


# ── 2a) Eşzamanlı tarama çekirdeği ────────────────────────────────────────
async def _tara_async(hedefler, kurumlar, sonuc, baslangic):
    """
    ESZAMANLI işçiyle tara. Sıralı sürüm 1.6 istek/sn veriyordu (tek akış ×
    ~600ms gecikme) → 85K kurum ≈ 15 saat. Gerçek sınır havuzun küresel
    tavanı (600/dk); işçiler onu doldurur, ~2,5 saate iner.
    Havuz zaten IP soğuması + küresel tavan + karantina uyguluyor; burada
    ek bir hız kısıtı GEREKMEZ (iki kat sınırlama işi yavaşlatırdı).
    """
    havuz = async_havuz_al(ssl_baglami=ekap_ssl_baglami())
    kilit = asyncio.Lock()
    sayac = {"islenen": 0}
    t0 = time.time()

    async def isle(iid):
        kayit = kurumlar[iid]
        # take=300: EKAP idare adını her ihalede farklı yazar; tek yazım kurumun
        # ihalelerinin ~%33,5'ini kapsıyordu (kapsama %32'de takıldı). 300 ihalede
        # geçen HER farklı yazım ayrı idare_tur satırı olur → kapsama ~%90.
        yuk = {"searchText": "", "paginationSkip": 0, "paginationTake": 300,
               "searchType": "GirdigimGibi", "idareKodList": [iid]}
        d = None
        async with havuz.istek() as ist:
            try:
                r = await ist.client.post(LISTE_URL, headers=crypto_headers(), json=yuk, timeout=40)
                # DİKKAT: `if status != 200: basarisiz()` YAZMA — 404/400 blok
                # sinyali değildir, havuzu kendi kendine tüketir. Kararı yanit() versin.
                ist.yanit(r)
                if r.status_code == 200:
                    d = r.json()
            except Exception:
                ist.basarisiz()          # gerçek ağ/TLS hatası → uç cezalansın

        async with kilit:
            sayac["islenen"] += 1
            i = sayac["islenen"]
            if d:
                n = d.get("totalCount") or 0
                liste = d.get("list") or []
                if n > 0 and liste:
                    # her farklı yazımı topla: fold-anahtarı başına görülme sayısı
                    yazimlar = {}
                    for kalem in liste:
                        ad = (kalem.get("idareAdi") or "").strip()
                        if not ad:
                            continue
                        a = fold(ad)
                        if a in yazimlar:
                            yazimlar[a]["gorulme"] += 1
                        else:
                            yazimlar[a] = {"ad": ad, "gorulme": 1}
                    # TÜR: DETSİS'in UZUN adından (üst kurum zincirini içerir)
                    tur0, guven0 = idare_tur_belirle(kayit.get("ad") or "")
                    for anahtar, y in yazimlar.items():
                        tur, guven = tur0, guven0
                        if tur == "bilinmiyor":      # uzun ad çözemediyse yazımı dene
                            tur, guven = idare_tur_belirle(y["ad"])
                        onceki = sonuc.get(anahtar)
                        # jenerik yazımlar ("BİLGİ İŞLEM DAİRE BAŞKANLIĞI") birden çok
                        # kurumda görünür → yazımı EN ÇOK kullanan kurum kazanır
                        if onceki is None or y["gorulme"] > onceki.get("gorulme", 0):
                            sonuc[anahtar] = {
                                "idare_ad": y["ad"], "tur": tur, "guven": guven,
                                "detsis_no": kayit.get("detsisNo"), "idare_id": iid,
                                "detsis_ad": kayit.get("ad"), "ihale_sayisi": n,
                                "gorulme": y["gorulme"],
                            }
            if i % 250 == 0:
                gecen = time.time() - t0
                hiz = i / gecen if gecen else 0
                kalan = (len(hedefler) - i) / hiz / 60 if hiz else 0
                print(f"  {i:,}/{len(hedefler):,} · eşleşme {len(sonuc):,} · "
                      f"{hiz:.1f} istek/sn · ~{kalan:.0f} dk kaldı", flush=True)
            # sonuc artık yazım-bazlı (kurum başına çok satır) → dosya büyük,
            # her 250'de yazmak IO israfı; 1000'de bir yeter
            if i % 1000 == 0:
                with open(CHECKPOINT, "w", encoding="utf-8") as f:
                    json.dump({"indeks": baslangic + i, "sonuc": sonuc}, f, ensure_ascii=False)

    sem = asyncio.Semaphore(ESZAMANLI)

    async def sinirli(iid):
        async with sem:
            await isle(iid)

    print(f"→ {ESZAMANLI} eşzamanlı işçi ile taranıyor…")
    await asyncio.gather(*(sinirli(x) for x in hedefler))
    await havuz.kapat()
    havuz.ozet_yaz()


# ── 2) Tam tarama: her idareId için ihale var mı, varsa idareAdi ne? ───────
def tara(havuz, limit=0, devam=False):
    agac = agac_yukle()
    if not agac:
        return
    _dizin()

    # aynı idareId birden çok DETSİS satırında olabilir → tekilleştir,
    # tür çıkarımı için EN UZUN adı sakla (üst kurum zinciri en çok onda)
    kurumlar = {}
    for r in agac:
        iid = r.get("idareId")
        if iid is None:
            continue
        onceki = kurumlar.get(iid)
        if onceki is None or len(r.get("ad") or "") > len(onceki.get("ad") or ""):
            kurumlar[iid] = r
    hedefler = sorted(kurumlar)
    print(f"→ {len(hedefler):,} tekil idareId (87K satırdan)")

    sonuc, baslangic = {}, 0
    if devam and os.path.exists(CHECKPOINT):
        with open(CHECKPOINT, encoding="utf-8") as f:
            ck = json.load(f)
        sonuc = ck.get("sonuc", {})
        baslangic = ck.get("indeks", 0)
        print(f"→ checkpoint'ten devam: {baslangic:,}. sıradan, {len(sonuc):,} eşleşme mevcut")

    if limit:
        hedefler = hedefler[baslangic:baslangic + limit]
    else:
        hedefler = hedefler[baslangic:]

    asyncio.run(_tara_async(hedefler, kurumlar, sonuc, baslangic))

    with open(SONUC_DOSYA, "w", encoding="utf-8") as f:
        json.dump(sonuc, f, ensure_ascii=False, indent=1)
    print(f"\n✓ tarama bitti — {len(sonuc):,} idare eşleşmesi → {SONUC_DOSYA}")

    from collections import Counter
    dag = Counter(v["tur"] for v in sonuc.values())
    print("\n=== TÜR DAĞILIMI ===")
    for t, n in dag.most_common():
        print(f"   {t:<24} {n:>6}")
    # NOT: havuz özeti _tara_async içinde basılır (havuz orada oluşturulup kapatılır)


# ── 3) idare_tur tablosuna yaz ────────────────────────────────────────────
def yaz():
    if not (SUPABASE_URL and SUPABASE_KEY):
        print("✗ SUPABASE_URL / SUPABASE_SERVICE_KEY eksik (.env — VDS'te çalıştırın)")
        return
    if not os.path.exists(SONUC_DOSYA):
        print("✗ eşleşme dosyası yok — önce --tara")
        return
    with open(SONUC_DOSYA, encoding="utf-8") as f:
        sonuc = json.load(f)

    kayitlar = [{
        "idare_norm": k,
        "idare_ad": v["idare_ad"],
        "tur": v["tur"],
        "ust_kurum": (v.get("detsis_ad") or "")[:300] or None,
        "detsis_no": str(v["detsis_no"]) if v.get("detsis_no") is not None else None,
        "kaynak": "ekap-detsis",
        "guven": max(v.get("guven", 0), 80),      # DETSİS zinciri → yüksek güven
    } for k, v in sonuc.items()]

    print(f"→ {len(kayitlar):,} kayıt yazılıyor…")
    basari = 0
    with httpx.Client(timeout=90.0) as c:
        for i in range(0, len(kayitlar), 500):
            dilim = kayitlar[i:i + 500]
            r = c.post(
                f"{SUPABASE_URL}/rest/v1/idare_tur",
                headers={"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}",
                         "Content-Type": "application/json",
                         "Prefer": "resolution=merge-duplicates,return=minimal"},
                params={"on_conflict": "idare_norm"},
                json=dilim,
            )
            if r.status_code >= 300:
                print(f"  ✗ {i}: {r.status_code} {r.text[:180]}")
            else:
                basari += len(dilim)
                print(f"  {basari:,}/{len(kayitlar):,}", flush=True)
    print(f"✓ {basari:,} kayıt yazıldı (kaynak='ekap-detsis')")


def main():
    ap = argparse.ArgumentParser(description="EKAP/DETSİS → idare türü eşlemesi")
    ap.add_argument("--agac-cek", action="store_true", help="DETSİS ağacını indir")
    ap.add_argument("--tara", action="store_true", help="idareId başına ihale sorgusu (tam tarama)")
    ap.add_argument("--yaz", action="store_true", help="sonucu idare_tur tablosuna yaz")
    ap.add_argument("--limit", type=int, default=0, help="deneme için kayıt sınırı")
    ap.add_argument("--devam", action="store_true", help="checkpoint'ten devam et")
    a = ap.parse_args()

    if not (a.agac_cek or a.tara or a.yaz):
        ap.print_help()
        return

    if a.agac_cek or a.tara:
        # EKAP zayıf TLS → ssl_baglami ŞART; proxy havuzu VDS IP'sini korur
        if a.agac_cek:
            agac_cek(havuz_al(ssl_baglami=ekap_ssl_baglami()))
        if a.tara:
            tara(None, limit=a.limit, devam=a.devam)   # async havuzu içeride alınır
    if a.yaz:
        yaz()


if __name__ == "__main__":
    main()
