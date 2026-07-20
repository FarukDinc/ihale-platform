# -*- coding: utf-8 -*-
"""
ilan_metni_backfill.py — GEÇMİŞ ilanların ilan_metni'ni (kalem listesi) EKAP'tan doldurur.

NEDEN: ilanlar tablosundaki ~352K geçmiş kayıt ekap_sonuc_backfill tarafından KOMPAKT
üretilmiş (ilan_metni=NULL). O karar eski managed Supabase'in satır/boyut limitleri içindi;
self-hosted VDS'te artık kısıt yok (128GB boş, DB 3.5GB). ilan_metni platformun EN ZENGİN
konu sinyali: "10 KISIM 13 KALEM GIDA MADDESİ" başlığı hiçbir şey söylemez ama kalem listesi
"pirinç, un, yağ" der. Eşleştirme motorunu (uygun firmalar / benzer ihaleler) ve site içi
aramayı besler — arama_fold ÜRETİLMİŞ kolonu ilan_metni'yi de içerir, yani dolduğu anda
352K geçmiş ilan aranabilir hale gelir.

KANIT (backend/ekap_ilan_metni_sonda.py, 17 Tem): sonuçlanmış ihale listesinden alınan
İÇ ihaleId ile detay çağrılınca 6/6 ilan HTML'i döndü (630-5464 char) → uygulanabilir.
DİKKAT: ilanlar.ekap_id İKN saklar ("2026/1210669"); detay endpoint'i EKAP'ın İÇ id'sini
ister. İKN ile çağrı HTTP 500, searchText ile İKN araması totalCount=0. İç id YALNIZCA
liste yanıtından gelir → bu yüzden listeyi sayfalayıp İKN eşleştiriyoruz (tersi mümkün değil).

YAVAŞ & GÜVENLİ (kullanıcı kararı): gece cron'una küçük dilim olarak eklenir. EKAP üçüncü
taraf; agresif tarama IP bloğuna ve GECE İHALE TOPLAMANIN durmasına yol açabilir. Bu yüzden:
düşük eşzamanlılık (öntanım 2), istekler arası uyku, checkpoint ile kaldığı yerden devam,
ardışık hata eşiğinde kendini durdurma. Liste "en yeni önce" olduğundan değer hemen birikir.

── SESSİZ KAYIP KORUMASI (bkz. ekap_ihale_backfill.py referans düzeltmesi) ─────────────────
EKAP boş liste / geçici hata / gerçek son'u AYNI göründüğü için eskiden veri sessizce
düşüyordu. Artık:
  · Boş sayfa VERİ BİTTİ sanılıp körlemesine ATLANMAZ. Gerçek son yalnız totalCount ile
    teyit edilir (skip >= totalCount). Değilse aynı offset sınırlı kez yeniden denenir.
  · EKAP'ın "delik" (geçerli yanıt + boş liste, sona gelinmeden) döndürdüğü nadir anomali
    SAYILARAK atlanır (sonsuza takılma yok); geçici (yanıtsız) hata ise checkpoint
    İLERLETİLMEDEN tur durdurulur (sonraki tur tekrar dener). Aynı offset ardışık turlarda
    da yanıtsızsa kalıcı sayılıp sayılarak atlanır (rule 6: takılıp kalma).
  · Detayı ÇEKİLEMEYEN (geçici) ihaleler artık kaybolmaz: bu turda birkaç kez denenir,
    olmazsa KALICI bir "yeniden-dene kuyruğu"na alınır ve checkpoint güvenle ilerler.
    Kuyruk her tur başında boşaltılır; KUYRUK_MAX_DENEME'yi aşan kayıt kalıcı sayılıp loglanır.

DEPOLAMA: yalnız ilan_metni yazılır (ilan_html DEĞİL) — metin arama/embedding için yeterli,
depolamayı ~yarıya indirir ve ham HTML'i saklamamak XSS yüzeyini de küçültür.

Kullanım:
  python ilan_metni_backfill.py --max-pages 5 --dry-run   # yazmadan dene
  python ilan_metni_backfill.py --max-pages 200           # kaldığı yerden devam (checkpoint)
  python ilan_metni_backfill.py --reset                   # baştan başla
Env: SUPABASE_URL, SUPABASE_SERVICE_KEY (backend/.env)
"""
import argparse
import asyncio
import json
import os
import sys
from datetime import datetime, timezone

import httpx
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(__file__))
from ekap_scraper import post, html_temizle                      # imzalı POST + HTML→metin
from ekap_sonuc_backfill import ssl_ctx, sb_headers  # rastgele_proxy_url ARTIK KULLANILMIYOR
from proxy_havuz import async_havuz_al, ekap_ssl_baglami

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))
SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")

LISTE_ENDPOINT = "/b_ihalearama/api/Ihale/GetListByParameters"
DETAY_ENDPOINT = "/b_ihalearama/api/IhaleDetay/GetByIhaleIdIhaleDetay"
SAYFA_BOYUTU = 100
CHECKPOINT_FILE = os.path.join(os.path.dirname(__file__), ".ilan_metni_backfill_checkpoint.json")
RETRY_QUEUE_FILE = os.path.join(os.path.dirname(__file__), ".ilan_metni_backfill_retry.json")

# ── Sessiz-kayıp eşikleri (GEÇİCİ hatayı KALICI durumdan ayırmak için) ──────────────────────
SAYFA_RETRY = 3        # aynı LISTE offset'ini geçici hata/rate-limit için bu kadar kez daha dene
DETAY_RETRY = 2        # sayfadaki başarısız (geçici) detay çağrılarını bu tur içinde bu kadar kez daha dene
TAKILMA_SINIRI = 3     # AYNI offset bu kadar ARDIŞIK TURDA da yanıtsız kalırsa kalıcı say → SAYARAK atla
ATLAMA_SINIRI = 20     # bir turda en fazla bu kadar boş sayfa atlanır; aşılırsa sistemik kabul edip dur
KUYRUK_MAX_DENEME = 5  # yeniden-dene kuyruğunda bir kayıt bu kadar denendikten sonra hâlâ olmuyorsa kalıcı say, düş


# ── Checkpoint ──────────────────────────────────────────────────────────────
def checkpoint_oku() -> dict:
    """Tüm checkpoint durumunu döndürür: {skip, takili_skip, takili_sayac, ...}.
    Eski format ({skip, guncellendi}) da sorunsuz okunur (yeni alanlar None/0 varsayılır)."""
    try:
        with open(CHECKPOINT_FILE, encoding="utf-8") as f:
            d = json.load(f)
            return d if isinstance(d, dict) else {}
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def checkpoint_yaz(skip: int, takili_skip=None, takili_sayac: int = 0):
    # Atomik yazım (referanstaki gibi): yarıda kesilirse bozuk checkpoint kalmaz.
    tmp = CHECKPOINT_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump({
            "skip": skip,
            "takili_skip": takili_skip,
            "takili_sayac": takili_sayac,
            "guncellendi": datetime.now(timezone.utc).isoformat(),
        }, f, ensure_ascii=False)
    os.replace(tmp, CHECKPOINT_FILE)


# ── Yeniden-dene kuyruğu (detayı GEÇİCİ çekilemeyen ihaleler; checkpoint ilerlese de kaybolmasınlar) ──
def kuyruk_oku() -> list:
    try:
        with open(RETRY_QUEUE_FILE, encoding="utf-8") as f:
            d = json.load(f)
            return d if isinstance(d, list) else []
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def kuyruk_yaz(kuyruk: list):
    tmp = RETRY_QUEUE_FILE + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(kuyruk, f, ensure_ascii=False)
    os.replace(tmp, RETRY_QUEUE_FILE)


def kuyruga_ekle(kalan_hedefler: list, eksik: dict, dry_run: bool) -> int:
    """Detayı bu turda çekilemeyen ihaleleri kuyruğa ekler (ilan_id ile tekilleştirerek)."""
    if dry_run or not kalan_hedefler:
        return 0
    kuyruk = kuyruk_oku()
    mevcut = {str(k.get("ilan_id")) for k in kuyruk}
    eklenen = 0
    for it in kalan_hedefler:
        ikn = str(it.get("ikn") or "")
        ilan_id = str(eksik.get(ikn, ""))
        if not ilan_id or ilan_id in mevcut:
            continue
        kuyruk.append({"ikn": ikn, "ic_id": it.get("id"), "ilan_id": ilan_id, "deneme": 1})
        mevcut.add(ilan_id)
        eklenen += 1
    if eklenen:
        kuyruk_yaz(kuyruk)
    return eklenen


def eksik_olanlar(ikn_listesi: list) -> dict:
    """Bu sayfadaki İKN'lerden ilan_metni'si BOŞ olanları {ikn: ilan_id} döndürür.
    Sayfa başına TEK REST çağrısı — 352K'lık dev harita kurmaktan çok daha hafif."""
    ikn_listesi = [i for i in ikn_listesi if i]
    if not ikn_listesi:
        return {}
    # in.() — İKN'de '/' var, çift tırnakla sar (ayraçla karışmasın)
    liste = ",".join('"' + str(i).replace('"', '') + '"' for i in ikn_listesi)
    with httpx.Client(timeout=30.0) as c:
        r = c.get(f"{SUPABASE_URL}/rest/v1/ilanlar", params={
            "select": "id,ikn",
            "ikn": f"in.({liste})",
            "ilan_metni": "is.null",
        }, headers=sb_headers())
        if r.status_code >= 300:
            print(f"    ✗ eksik sorgusu hatası: {r.status_code} {r.text[:150]}")
            return {}
        return {str(row["ikn"]): row["id"] for row in r.json() if row.get("ikn")}


def metni_yaz(ilan_id: str, metin: str) -> bool:
    with httpx.Client(timeout=30.0) as c:
        r = c.patch(f"{SUPABASE_URL}/rest/v1/ilanlar",
                    params={"id": f"eq.{ilan_id}"},
                    json={"ilan_metni": metin},
                    headers={**sb_headers(), "Prefer": "return=minimal"})
        if r.status_code >= 300:
            print(f"    ✗ yazma hatası ({ilan_id}): {r.status_code} {r.text[:120]}")
            return False
        return True


async def bir_ihale(havuz, sem, ikn: str, ic_id, ilan_id: str, dry_run: bool) -> str:
    """Tek ihale: detay çek → ilan HTML'ini metne çevir → yaz. Döner: 'yazildi'|'bos'|'hata'.
    'bos'  = EKAP'ta gerçekten metin yok (≤50 char) → KALICI, yeniden denenmez.
    'hata' = detay çekilemedi (post() {} döndü) veya DB yazımı başarısız → GEÇİCİ, yeniden denenir."""
    async with sem:
        veri = await post(havuz, DETAY_ENDPOINT, {"ihaleId": ic_id})
        await asyncio.sleep(0.35)          # EKAP'a nazik ol (eşzamanlılıkla birlikte etkin hız düşük)
    if not veri:
        return "hata"
    ilan_list = ((veri.get("item") or {}).get("ilanList") or [])
    html = (ilan_list[0].get("veriHtml") if ilan_list else "") or ""
    metin = (html_temizle(html) or "").strip() if html else ""
    if len(metin) <= 50:
        return "bos"
    if dry_run:
        print(f"    [DRY-RUN] {ikn} → {len(metin)} char yazılacaktı")
        return "yazildi"
    return "yazildi" if metni_yaz(ilan_id, metin) else "hata"


async def sayfa_getir(havuz, skip: int):
    """LISTE sayfasını AYNI offset için sınırlı kez dener (geçici hata/rate-limit için).
    Döner (durum, veri, lst):
      'ok'  → lst dolu, işlenecek.
      'son' → GEÇERLİ yanıt + boş liste + skip >= totalCount → GERÇEK son (backlog tarandı).
      'bos' → sınırlı denemeye rağmen boş, gerçek son DEĞİL. Çağıran, veri'ye bakıp ayırt eder:
              veri GEÇERLİ (totalCount var) → EKAP'ın döndürdüğü 'delik' (zehirli bölge anomalisi);
              veri {} → yanıt yok (geçici hata / EKAP sağlıksız).
    NOT: post() havuz tükenişinde RuntimeError fırlatır; burada YUTULMAZ (emniyet supabı üste çıksın)."""
    veri = {}
    for deneme in range(SAYFA_RETRY + 1):
        veri = await post(havuz, LISTE_ENDPOINT, {
            "searchText": "", "paginationSkip": skip, "paginationTake": SAYFA_BOYUTU,
            "ihaleDurumIdList": [5], "searchType": "GirdigimGibi",
        })
        lst = (veri or {}).get("list") or []
        if lst:
            return "ok", veri, lst
        # Boş: GERÇEK son mu? totalCount YALNIZ geçerli yanıtta olur (post() geçici hatada {} döner).
        if isinstance(veri, dict) and "totalCount" in veri and skip >= int(veri.get("totalCount") or 0):
            return "son", veri, []
        # Geçici hata ya da 'delik' → AYNI offseti bekleyip yeniden dene (körlemesine ATLAMA yok).
        if deneme < SAYFA_RETRY:
            await asyncio.sleep(2 * (deneme + 1))
    return "bos", veri, []


async def sayfa_detaylari_isle(havuz, sem, hedefler: list, eksik: dict, dry_run: bool):
    """Sayfadaki eksik ihalelerin detayını çeker; GEÇİCİ 'hata'ları bu tur içinde sınırlı kez yeniden dener.
    Döner (yazildi, bos, kalan): kalan = DETAY_RETRY sonrası HÂLÂ başarısız olanlar (kuyruğa gider)."""
    yazildi = bos = 0
    kalan = list(hedefler)
    for tur in range(DETAY_RETRY + 1):
        if not kalan:
            break
        sonuclar = await asyncio.gather(*[
            bir_ihale(havuz, sem, str(it.get("ikn")), it.get("id"),
                      eksik[str(it.get("ikn"))], dry_run)
            for it in kalan
        ])
        yeniden = []
        for it, sonuc in zip(kalan, sonuclar):
            if sonuc == "yazildi":
                yazildi += 1
            elif sonuc == "bos":
                bos += 1                       # EKAP'ta gerçekten metin yok → kalıcı, tekrar deneme
            else:                              # 'hata' = geçici → yeniden dene
                yeniden.append(it)
        kalan = yeniden
        if kalan and tur < DETAY_RETRY:
            await asyncio.sleep(1.5 * (tur + 1))
    return yazildi, bos, kalan


async def kuyrugu_isle(havuz, sem, dry_run: bool):
    """Önceki turlardan kalan başarısız (geçici) detayları yeniden dener.
    Döner (yazildi, bos, kalici). Çözülemeyenler deneme sayısı artırılarak kuyrukta bırakılır;
    KUYRUK_MAX_DENEME'yi aşan kayıt kalıcı sayılıp düşürülür (kurtarma ayrı iş — rule 7)."""
    kuyruk = kuyruk_oku()
    if not kuyruk:
        return 0, 0, 0
    print(f"→ Yeniden-dene kuyruğu: {len(kuyruk)} bekleyen başarısız detay işleniyor…")
    yazildi = bos = kalici = 0
    sonuclar = await asyncio.gather(*[
        bir_ihale(havuz, sem, str(k.get("ikn")), k.get("ic_id"), str(k.get("ilan_id")), dry_run)
        for k in kuyruk
    ])
    yeni_kuyruk = []
    for k, sonuc in zip(kuyruk, sonuclar):
        if sonuc == "yazildi":
            yazildi += 1
        elif sonuc == "bos":
            bos += 1                            # EKAP'ta gerçekten yok → çözüldü, kuyruktan düş
        else:
            deneme = int(k.get("deneme", 0)) + 1
            if deneme >= KUYRUK_MAX_DENEME:
                kalici += 1
                print(f"    ✗ KALICI: ilan_id={k.get('ilan_id')} ikn={k.get('ikn')} "
                      f"{deneme} denemede çekilemedi — kuyruktan düşürüldü, ilan_metni NULL kalıyor.")
            else:
                yeni_kuyruk.append({**k, "deneme": deneme})
    if not dry_run:
        kuyruk_yaz(yeni_kuyruk)
    print(f"  kuyruk sonucu: {yazildi} yazıldı, {bos} EKAP'ta yok, "
          f"{kalici} kalıcı başarısız, {len(yeni_kuyruk)} tekrar bekliyor.")
    return yazildi, bos, kalici


async def calis(max_pages: int, dry_run: bool, start_skip, eszamanli: int):
    cp = checkpoint_oku()
    if start_skip is not None:
        skip = start_skip
        takili_skip, takili_sayac = None, 0
    else:
        skip = int(cp.get("skip", 0))
        takili_skip = cp.get("takili_skip")
        takili_sayac = int(cp.get("takili_sayac") or 0)

    # ESKİ: rastgele_proxy_url() tur başına TEK IP seçiyordu — 100 IP'nin 99'u boşta.
    # 20 Tem: dört scraper havuza bağlanırken bu dosya listede yoktu, eski yöntemde kalmıştı.
    havuz = async_havuz_al(ssl_baglami=ekap_ssl_baglami())
    sem = asyncio.Semaphore(eszamanli)
    print(f"→ EKAP sonuçlanmış liste taranıyor (skip={skip}, max_pages={max_pages}, eşzamanlı={eszamanli})\n")

    tarandi = hedef = yazildi = bos = 0
    kuyruga_eklenen = kuyruktan_yazildi = kuyruk_bos = kalici_basarisiz = 0
    atlanan_sayfa = 0
    tamamlandi = durduruldu = False

    def kaydet(yeni_skip, tk, ts):
        nonlocal skip, takili_skip, takili_sayac
        skip, takili_skip, takili_sayac = yeni_skip, tk, ts
        if not dry_run:
            checkpoint_yaz(yeni_skip, tk, ts)

    # 0) Önce önceki turlardan kalan başarısız detayları dene.
    ky, kb, kk = await kuyrugu_isle(havuz, sem, dry_run)
    kuyruktan_yazildi += ky
    kuyruk_bos += kb
    kalici_basarisiz += kk

    for _ in range(max_pages):
        durum, veri, lst = await sayfa_getir(havuz, skip)

        # ── Gerçek son (totalCount teyitli) ──────────────────────────
        if durum == "son":
            tamamlandi = True
            print(f"  ✓ Liste sonuna gelindi (skip={skip} ≥ totalCount) — backlog tarandı.")
            kaydet(skip, None, 0)
            break

        # ── Boş sayfa: gerçek son DEĞİL (geçici hata ya da 'delik') ───
        if durum == "bos":
            ekap_yanit_verdi = isinstance(veri, dict) and "totalCount" in veri
            if ekap_yanit_verdi:
                # EKAP açık AMA bu offset için boş liste döndürdü = 'delik' (zehirli bölge anomalisi,
                # bkz. ekap_ihale_backfill.py). Sınırlı deneme sürdü → SAYARAK atla (rule 6: takılma yok).
                atlanan_sayfa += 1
                print(f"  ⚠ boş sayfa ama sona gelinmedi (skip={skip}) — EKAP 'delik' döndürdü, "
                      f"SAYILARAK atlanıyor ({atlanan_sayfa}. kez).")
                kaydet(skip + SAYFA_BOYUTU, None, 0)
                if atlanan_sayfa >= ATLAMA_SINIRI:
                    durduruldu = True
                    print(f"  ✗ {atlanan_sayfa} boş sayfa atlandı — tekil anomali değil sistemik. "
                          f"Tur durduruldu (checkpoint skip={skip}).")
                    break
                continue
            # Yanıt YOK (geçici hata / EKAP sağlıksız). SAYFA_RETRY denemeye rağmen boş →
            # checkpoint'i İLERLETME (körlemesine atlama = veri kaybı). takili ile takılma-koruması:
            if takili_skip == skip:
                takili_sayac += 1
            else:
                takili_skip, takili_sayac = skip, 1
            if takili_sayac >= TAKILMA_SINIRI:
                # AYNI offset TAKILMA_SINIRI turdur yanıtsız → kalıcı sorunlu LISTE offseti say,
                # sonsuza takılma (rule 6): SAYARAK atla, ilerle.
                atlanan_sayfa += 1
                print(f"  ✗ skip={skip} {takili_sayac} turdur yanıtsız — kalıcı sorunlu offset sayılıp "
                      f"SAYILARAK atlanıyor ({atlanan_sayfa}. kez).")
                kaydet(skip + SAYFA_BOYUTU, None, 0)
                if atlanan_sayfa >= ATLAMA_SINIRI:
                    durduruldu = True
                    print(f"  ✗ {atlanan_sayfa} sayfa atlandı — sistemik. Tur durduruldu.")
                    break
                continue
            durduruldu = True
            kaydet(skip, takili_skip, takili_sayac)   # skip DEĞİŞMEDEN korunur
            print(f"  ✗ EKAP yanıt vermiyor (skip={skip}, {SAYFA_RETRY + 1} deneme boş/başarısız). "
                  f"Tur durduruldu, checkpoint KORUNDU ({takili_sayac}/{TAKILMA_SINIRI}); "
                  f"sonraki tur buradan tekrar dener.")
            break

        # ── durum == 'ok': sayfayı işle ──────────────────────────────
        tarandi += len(lst)
        eksik = eksik_olanlar([it.get("ikn") for it in lst])
        hedefler = [it for it in lst if str(it.get("ikn") or "") in eksik]
        hedef += len(hedefler)

        sayfa_yazildi, sayfa_bos, kalan = await sayfa_detaylari_isle(havuz, sem, hedefler, eksik, dry_run)
        yazildi += sayfa_yazildi
        bos += sayfa_bos
        if kalan:
            # Detayı bu turda çekilemeyen (geçici) ihaleler kuyruğa alınır → checkpoint ilerlese de
            # KAYBOLMAZLAR; sonraki turlarda yeniden denenir. (Bug 2 sessiz orfan düzeltmesi.)
            kuyruga_eklenen += kuyruga_ekle(kalan, eksik, dry_run)

        # Başarısızlar kuyrukta güvende → checkpoint HER ZAMAN ilerler (sessiz kayıp YOK, takılma YOK).
        kaydet(skip + len(lst), None, 0)
        print(f"  … skip={skip} | sayfada {len(lst)} kayıt, {len(hedefler)} eksik | "
              f"yazıldı={yazildi} boş={bos} kuyruğa={kuyruga_eklenen}")

    # ── Özet (rule 4: gerçek durumu yansıt, sahte 'Bitti ✓' verme) ──
    if tamamlandi:
        bas = "✓ Backlog sonuna ulaşıldı"
    elif durduruldu:
        bas = "⚠ Tur ERKEN DURDU (EKAP/veri sorunu) — checkpoint korundu, sonraki tur devam eder"
    else:
        bas = "→ Tur bitti (max-pages sınırı) — backlog henüz sürüyor"
    kalan_kuyruk = len(kuyruk_oku())
    print(f"\n{bas}")
    print(f"  tarandı={tarandi}, eksikti={hedef} → yazıldı={yazildi} (+kuyruktan {kuyruktan_yazildi}), "
          f"EKAP'ta metin yok={bos + kuyruk_bos}, kuyruğa eklendi={kuyruga_eklenen}, "
          f"kalıcı çekilemedi={kalici_basarisiz}, boş sayfa atlandı={atlanan_sayfa}. (checkpoint skip={skip})")
    if kalan_kuyruk:
        print(f"  ℹ {kalan_kuyruk} başarısız detay yeniden-dene kuyruğunda (sonraki tur denenecek).")
    if kalici_basarisiz:
        print(f"  ⚠ {kalici_basarisiz} kayıt {KUYRUK_MAX_DENEME} denemede çekilemedi, ilan_metni NULL bırakıldı "
              f"(ileride hedefli kurtarma turu gerekebilir).")


def main():
    ap = argparse.ArgumentParser(description="Geçmiş ilanların ilan_metni'ni EKAP'tan doldur (yavaş & güvenli)")
    ap.add_argument("--max-pages", type=int, default=200, help="bu turda taranacak sayfa (100 kayıt/sayfa)")
    ap.add_argument("--eszamanli", type=int, default=2, help="eşzamanlı detay çağrısı (öntanım 2 — EKAP'a nazik)")
    ap.add_argument("--start-skip", type=int, default=None, help="checkpoint yerine bu offset'ten başla")
    ap.add_argument("--reset", action="store_true", help="checkpoint'i sıfırla (baştan)")
    ap.add_argument("--dry-run", action="store_true", help="DB'ye yazma, sadece raporla")
    args = ap.parse_args()

    if not SUPABASE_URL or not SUPABASE_KEY:
        print("✗ SUPABASE_URL / SUPABASE_SERVICE_KEY eksik (.env — VDS'te çalıştırın)")
        sys.exit(1)
    if args.max_pages <= 0 or args.eszamanli <= 0:
        print("✗ --max-pages ve --eszamanli pozitif olmalı")
        sys.exit(1)

    if args.reset:
        for f in (CHECKPOINT_FILE, RETRY_QUEUE_FILE):
            try:
                os.remove(f)
            except FileNotFoundError:
                pass
        print("checkpoint ve yeniden-dene kuyruğu sıfırlandı")

    start = 0 if args.reset else args.start_skip
    asyncio.run(calis(args.max_pages, args.dry_run, start, args.eszamanli))


if __name__ == "__main__":
    main()
