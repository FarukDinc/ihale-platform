# -*- coding: utf-8 -*-
"""
İdare Türü sınıflandırıcı — ad kalıbından tür çıkarımı (GEÇİCİ katman).
========================================================================
MİMARİDEKİ YERİ (bkz. migration_idare_tur.sql):
  (a) OTORİTER kaynak = EKAP/DETSİS hiyerarşisi  → kaynak='ekap-detsis'
  (b) Boşluk dedektörü yeni/eşleşmeyen idareleri bulur
  (c) BU MODÜL = boşluk asla "sınıfsız" kalmasın diye geçici sınıflama
      → kaynak='kural'; resmî tazeleme gelince ÜZERİNE YAZILIR.

NEDEN TEK BAŞINA YETMEZ: EKAP'ta `idareAdi` çoğu zaman ALT BİRİM adıdır
("BİLGİ İŞLEM DAİRE BAŞKANLIĞI") — hangi kuruma ait olduğu addan anlaşılmaz.
Bu yüzden jenerik adlar bilinçli olarak 'bilinmiyor' döner; hiyerarşi bekler.

Kural tabanı 14 paralel ajanla çıkarıldı (741 anahtar kelime, 172 çakışma notu).
Kullanım:
    from idare_tur_siniflandir import idare_tur_belirle
    tur, guven = idare_tur_belirle("ANKARA BÜYÜKŞEHİR BELEDİYESİ FEN İŞLERİ D.BŞK.")
    # -> ('buyuksehir_belediye', 95)
"""
import json
import os
import re
import sys

try:
    sys.stdout.reconfigure(encoding="utf-8")   # Windows cp1254 konsolu
except Exception:
    pass

# ── Türkçe katlama — SQL tr_fold() ve JS trFold ile ÖZDEŞ olmalı ────────────
_HARF = str.maketrans("İIıŞşĞğÜüÖöÇç", "iiissgguuoocc")


def fold(s):
    """'ANKARA BÜYÜKŞEHİR' -> 'ankara buyuksehir' (noktalama tekil boşluğa)."""
    s = (s or "").translate(_HARF).lower()
    s = re.sub(r"[^a-z0-9]+", " ", s)
    return re.sub(r"\s+", " ", s).strip()


TURLER = {
    "buyuksehir_belediye": "Büyükşehir Belediyesi",
    "belediye":            "Belediye",
    "belediye_sirket":     "Belediye Şirketi",
    "su_kanal":            "Su ve Kanalizasyon İdaresi",
    "il_ozel_idare":       "İl Özel İdaresi",
    "saglik":              "Sağlık",
    "universite":          "Üniversite",
    "milli_egitim":        "Milli Eğitim",
    "bakanlik_merkez":     "Bakanlık (Merkez)",
    "bakanlik_tasra":      "Bakanlık (Taşra)",
    "kit":                 "KİT / Kamu Şirketi",
    "guvenlik":            "Güvenlik / Savunma",
    "yargi":               "Yargı / Ceza İnfaz",
    "diger_kamu":          "Diğer Kamu",
    "bilinmiyor":          "Bilinmiyor",
}

# ── ÖNCELİK SIRASI — çakışma notlarından türetildi ──────────────────────────
# Üstteki kazanır. Gerekçeler:
#  1 belediye_sirket : "İSPARK A.Ş." adında 'büyükşehir belediyesi' geçse bile
#                      sermaye şirketidir → bağlı idare sayılmaz.
#  2 il_ozel_idare   : büyükşehir ilinde bile kendi türüdür (2014 sonrası eski kayıtlar).
#  3 su_kanal        : İSKİ/ASKİ vb. büyükşehire bağlıdır ama ayrı tür olarak izlenir.
#  4 universite      : "üniversite hastanesi" hem sağlık hem üniversite görünür → üniversite.
#  5 yargi/guvenlik  : "adliye/cezaevi", "emniyet/jandarma" bakanlık taşrasından önce gelir.
#  6 saglik          : "il sağlık müdürlüğü" bakanlık taşrasından önce.
#  7 milli_egitim    : "ilçe MEM" bakanlık taşrasından önce.
#  8 buyuksehir → belediye : 'büyükşehir' token'i yoksa normal belediye.
#  9 kit             : TCDD/BOTAŞ vb. genel müdürlükler bakanlık merkezinden önce.
# 10 bakanlik_tasra → bakanlik_merkez → diger_kamu (en genel en sonda)
ONCELIK = [
    "belediye_sirket", "il_ozel_idare", "su_kanal", "universite",
    "yargi", "guvenlik", "saglik", "milli_egitim",
    "buyuksehir_belediye", "belediye", "kit",
    "bakanlik_tasra", "bakanlik_merkez", "diger_kamu",
]

# ── TUZAK KORUMASI (ajan bulgusu, kritik) ───────────────────────────────────
# Su idaresi kısaltmaları Türkçe katlanınca gündelik sözcüklerle çakışır:
#   ESKİ -> "eski" (sıfat!), ASKİ -> "aski", BASKI -> "baski" (matbaa işi!),
#   İSU -> "isu", MASKİ/SASKİ vb.
# Bunlar TEK BAŞINA asla eşleşmemeli; yanında kurumsal bağlam ŞART.
_KISALTMA_TUZAK = {
    "eski", "aski", "baski", "isu", "maski", "saski", "koski", "buski",
    "meski", "muski", "deski", "teski", "oski", "kaski", "vaski", "diski",
    "gaski", "suski", "asat", "ego", "iett", "eshot", "izsu", "iski", "tiski",
}
_SU_BAGLAM = ("genel mudurlugu", "su ve kanalizasyon", "su ve atiksu",
              "icmesuyu", "kanalizasyon idaresi", "buyuksehir")

# Şirket eki — belediye şirketini bağlı idareden ayırır
_SIRKET_EK = re.compile(r"\b(a s|as|anonim sirketi|limited sirketi|ltd sti|ltd|sti)\b")

# ── TAŞRA EKİ MERKEZİ EZER (20 Tem düzeltmesi) ──────────────────────────────
# ÖLÇÜLEN HATA: "KARAYOLLARI GENEL MÜDÜRLÜĞÜ 5. BÖLGE MÜDÜRLÜĞÜ" → bakanlik_merkez.
# Sebep: bakanlik_merkez.guclu içinde 'karayollari genel mudurlugu' var ve ad bunu
# alt-dize olarak İÇERİYOR; taşranın karşılık gelen kuralı ise 'karayollari n bolge
# mudurlugu' — literal "n" yer tutucusu, "5" ile asla eşleşmez. Güçlü kalıp döngüsü
# tüm türleri kapsadığı için merkez, taşranın zayıf ('anahtar') kalıbını yeniyor.
#
# Kural: bir ad hem merkez bir teşkilatı hem de YEREL bir birim ekini taşıyorsa,
# o kayıt o teşkilatın TAŞRA birimidir. Merkez teşkilatın kendisi bu eki taşımaz.
#
# ⚠️ Sadece bakanlik_merkez'e uygulanır. KİT'in bölge müdürlüğü (TCDD 3. Bölge)
# hâlâ KİT'tir — bakanlık taşrası değil, o yüzden kit listeye alınmadı.
# ⚠️ Sözcük sınırı ŞART: "sicil mudurlugu" alt-dize olarak "il mudurlugu" içerir.
# ⚠️ "sube mudurlugu" BİLEREK dışarıda — merkez teşkilatlarda da şube müdürlüğü var.
_TASRA_EK = re.compile(r"\b(bolge|il|ilce) mudurlugu\b")


def _tasra_ezmesi(tur, m):
    """Merkez sınıfı yerel birim eki taşıyorsa taşraya çevir."""
    if tur == "bakanlik_merkez" and _TASRA_EK.search(m):
        return "bakanlik_tasra"
    return tur


# ── ÜST KURUM ZİNCİRİ ANAHTAR SÖZCÜKTEN GÜÇLÜDÜR (20 Tem) ───────────────────
# EKAP adları "ÜST KURUM ... ALT BİRİM" biçiminde gelir. Alt birimin ÖZEL ADI
# başka bir kurumu andırabilir; bu ad, TÜR değil ANMA/BAĞIŞ bilgisidir:
#   "NİLÜFER İLÇE MEM ... ŞEHİT JANDARMA ER EYÜP GÜRSOY ORTAOKULU"  → okul (jandarma DEĞİL)
#   "DÜZCE İL MEM ... BAŞKENT ÜNİVERSİTESİ ... ANAOKULU"            → okul (üniversite DEĞİL)
#   "BARTIN İL MEM ... İL ÖZEL İDARESİ ... ANAOKULU"                → okul (İÖİ DEĞİL)
#   "BOZÜYÜK İLÇE MEM ... DEVLET HASTANESİ ANAOKULU"                → okul (hastane DEĞİL)
# Ölçüldü (20 Tem, 813K satırlık sınıfsız küme): 67 ad / 287 satır yanlış türe gidiyordu.
#
# Zincir işaretçisi tartışmasız üst kurum bildirir: MEB'e bağlı bir birim asla
# emniyet/jandarma teşkilatı olamaz. Bu yüzden EN YÜKSEK öncelikte kontrol edilir.
_UST_ZINCIR = (
    ("milli egitim mudurlugu", "milli_egitim"),
    ("il saglik mudurlugu",    "saglik"),
)


def _kurallari_yukle():
    """Ajan envanterini yükle (yanında idare_kurallar.json varsa oradan)."""
    yol = os.path.join(os.path.dirname(__file__), "idare_kurallar.json")
    if os.path.exists(yol):
        with open(yol, encoding="utf-8") as f:
            ham = json.load(f)
        out = {}
        for t in ham:
            out[t["kod"]] = {
                "guclu":   [fold(x) for x in t.get("guclu_kaliplar", []) if x],
                "anahtar": [fold(x) for x in t.get("anahtar_kelimeler", []) if x],
                "jenerik": {fold(x) for x in t.get("jenerik_risk", []) if x},
            }
        return out
    return {}


KURALLAR = _kurallari_yukle()
# Tüm türlerin jenerik-risk adları: bunlar TEK BAŞINA tür belirtmez
JENERIK = set()
for _v in KURALLAR.values():
    JENERIK |= _v["jenerik"]


# Kalıp → derlenmiş regex önbelleği. 1081 kalıp × on binlerce ad taranıyor;
# her çağrıda re.compile etmek kabul edilemez, bir kez derle sakla.
_KALIP_RE = {}


def _kalip_re(kalip):
    r = _KALIP_RE.get(kalip)
    if r is None:
        r = re.compile(r"\b" + re.escape(kalip) + r"\b")
        _KALIP_RE[kalip] = r
    return r


def _eslesir(metin, kalip):
    """
    Kalıp metinde SÖZCÜK OLARAK geçiyor mu.

    ⚠️ 20 Tem düzeltmesi — eskiden ham alt-dize (`kalip in metin`) bakılıyordu.
    Ölçülen iki gerçek hata:
      'a s'          → "satın ALMA Sube" içinde eşleşti → belediye_sirket (ONCELIK'te
                       BİRİNCİ olduğu için her şeyi çalıyordu; "ankara su" bile eşleşir)
      'il mudurlugu' → "sİCİL MÜDÜRLÜĞÜ" içinde eşleşti → bakanlik_tasra
    Kod zaten _KISALTMA_TUZAK için \b kullanıyordu; kalıpların tamamı aynı korumayı
    hak ediyor. Kalıplar fold() çıktısı olduğu için ([a-z0-9 ]) \b güvenli çalışır.
    """
    if not kalip:
        return False
    # tek sözcüklük riskli kısaltma → kurumsal bağlam AYRICA şart
    if kalip in _KISALTMA_TUZAK and not any(b in metin for b in _SU_BAGLAM):
        return False
    return _kalip_re(kalip).search(metin) is not None


def idare_tur_belirle(ad):
    """
    İdare adından tür çıkar.
    Dönüş: (tur_kodu, guven 0-100). Karar verilemezse ('bilinmiyor', 0).
    Jenerik alt birim adları ('bilgi islem daire baskanligi') BİLİNÇLİ olarak
    'bilinmiyor' döner — hiyerarşi (ekap-detsis) doldurmalı.
    """
    m = fold(ad)
    if not m:
        return ("bilinmiyor", 0)

    # 0) Üst kurum zinciri — alt birimin özel adı yanıltıcı olabilir, zincir olamaz
    for anahtar, tur in _UST_ZINCIR:
        if anahtar in m:
            return (tur, 95)

    # Şirket eki varsa ve belediye bağlamı da varsa → belediye şirketi (en yüksek öncelik)
    if _SIRKET_EK.search(m) and ("belediye" in m or "buyuksehir" in m):
        return ("belediye_sirket", 90)

    # 1) GÜÇLÜ kalıplar — öncelik sırasına göre ilk eşleşen kazanır
    for tur in ONCELIK:
        k = KURALLAR.get(tur)
        if not k:
            continue
        for kalip in k["guclu"]:
            if _eslesir(m, kalip):
                return (_tasra_ezmesi(tur, m), 95)

    # 2) NORMAL anahtar kelimeler — yine öncelik sırasıyla
    for tur in ONCELIK:
        k = KURALLAR.get(tur)
        if not k:
            continue
        for kalip in k["anahtar"]:
            if _eslesir(m, kalip):
                return (_tasra_ezmesi(tur, m), 75)

    # 3) Yalnızca jenerik bir alt birim adıysa: karar VERME (hiyerarşi gerekli)
    if m in JENERIK or any(j and j in m for j in JENERIK):
        return ("bilinmiyor", 0)

    return ("bilinmiyor", 0)


def ozet(adlar):
    """Liste için kapsama raporu — {tur: adet} + eşleşmeyen örnekler."""
    from collections import Counter
    say, esz = Counter(), []
    for a in adlar:
        t, g = idare_tur_belirle(a)
        say[t] += 1
        if t == "bilinmiyor" and len(esz) < 50:
            esz.append(a)
    toplam = sum(say.values()) or 1
    return {
        "toplam": toplam,
        "kapsama_yuzde": round(100.0 * (toplam - say["bilinmiyor"]) / toplam, 1),
        "dagilim": dict(say.most_common()),
        "eslesmeyen_ornek": esz,
    }


if __name__ == "__main__":
    ornekler = [
        "ANKARA BÜYÜKŞEHİR BELEDİYESİ FEN İŞLERİ DAİRESİ BAŞKANLIĞI",
        "KEÇİÖREN BELEDİYESİ FEN İŞLERİ MÜDÜRLÜĞÜ",
        "İSPARK A.Ş. İSTANBUL BÜYÜKŞEHİR BELEDİYESİ",
        "İSTANBUL SU VE KANALİZASYON İDARESİ GENEL MÜDÜRLÜĞÜ (İSKİ)",
        "KONYA İL ÖZEL İDARESİ",
        "ANKARA ETLİK ŞEHİR HASTANESİ",
        "HACETTEPE ÜNİVERSİTESİ REKTÖRLÜĞÜ",
        "İSTANBUL İL MİLLİ EĞİTİM MÜDÜRLÜĞÜ",
        "TCDD İŞLETMESİ GENEL MÜDÜRLÜĞÜ",
        "BİLGİ İŞLEM DAİRE BAŞKANLIĞI",          # jenerik → bilinmiyor beklenir
        "ESKİ MOBİLYA ALIMI MÜDÜRLÜĞÜ",           # 'eski' tuzağı → su_kanal OLMAMALI
    ]
    print(f"kural tabani: {len(KURALLAR)} tur, jenerik: {len(JENERIK)}\n")
    for a in ornekler:
        t, g = idare_tur_belirle(a)
        print(f"  {TURLER.get(t, t):<28} ({g:>3}) ← {a[:62]}")
