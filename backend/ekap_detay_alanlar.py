# -*- coding: utf-8 -*-
"""
ekap_detay_alanlar.py — `GetByIhaleIdIhaleDetay` yanıtından ATILAN alanları `ilanlar`a yazar.

NEDEN (29 Tem denetimi): aynı detay yanıtı İKİ ayrı backfill tarafından çekiliyor ama
her biri yanıttan TEK alan alıp gerisini çöpe atıyordu:
  · ilan_metni_backfill.py   → yalnız `ilanList[0].veriHtml`
  · ekap_sonuc_backfill.py   → yalnız `sozlesmeBilgiList` + `ilanList`
Atılanlar (canlı yanıttan doğrulandı, 29 Tem — bkz. aşağıdaki ŞEKİL bloğu):
  item.eIhale · item.kismiIhale · item.ihaleKapsamAciklama · item.idareId ·
  item.ihtiyacKalemiOkasList · item.ihaleOzellikList ·
  ihaleBilgi.{okas, isinYapilacagiYer, ihaleYeri, itirazenSikayetBasvuruBedeli,
              istisnaUsulAciklama, iptalTarihi/Nedeni/Madde, ihaleTarihSaatList} ·
  idare.{telefon, fax, ustIdare, enUstIdareKod, enUstIdareAdi, il.adi, ilce.ilceAdi}
Ölçülen sonuç: `ilanlar.okas` %0,62 · kalem listesi %0,41 dolu — yani neredeyse tamamen boş,
oysa veri ZATEN çekilmiş yanıtın içindeydi. Bu modül SIFIR EK EKAP İSTEĞİ ile onu yazar.

── GERİYE DÖNÜK UYUMLULUK (migration uygulanmadan da çökmez) ───────────────────────────
Backfill'ler ÇALIŞIRKEN `git pull` yapılabildiği için kod, migration'ın uygulanmadığı
şemada da ayakta kalmak ZORUNDA. Üç katmanlı güvence:
  1. AÇILIŞTA TEK KEZ ŞEMA SAPTAMA — `kolonlari_sapta()` PostgREST'e adayların hepsini
     birden `select=` ile sorar; 42703 dönerse hata mesajındaki kolonu listeden düşürüp
     yeniden dener. Sonuç süreç ömrü boyunca önbelleklenir (ek istek yok).
  2. YAZIMDA DÜŞÜR-VE-TEKRAR-DENE — PATCH yine 42703 / PGRST204 alırsa (şema önbelleği
     bayat, migration yarıda kaldı vb.) suçlu kolon(lar) gövdeden atılıp yeniden denenir.
  3. ZORUNLU GÖVDE — çağıran `zorunlu=` ile ESKİ davranışın gövdesini verir
     (ör. {"ilan_metni": …}). Zenginleştirme her şeye rağmen yazılamazsa YALNIZ o gövde
     yazılır, yani eski davranış AYNEN sürer ve dönüş değeri değişmez.
Ayrıca None değerler gövdeden atılır → dolu bir alan asla NULL ile EZİLMEZ.

⚠️ `iptalTarihi/iptalNedeni` KOLONLARI DOLDURULUR ama `durum` alanına 'iptal' YAZILMAZ —
proje kararı: arayüz 'iptal' durumunu beklemiyor, yazılırsa 236.647 kayıt tüm sekmelerden
sessizce düşer. Durum dönüşümü arayüz hazır olunca ayrı iş olarak ele alınacak.

── CANLI YANIT ŞEKLİ (29 Tem, iki örnek: durum=5 sonuçlanmış + durum=2 açık) ────────────
item
├─ id · ikn · ihaleAdi · ihaleDurum · eIhale(bool) · ihaleUsul · ihaleKapsamAciklama
│  ('4734 Kapsamında' | 'İstisna')  · idareAdi · idareId('1996') · kismiIhale(bool)
├─ ihaleOzellikList[]      → [{ihaleOzellik: 'TENDER_DETAIL.IS_DENEYIM_BELGE'}, …]
├─ ihtiyacKalemiOkasList[] → [{adi, kodu, koduAdi}, …]
├─ ihaleBilgi{}
│    yasaKapsami4734 ('1'|'2') · ihaleKapsamAciklama (⚠️ BURADA i18n ANAHTARI döner,
│    item'daki çevrilmiş sürümü kullan) · ihaleTarihSaat · ihaleTipiAciklama ·
│    ihaleUsulAciklama · istisnaUsulAciklama ('4734 / 3-g') · isinYapilacagiYer ·
│    ihaleYeri · itirazenSikayetBasvuruBedeli · okas ('452132501 - …, 45251230 - …') ·
│    iptalTarihi · iptalNedeni · iptalMadde ·
│    ihaleTarihSaatList[] → [{ihaleTarihiEtiket:'DATASYNC.IHALE_TARIH_SAAT',
│                             ihaleTarihiEtiketDegeri:'11.12.2026 11:00'}, …]
│                            (YETERLIK_TARIH_SAAT / ILK_TEKLIF_ICIN_TARIH_SAAT de gelir)
├─ ilanList[]        → [{id, ilanTip('1'=ihale ilanı, '4'=sonuç ilanı), ilanTarihi,
│                        baslik, veriHtml, istekliAdi}, …]
├─ sozlesmeBilgiList[] (ekap_sonuc_backfill zaten okuyor)
└─ idare{}  id · adi · telefon · fax · ustIdare · enUstIdareKod · enUstIdareAdi
            · il{adi} · ilce{ilceAdi}
"""
import re

import httpx

from ekap_scraper import itiraz_parse, maliyet_araligi, mojibake_duzelt

# ── Kolon envanteri ─────────────────────────────────────────────────────────
# TEMEL: migration_* ile ÇOK ÖNCE eklenmiş, canlıda VAR olduğu doğrulanmış kolonlar
# (29 Tem PostgREST kontrolü). Bunlar migration'a bağlı DEĞİL → şema saptamasında
# "her hâlükârda dene" listesi. Yine de yazımda düşür-ve-tekrar-dene korumaları geçerli.
TEMEL_KOLONLAR = (
    "okas", "isin_yapilacagi_yer", "ihale_yeri", "kalemler",
    "teklif_elektronik", "teklif_kismi", "ihale_tarihi", "ilan_tarihi",
    "itiraz_bedeli", "yaklasik_maliyet_min", "yaklasik_maliyet_max",
)
# YENI: migration_ilanlar_detay_alanlari.sql ile gelir. Uygulanmadıysa sessizce düşürülür.
YENI_KOLONLAR = (
    "yasa_kapsami", "istisna_usul",
    "iptal_tarihi", "iptal_nedeni", "iptal_madde",
    "yeterlik_tarihi", "ilk_teklif_tarihi", "ihale_tarih_saatleri",
    "ihale_ozellikleri", "ekap_idare_id",
    "idare_telefon", "idare_faks", "ust_idare",
    "en_ust_idare_kod", "en_ust_idare_adi", "idare_il", "idare_ilce",
)
ADAY_KOLONLAR = TEMEL_KOLONLAR + YENI_KOLONLAR

# ihaleTarihSaatList etiketleri → kolon eşlemesi. Listede BUNLAR DIŞINDA bir etiket
# gelirse ham liste `ihale_tarih_saatleri` jsonb'ına düşer (bir daha veri atmayalım).
TARIH_ETIKET_KOLON = {
    "DATASYNC.IHALE_TARIH_SAAT": "ihale_tarihi",
    "DATASYNC.YETERLIK_TARIH_SAAT": "yeterlik_tarihi",
    "DATASYNC.ILK_TEKLIF_ICIN_TARIH_SAAT": "ilk_teklif_tarihi",
}

# yasaKapsami4734 kodu → okunur metin. YALNIZ item.ihaleKapsamAciklama i18n anahtarı
# olarak geldiğinde (Accept-Language başlığı düşmüşse) yedek olarak kullanılır.
YASA_KAPSAMI_KOD = {"1": "4734 Kapsamında", "2": "İstisna"}

_izinli_kolonlar = None   # süreç ömrü boyunca önbellek (None = henüz saptanmadı)


# ── Yardımcılar (ekap_sonuc_backfill.py'deki eşlerinin birebir davranışı) ────
def _metin(s):
    """Boşluk kırp + mojibake onar; boş dize → None (dolu alanı NULL'la ezmeyelim)."""
    if s is None:
        return None
    s = mojibake_duzelt(str(s)).strip()
    if not s or s == "-":
        return None
    return s


def _tarih_iso(s):
    """'11.12.2026 11:00' → '2026-12-11T11:00:00+03:00'. EKAP saatleri TR yereli."""
    if not s:
        return None
    s = str(s).strip()
    if re.match(r"^\d{4}-\d{2}-\d{2}", s):
        return s                      # zaten ISO (ilanList.ilanTarihi böyle geliyor)
    m = re.match(r"^(\d{1,2})\.(\d{1,2})\.(\d{4})(?:[ T](\d{1,2}):(\d{2}))?", s)
    if m:
        g, a, y, sa, dk = m.groups()
        return f"{y}-{int(a):02d}-{int(g):02d}T{int(sa or 0):02d}:{dk or '00'}:00+03:00"
    return None


def _bool(v):
    return v if isinstance(v, bool) else None


# ── Ayrıştırma: detay yanıtı → ilanlar gövdesi (SAF fonksiyon, ağ yok) ──────
def detay_ilan_alanlari(detay: dict) -> dict:
    """
    GetByIhaleIdIhaleDetay yanıtı → `ilanlar` PATCH gövdesi.
    None değerler zaten burada elenir: eldeki dolu veri NULL ile EZİLMEZ.
    ⚠️ `durum` ÜRETMEZ (iptal dönüşümü bilinçli olarak kapsam dışı — modül başlığına bak).
    """
    item = (detay or {}).get("item") or {}
    if not item:
        return {}
    bilgi = item.get("ihaleBilgi") or {}
    idare = item.get("idare") or {}

    g = {}

    # ── ihaleBilgi: işin/ihalenin kimliği ──────────────────────────────
    g["okas"] = _metin(bilgi.get("okas"))
    g["isin_yapilacagi_yer"] = _metin(bilgi.get("isinYapilacagiYer"))
    g["ihale_yeri"] = _metin(bilgi.get("ihaleYeri"))
    g["istisna_usul"] = _metin(bilgi.get("istisnaUsulAciklama"))

    # Yasa kapsamı: item'daki ÇEVRİLMİŞ metin ('İstisna'), ihaleBilgi'deki i18n anahtarı
    # ('TENDER_SEARCH.…LEGALSCOPE_EXCEPTION') DEĞİL. Anahtar gelirse koda düş.
    kapsam = _metin(item.get("ihaleKapsamAciklama"))
    if not kapsam or kapsam.startswith("TENDER_"):
        kapsam = YASA_KAPSAMI_KOD.get(str(bilgi.get("yasaKapsami4734") or "").strip())
    g["yasa_kapsami"] = kapsam

    # ── İptal bilgisi: KOLONLAR doldurulur, `durum` DEĞİŞTİRİLMEZ (proje kararı) ──
    g["iptal_tarihi"] = _tarih_iso(bilgi.get("iptalTarihi"))
    g["iptal_nedeni"] = _metin(bilgi.get("iptalNedeni"))
    g["iptal_madde"] = _metin(bilgi.get("iptalMadde"))

    # ── Tarih listesi: etiketli üç tarih + bilinmeyen etiket kalırsa ham liste ──
    bilinmeyen = []
    for t in (bilgi.get("ihaleTarihSaatList") or []):
        if not isinstance(t, dict):
            continue
        kolon = TARIH_ETIKET_KOLON.get((t.get("ihaleTarihiEtiket") or "").strip())
        iso = _tarih_iso(t.get("ihaleTarihiEtiketDegeri"))
        if kolon and iso:
            g[kolon] = iso
        elif iso:
            bilinmeyen.append(t)      # EKAP yeni etiket eklerse bir daha veri ATMAYALIM
    if bilinmeyen:
        g["ihale_tarih_saatleri"] = bilgi.get("ihaleTarihSaatList")
    g.setdefault("ihale_tarihi", _tarih_iso(bilgi.get("ihaleTarihSaat")))

    # ── Yapısal teklif türü: ilan_metni regex'inden (teklif_turu_parse.sql) DAHA GÜVENİLİR.
    #    O SQL yalnız 4 kolonun HEPSİ NULL olan satırlara dokunuyor → burada yazdığımız
    #    yapısal değer gece turunda geri EZİLMEZ.
    g["teklif_elektronik"] = _bool(item.get("eIhale"))
    g["teklif_kismi"] = _bool(item.get("kismiIhale"))

    # ── Kalem listesi (rakip "Malzeme Listesi (N)") + ihale özellikleri ──
    kalemler = item.get("ihtiyacKalemiOkasList")
    if kalemler:
        g["kalemler"] = kalemler
    ozellikler = [
        (o.get("ihaleOzellik") or "").replace("TENDER_DETAIL.", "").strip()
        for o in (item.get("ihaleOzellikList") or []) if isinstance(o, dict)
    ]
    ozellikler = [o for o in ozellikler if o]
    if ozellikler:
        g["ihale_ozellikleri"] = ozellikler

    # ── İtiraz bedeli → yaklaşık maliyet bandı. ekap_scraper bunun için AYRI bir
    #    endpoint (GetByIdItirazenSikayetBasvuruBedel) çağırıyor; oysa aynı değer
    #    ZATEN bu yanıtta — yani bedava. Yalnız ayrıştırılabildiyse yazılır.
    ib = itiraz_parse(_metin(bilgi.get("itirazenSikayetBasvuruBedeli")))
    if ib:
        mn, mx = maliyet_araligi(ib)
        g["itiraz_bedeli"] = ib
        g["yaklasik_maliyet_min"] = mn
        g["yaklasik_maliyet_max"] = mx
    # NOT: `tahmini_bedel` BİLİNÇLİ yazılmıyor — arayüzün bütçe alanı; DMO/Jandarma
    # gibi başka kaynaklardan gelmiş gerçek değeri türetilmiş bantla ezmeyelim.

    # ── İlan tarihi: YALNIZ ilanTip='1' (gerçek ihale ilanı) girdisinden.
    #    ⚠️ Sonuç ilanının (ilanTip='4') tarihi ilan_tarihi'ye YAZILMAZ — sonuç tarihi
    #    ilan tarihinden haftalar/aylar sonradır, veriyi çarpıtır (bkz. migration_etkin_tarih.sql).
    for il in (item.get("ilanList") or []):
        if isinstance(il, dict) and str(il.get("ilanTip") or "") == "1":
            iso = _tarih_iso(il.get("ilanTarihi"))
            if iso:
                g["ilan_tarihi"] = iso
            break

    # ── idare bloğu (kurumsal iletişim + hiyerarşi). idare adı zaten var; bunlar yeni. ──
    g["ekap_idare_id"] = _metin(item.get("idareId") or idare.get("id"))
    g["idare_telefon"] = _metin(idare.get("telefon"))
    g["idare_faks"] = _metin(idare.get("fax"))
    g["ust_idare"] = _metin(idare.get("ustIdare"))
    g["en_ust_idare_kod"] = _metin(idare.get("enUstIdareKod"))
    g["en_ust_idare_adi"] = _metin(idare.get("enUstIdareAdi"))
    g["idare_il"] = _metin((idare.get("il") or {}).get("adi"))
    g["idare_ilce"] = _metin((idare.get("ilce") or {}).get("ilceAdi"))

    return {k: v for k, v in g.items() if v is not None}


# ── Şema saptama (süreç başına TEK KEZ) ─────────────────────────────────────
def _mesajdaki_kolonlar(mesaj: str, adaylar) -> set:
    """
    Hata mesajında geçen ADAY kolon adlarını döndürür. PostgREST/PG metinleri farklı:
      select   → 'column ilanlar.yasa_kapsami does not exist'
      yazım    → "Could not find the 'yasa_kapsami' column of 'ilanlar' in the schema cache"
    ⚠️ Düz `in` ARAMASI YETMEZ: 'idare_il' → 'idare_ilce' mesajında da eşleşir ve masum
    kolonu düşürürdü. Kimlik sınırı (öncesi/sonrası tanımlayıcı karakteri olmayan) aranır.
    """
    m = (mesaj or "").lower()
    bulunan = set()
    for k in adaylar:
        if re.search(r"(?<![a-z0-9_])" + re.escape(k.lower()) + r"(?![a-z0-9_])", m):
            bulunan.add(k)
    return bulunan


def kolonlari_sapta(sb_url: str, headers: dict, adaylar=ADAY_KOLONLAR) -> set:
    """
    ADAY kolonlardan ŞU AN şemada var olanları saptar; sonucu önbellekler.
    Tek `select=` isteğiyle başlar; 42703 gelirse mesajdaki kolonu düşürüp tekrar dener
    (migration YARIM uygulanmış olsa da doğru sonucu verir).
    Ağ/kimlik hatasında GÜVENLİ tarafa düşer: yalnız TEMEL_KOLONLAR — yani eski davranış.
    """
    global _izinli_kolonlar
    if _izinli_kolonlar is not None:
        return _izinli_kolonlar

    kalan = list(adaylar)
    try:
        with httpx.Client(timeout=30.0) as c:
            for _ in range(len(adaylar) + 1):
                if not kalan:
                    break
                r = c.get(f"{sb_url}/rest/v1/ilanlar",
                          params={"select": ",".join(kalan), "limit": 1},
                          headers=headers)
                if r.status_code < 300:
                    break
                dus = _mesajdaki_kolonlar(r.text, kalan)
                if not dus:
                    # Beklenmedik hata (yetki/timeout) — zenginleştirmeyi kapatma,
                    # sadece migration'a bağlı olmayan TEMEL kolonlarla devam et.
                    print(f"    ⚠ şema saptama beklenmedik yanıt ({r.status_code}) — "
                          f"yalnız temel kolonlar kullanılacak: {r.text[:120]}")
                    kalan = [k for k in adaylar if k in TEMEL_KOLONLAR]
                    break
                kalan = [k for k in kalan if k not in dus]
    except Exception as e:
        print(f"    ⚠ şema saptama başarısız ({type(e).__name__}: {e}) — "
              "yalnız temel kolonlar kullanılacak")
        kalan = [k for k in adaylar if k in TEMEL_KOLONLAR]

    _izinli_kolonlar = set(kalan)
    yok = [k for k in adaylar if k not in _izinli_kolonlar]
    print(f"→ ilanlar zenginleştirme kolonları: {len(_izinli_kolonlar)}/{len(adaylar)} kullanılabilir"
          + (f" | ŞEMADA YOK (migration_ilanlar_detay_alanlari.sql uygulanmamış): {', '.join(yok)}" if yok else ""))
    return _izinli_kolonlar


def zenginlestirme_sifirla():
    """Test/yeniden saptama için önbelleği temizler."""
    global _izinli_kolonlar
    _izinli_kolonlar = None


# ── Yazım (düşür-ve-tekrar-dene + zorunlu gövde garantisi) ──────────────────
def ilan_alanlarini_yaz(sb_url: str, headers: dict, ilan_id: str, alanlar: dict,
                        zorunlu: dict | None = None, dry_run: bool = False) -> bool:
    """
    `ilanlar` satırını PATCH'ler. Döner: ZORUNLU gövdenin yazılıp yazılmadığı
    (zorunlu verilmediyse: en az bir şey yazıldı mı).

    GERİYE UYUM SÖZLEŞMESİ — çağıranın eski davranışı ASLA bozulmaz:
      · `alanlar` şemada olmayan kolon içeriyorsa 42703/PGRST204 alınır → suçlu kolon(lar)
        düşürülüp tekrar denenir; hangisinin suçlu olduğu anlaşılamazsa TÜM zenginleştirme
        alanları düşürülüp YALNIZ `zorunlu` yazılır.
      · `zorunlu` boş kalırsa ve zenginleştirme de yazılamıyorsa sessizce True döner
        (yazacak bir şey yok = hata değil).
    """
    izinli = kolonlari_sapta(sb_url, headers)
    zorunlu = dict(zorunlu or {})
    ek = {k: v for k, v in (alanlar or {}).items() if k in izinli and k not in zorunlu}
    govde = {**zorunlu, **ek}
    if not govde:
        return True

    if dry_run:
        print(f"    [DRY-RUN] ilanlar PATCH {ilan_id}: {len(zorunlu)} zorunlu + "
              f"{len(ek)} zenginleştirme alanı ({', '.join(sorted(ek)) or '—'})")
        return True

    with httpx.Client(timeout=30.0) as c:
        for deneme in range(3):
            r = c.patch(f"{sb_url}/rest/v1/ilanlar",
                        params={"id": f"eq.{ilan_id}"}, json=govde,
                        headers={**headers, "Prefer": "return=minimal"})
            if r.status_code < 300:
                return True
            # Kolon yok / şema önbelleği bayat → suçluyu düşür, yeniden dene.
            govde_kolon_hatasi = ("42703" in r.text or "PGRST204" in r.text
                                  or "does not exist" in r.text)
            if not govde_kolon_hatasi or deneme == 2:
                break
            dus = _mesajdaki_kolonlar(r.text, [k for k in govde if k not in zorunlu])
            if dus:
                # Bir daha denenmesin diye süreç önbelleğinden de çıkar.
                izinli.difference_update(dus)
                govde = {k: v for k, v in govde.items() if k not in dus}
            else:
                govde = dict(zorunlu)     # son çare: yalnız eski davranış
            if not govde:
                return True

        if r.status_code >= 300:
            print(f"    ✗ ilan alan yazma hatası ({ilan_id}): {r.status_code} {r.text[:140]}")
            if not zorunlu:
                return False
            # Zorunlu gövde HÂLÂ yazılmalı: zenginleştirme yüzünden eski davranış kaybolmasın.
            r2 = c.patch(f"{sb_url}/rest/v1/ilanlar",
                         params={"id": f"eq.{ilan_id}"}, json=zorunlu,
                         headers={**headers, "Prefer": "return=minimal"})
            if r2.status_code >= 300:
                print(f"    ✗ zorunlu yazma da başarısız ({ilan_id}): {r2.status_code} {r2.text[:120]}")
                return False
            return True
    return True
