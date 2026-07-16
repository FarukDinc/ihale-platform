# -*- coding: utf-8 -*-
"""
kategori_siniflandir.py — İhale kategorisi sınıflandırıcı (ihaleciler.com tarzı ~40 iş-dostu kategori).

Önceki sistem: OKAS'ın İLK 2 HANESİNDEN (CPV bölümü) 44 ham AB-tarzı kategori türetiyordu ve
OKAS'sız ~%39 ihale jenerik "Mal/Hizmet Alımı" kovasına düşüyordu (bilgisiz).

Yeni sistem: OKAS AÇIKLAMASI (kod - Türkçe açıklama; ör. "45232120 - Sulama tesis ve yapıları")
+ ihale BAŞLIĞI üzerinde Türkçe-katlanmış ANAHTAR KELİME eşleştirmesi. Daha isabetli + OKAS'sız
ihaleleri de gerçek sektöre atar. Kurallar SIRAYLA denenir (özel → genel); ilk eşleşen kazanır.

Hem ekap_scraper.py (yeni veri) hem kategori_backfill.py (mevcut veriyi yeniden hesapla) kullanır.
"""

import re


def _fold(s):
    """Türkçe-duyarsız katlama (trFold ile aynı): İ/I/ı→i, Ş→s, Ğ→g, Ü→u, Ö→o, Ç→c + lower."""
    if not s:
        return ""
    return (s.replace("İ", "i").replace("I", "i").replace("ı", "i")
             .replace("Ş", "s").replace("ş", "s")
             .replace("Ğ", "g").replace("ğ", "g")
             .replace("Ü", "u").replace("ü", "u")
             .replace("Ö", "o").replace("ö", "o")
             .replace("Ç", "c").replace("ç", "c")
             .lower())


# (kategori adı, [anahtar kelimeler]) — SIRA ÖNEMLİ: daha spesifik olan önce.
# Anahtar kelimeler zaten katlanmış (fold) yazılır; girdi de katlanıp aranır (substring).
_KURALLAR = [
    ("Hazır Yemek - Lokantacılık", [
        "hazir yemek", "malzemeli yemek", "malzemesiz yemek", "yemek pisirme", "tabldot",
        "yemek hizmet", "catering", "lokanta", "mutfak hizmet", "yemek dagitim", "kumanya",
        "ogle yemegi", "sicak yemek", "yemek verilmesi",
    ]),
    ("Tıbbi Cihaz - Laboratuvar - Hastane Ekipmanları", [
        "tibbi cihaz", "tibbi demirbas", "laboratuvar", "hastane ekipman", "tomografi", "rontgen",
        "ultrason", "mikroskop", "reaktif", "test kiti", "analiz cihaz", "diyaliz", "steril",
        "otoklav", "santrifuj", "elektrokardiyograf", "defibrilator", "hasta basi", "medikal cihaz",
        "goruntuleme sistem", "anestezi cihaz", "ventilator", "biyokimya", "hemogram", "laparoskopi", "endoskopi", "olcer cihaz", "olcum cihaz",
    ]),
    ("Sağlık - Medikal - İlaç - Kozmetik", [
        "ilac", "medikal", "tibbi malzeme", "tibbi sarf", "kozmetik", "serum", "asi", "farmasotik",
        "eczane", "saglik malzeme", "enjektor", "eldiven", "maske", "pansuman", "sarf malzeme",
        "protez", "ortez", "dis malzeme", "kan urun", "diyaliz solusyon",
    ]),
    ("Yangın Algılama - Söndürme", [
        "yangin", "sondurme", "yangin algilama", "yangin tup", "sprinkler", "yangin ihbar",
        "yangin dolabi", "yangin sistem", "davlumbaz sondurme",
    ]),
    ("Asansör - Yapı Otomasyon - Mekanik Güvenlik", [
        "asansor", "yuruyen merdiven", "yapi otomasyon", "mekanik guvenlik", "bariyer", "turnike",
        "otomatik kapi", "yuruyen bant",
    ]),
    ("Klima - Soğutma - Isıtma - Havalandırma", [
        "klima", "sogutma", "isitma", "havalandirma", "kombi", "kalorifer", "kazan dair", "fan coil",
        "split klima", "chiller", "iklimlendirme", "vrf", "radyator", "brulor", "sicak su kazan",
    ]),
    ("Uydu Takip - Kamera - Scada - Haberleşme", [
        "guvenlik kamera", "kamera sistem", "cctv", "scada", "haberlesme sistem", "uydu takip",
        "plaka tanima", "telsiz", "arac takip", "gps takip", "kgys", "kent guvenlik",
    ]),
    ("Yazılım - Bilişim - Bilgi Yönetim", [
        "yazilim", "bilisim", "bilgi yonetim", "yazilim gelistirme", "yazilim lisans", "veritabani",
        "lisans yenileme", "lisans alimi",
        "web sitesi", "web tabanli", "uygulama gelistirme", "otomasyon yazilim", "mobil uygulama",
        "bulut", "siber guvenlik", "e-belediye", "bilgi sistem",
    ]),
    ("Elektronik - Bilgisayar - İletişim - Ölçü Aletleri", [
        "bilgisayar", "dizustu", "masaustu", "yazici", "tarayici", "sunucu", "server", "monitor",
        "tablet", "projeksiyon", "olcu alet", "elektronik kart", "network cihaz", "switch", "router",
        "ups", "kesintisiz guc", "barkod", "elektronik malzeme", "anakart", "harddisk",
        "ag anahtari", "omurga ag",
    ]),
    ("Enerji - Aydınlatma - Sinyalizasyon - Elektrik Tesisatı", [
        "elektrik tesisat", "aydinlatma", "sinyalizasyon", "trafo", "enerji nakil", "elektrik malzeme",
        "armatur", "aydinlatma diregi", "kablo", "jenerator", "elektrik pano", "og hucre", "ag pano",
        "sokak aydinlatma", "led aydinlatma", "elektrik sebeke", "enerji verimli",
    ]),
    ("Kanalizasyon - Boru - Su - Doğalgaz - Sıhhi Tesisat", [
        "kanalizasyon", "icme suyu", "atiksu", "sihhi tesisat", "dogalgaz", "su tesisat", "boru dose",
        "boru hatti", "icmesuyu", "kanal insaat", "foseptik", "aritma tesis", "su deposu",
        "terfi merkez", "isale hatti", "kanal aci", "pissu", "sulama borusu", "klorlama",
    ]),
    ("Ormancılık - Bahçıvanlık - Peyzaj", [
        "peyzaj", "agaclandirma", "fidan", "bahcivan", "ormancilik", "budama", "cim", "park bahce",
        "yesil alan", "orman", "sulama sistem", "cicek", "bitkilendirme", "mesire",
    ]),
    ("Kent Mobilyaları - Prefabrik - Doğramacılık", [
        "kent mobilya", "prefabrik", "dograma", "pvc dograma", "aluminyum dograma", "konteyner",
        "park mobilya", "oyun grubu", "spor aleti", "pergole", "cardak", "otobus duragi",
    ]),
    ("İnşaat - Altyapı - Üstyapı - Yapım", [
        "insaat", "yapim isi", "yapim ihale", "onarim", "tadilat", "bina yap", "yol yap", "asfalt",
        "beton", "kaldirim", "altyapi", "ustyapi", "yikim", "restorasyon", "kaba yapi", "ince yapi",
        "cati onarim", "duvar", "bordur", "parke tas", "parke tasi", "menfez", "kopru", "istinat", "sicak asfalt",
        "yol yapim", "sanat yapi", "spor salon insa", "derslik", "kilitli parke",
    ]),
    ("İnşaat Malzemeleri", [
        "insaat malzeme", "hazir beton", "cimento", "demir celik", "insaat demir", "agrega", "kum cakil",
        "tuvenan", "micir", "kirmatas", "yapi malzeme", "insaat celigi", "bims", "tugla",
    ]),
    ("Akaryakıt - Gazyakıt - Madeni Yağ", [
        "akaryakit", "motorin", "benzin", "lpg", "madeni yag", "gazyakit", "yakit alim", "dizel",
        "kursunsuz benzin", "fuel oil", "kalorifer yakit",
    ]),
    ("Odun - Kömür - Katıyakıt", [
        "odun", "komur", "katiyakit", "linyit", "yakacak", "tas komur", "ithal komur", "kok komur",
    ]),
    ("Madencilik - Sondaj - Doğal Kaynaklar", [
        "madencilik", "sondaj", "maden ocak", "kuyu acma", "jeolojik", "jeotermal", "kaya delme",
    ]),
    ("Kimyasal Maddeler - Dezenfektan - Gübre", [
        "kimyasal", "dezenfektan", "gubre", "asit", "kimyevi", "cozelti", "klor", "polielektrolit", "biyosidal",
        "arac yikama kimyasal", "havuz kimyasal", "cinko", "kukurt", "oksit", "granul",
        "kaustik", "sulfat", "sodyum",
    ]),
    ("Gıda - Tarım Ürünleri - Yiyecek - İçecek", [
        "gida", "yiyecek", "icecek", "et alim", "sut ", "ekmek", "sebze", "meyve", "tavuk", "pilic",
        "un alim", "seker", "bakliyat", "kuru gida", "yumurta", "zeytin", "cay ", "peynir", "yogurt", "bugday",
        "makarna", "pirinc", "bulgur", "salca", "dondurulmus gida", "balik alim", "yufka", "boreklik", "kuru uzum",
    ]),
    ("Tekstil - Giyim - Spor Ekipmanları", [
        "tekstil", "giyim", "kiyafet", "elbise", "ayakkabi", "spor ekipman", "kumas", "uniforma",
        "is elbisesi", "battaniye", "nevresim", "havlu", "carsaf", "montu", "bot ", "esofman",
    ]),
    ("Mobilya - Beyaz Eşya - Mutfak - Züccaciye", [
        "mobilya", "beyaz esya", "zuccaciye", "buzdolabi", "camasir makine", "bulasik makine",
        "masa sandalye", "okul sirasi", "dolap ", "mutfak esya", "yatak ", "koltuk", "mefrusat",
    ]),
    ("Matbaa - Kırtasiye - Toner - Kartuş - Ambalaj", [
        "matbaa", "kirtasiye", "toner", "kartus", "ambalaj", "fotokopi kagit", "baski hizmet",
        "kagit alim", "defter", "afis baski", "brosur", "form baski", "zarf",
        "buro malzemesi", "buro malzeme",
    ]),
    ("Taşıt - İş Makinesi - Yedek Parça", [
        "tasit kirala", "arac kirala", "is makinesi", "yedek parca", "kamyon", "otobus alim",
        "ekskavator", "arac lastik", "kepce", "greyder", "silindir", "binek arac", "arac alim",
        "traktor", "damper", "vinc", "forklift", "arac bakim onarim", "arac muayene", "lastik", "aku",
        "arac kiralama", "tasit kiralama", "arac kiralanmasi", "soforlu arac", "suruculu arac",
    ]),
    ("Nakliye - Servis - Taşımacılık", [
        "nakliye", "tasimacilik", "personel tasima", "ogrenci tasima", "kargo", "tasima hizmet",
        "servis hizmet", "yolcu tasima", "yuk tasima",
        # 16 Tem: 67K "Diğer" başlık frekans analizi — taşımalı eğitim ihaleleri çekim ekleri
        # yüzünden kaçıyordu ("öğrencilerin taşınmaSI", "taşımaLI eğitim"); \b tam-kelime
        # eşleşmesinde her çekim ayrı kelime olarak listelenmeli.
        "tasinmasi", "tasimali", "tasima merkezi", "tasima isi", "arac gunu", "hat arac",
        "servis araci", "tasinma",
    ]),
    ("Özel Güvenlik - Koruma - Bekçilik", [
        "ozel guvenlik", "guvenlik hizmet", "koruma hizmet", "bekcilik", "guvenlik gorevli",
        "silahli guvenlik", "silahsiz guvenlik",
    ]),
    ("Temizlik - İlaçlama - Geri Dönüşüm", [
        "temizlik hizmet", "temizlik malzeme", "ilaclama", "geri donusum", "hasere", "cevre temizlik",
        "atik toplama", "cop toplama", "genel temizlik", "ted. temizlik", "kati atik",
    ]),
    ("Endüstriyel Makine - Motor - Konveyör", [
        "endustriyel makine", "konveyor", "makine alim", "tezgah", "pres makine", "kompresor",
        "hidrolik", "elektrik motor", "reduktor", "pompa alim", "santral makine", "vana", "valf",
        "cekvalf", "filtre", "toz tutma", "turbin", "rulman", "conta", "sanzuman", "servo",
    ]),
    ("Hırdavat - Nalburiye - Metal ve Plastik", [
        "hirdavat", "nalburiye", "civata", "somun", "metal urun", "plastik urun", "sac levha",
        "profil demir", "vida", "el aleti", "alet edevat", "boya alim", "izolasyon malzeme",
        "kelepce", "halat", "zincir", "muhtelif malzeme", "dokum malzeme", "dovme",
    ]),
    ("Savunma Sanayi - Silah - Denizcilik - Havacılık", [
        "savunma", "silah alim", "muhimmat", "denizcilik", "havacilik", "askeri malzeme", "gemi alim",
        "ucak alim", "insansiz hava", "fisek", "atis",
    ]),
    ("İş Sağlığı - İş Güvenliği ve Ekipmanları", [
        "is sagligi", "is guvenligi", "kkd", "koruyucu ekipman", "baret", "is guvenligi malzeme",
        "emniyet kemer", "gaz maske", "is guvenligi hizmet",
    ]),
    ("Hayvancılık - Veterinerlik - Hayvan Yemi", [
        "hayvancilik", "veteriner", "hayvan yemi", "buyukbas", "kucukbas", "yem alim", "kaba yem",
        "suni tohumlama", "damizlik", "arilik", "hayvan sagligi",
    ]),
    ("Mühendislik - Mimarlık - Danışmanlık", [
        "muhendislik hizmet", "mimarlik", "danismanlik", "proje hazirla", "etut proje", "musavirlik",
        "kontrollük", "harita muhendis", "aplikasyon", "zemin etut", "cizim hizmet", "mimari proje", "fikir projesi", "kentsel tasarim", "fikir yaris", "mimari fikir",
    ]),
    ("Eğitim - Araştırma - Anket - Tercümanlık", [
        "egitim hizmet", "arastirma hizmet", "anket", "tercuman", "kurs hizmet", "seminer", "ceviri",
        "egitim organizasyon", "sertifika programi",
    ]),
    ("Turizm - Organizasyon - Ödüllendirme", [
        "turizm", "organizasyon hizmet", "konaklama", "otel hizmet", "gezi", "fuar", "toplanti organiz",
        "tanitim organizasyon", "odul toren",
    ]),
    ("Reklam - Tabela - Billboard - Tanıtım", [
        "reklam", "tabela", "billboard", "tanitim materyal", "afis", "promosyon", "totem", "led ekran",
        "dijital reklam", "raket pano",
    ]),
    ("Sigortacılık - Mali ve Hukuki Hizmetler", [
        "sigorta", "mali hizmet", "hukuki hizmet", "muhasebe hizmet", "denetim hizmet", "avukatlik",
        "arac sigorta", "kasko", "aktueryal", "mali sorumluluk", "zorunlu mali", "trafik sigorta",
    ]),
    ("Sanat Eserleri - Müzik Aletleri - Heykel", [
        "sanat eser", "muzik aleti", "heykel", "maket", "enstruman", "piyano", "muzik seti",
    ]),
    ("Menkul Mallar - Araç ve Hurda Satışı", [
        "hurda satis", "hurda alim", "menkul mal satis", "arac satis", "olu demirbas", "hurda arac",
        "ekonomik omrunu", "atik satis",
    ]),
    ("Gayrimenkul - Arsa Satışı - Kantin", [
        "gayrimenkul", "arsa satis", "tasinmaz satis", "isyeri kira", "kantin", "kiraya verilecek",
        "kira ihale", "bufe kira", "tasinmaz kira", "arsa kira", "yer tahsis",
    ]),
    ("İşletmecilik - İşçilik - Sosyal Hizmetler", [
        "iscilik hizmet", "isletmecilik", "sosyal hizmet", "personel calistir", "isci temin",
        "destek personel", "hizmet alimi personel",
    ]),
]

# DMO'nun KENDİ kategori adları → kanonik (dmo_scraper kullanır; başlık-kelime tahmininden
# daha güvenilir olduğundan ÖNCE denenir). Jenerik olanlar ("Diğer İhale İlanları",
# "Aydınlatma ve Temizlik Malzemeleri" gibi karışık kovalar) BİLEREK yok — başlığa düşer.
DMO_KATEGORI_MAP = {
    "Bilgisayar ve Yan Ürünleri":              "Elektronik - Bilgisayar - İletişim - Ölçü Aletleri",
    "Büro Makine ve Aletleri":                 "Elektronik - Bilgisayar - İletişim - Ölçü Aletleri",
    "Diğer Büro Makina ve Teçhizatı":          "Elektronik - Bilgisayar - İletişim - Ölçü Aletleri",
    "Bilgisayar Paket Programları":            "Yazılım - Bilişim - Bilgi Yönetim",
    "Tıbbi Cihaz ve Laboratuvar Malzemeleri":  "Tıbbi Cihaz - Laboratuvar - Hastane Ekipmanları",
    "İlaçlar":                                 "Sağlık - Medikal - İlaç - Kozmetik",
    "Nakil Vasıtalar":                         "Taşıt - İş Makinesi - Yedek Parça",
    "Büro Mefruşatı":                          "Mobilya - Beyaz Eşya - Mutfak - Züccaciye",
    "Kırtasiye Malzemeleri":                   "Matbaa - Kırtasiye - Toner - Kartuş - Ambalaj",
    "Temizlik Malzemeleri":                    "Temizlik - İlaçlama - Geri Dönüşüm",
    "Giyim ve Tekstil Ürünleri":               "Tekstil - Giyim - Spor Ekipmanları",
    "Mobilya":                                 "Mobilya - Beyaz Eşya - Mutfak - Züccaciye",
}


# OKAS yoksa/eşleşmezse CPV ilk-2-hane fallback (eski _CPV_KATEGORI'nin yeni isimlere haritası).
_CPV2_FALLBACK = {
    "03": "Hayvancılık - Veterinerlik - Hayvan Yemi", "09": "Akaryakıt - Gazyakıt - Madeni Yağ",
    "14": "Madencilik - Sondaj - Doğal Kaynaklar", "15": "Gıda - Tarım Ürünleri - Yiyecek - İçecek",
    "16": "Endüstriyel Makine - Motor - Konveyör", "18": "Tekstil - Giyim - Spor Ekipmanları",
    "22": "Matbaa - Kırtasiye - Toner - Kartuş - Ambalaj", "24": "Kimyasal Maddeler - Dezenfektan - Gübre",
    "30": "Elektronik - Bilgisayar - İletişim - Ölçü Aletleri", "31": "Enerji - Aydınlatma - Sinyalizasyon - Elektrik Tesisatı",
    "32": "Uydu Takip - Kamera - Scada - Haberleşme", "33": "Tıbbi Cihaz - Laboratuvar - Hastane Ekipmanları",
    "34": "Taşıt - İş Makinesi - Yedek Parça", "35": "Savunma Sanayi - Silah - Denizcilik - Havacılık",
    "37": "Sanat Eserleri - Müzik Aletleri - Heykel", "38": "Tıbbi Cihaz - Laboratuvar - Hastane Ekipmanları",
    "39": "Mobilya - Beyaz Eşya - Mutfak - Züccaciye", "41": "Kanalizasyon - Boru - Su - Doğalgaz - Sıhhi Tesisat",
    "42": "Endüstriyel Makine - Motor - Konveyör", "43": "Endüstriyel Makine - Motor - Konveyör",
    "44": "İnşaat Malzemeleri", "45": "İnşaat - Altyapı - Üstyapı - Yapım", "48": "Yazılım - Bilişim - Bilgi Yönetim",
    "50": "Taşıt - İş Makinesi - Yedek Parça", "51": "Endüstriyel Makine - Motor - Konveyör",
    "55": "Hazır Yemek - Lokantacılık", "60": "Nakliye - Servis - Taşımacılık", "63": "Nakliye - Servis - Taşımacılık",
    "64": "Uydu Takip - Kamera - Scada - Haberleşme", "66": "Sigortacılık - Mali ve Hukuki Hizmetler",
    "70": "Gayrimenkul - Arsa Satışı - Kantin", "71": "Mühendislik - Mimarlık - Danışmanlık",
    "72": "Yazılım - Bilişim - Bilgi Yönetim", "73": "Eğitim - Araştırma - Anket - Tercümanlık",
    "75": "İşletmecilik - İşçilik - Sosyal Hizmetler", "77": "Ormancılık - Bahçıvanlık - Peyzaj",
    "79": "İşletmecilik - İşçilik - Sosyal Hizmetler", "80": "Eğitim - Araştırma - Anket - Tercümanlık",
    "85": "Sağlık - Medikal - İlaç - Kozmetik", "90": "Temizlik - İlaçlama - Geri Dönüşüm",
    "92": "Turizm - Organizasyon - Ödüllendirme", "98": "İşletmecilik - İşçilik - Sosyal Hizmetler",
}


# Kelime-sınırı (\b) ile eşleştir: kısa kelimeler ("asi") "taşıma" içinde YANLIŞ eşleşmesin.
# Her kategori için tek birleşik regex (performans — backfill 167K satır).
_DERLENMIS = [
    (kategori, re.compile(r"\b(?:" + "|".join(re.escape(kw.strip()) for kw in kelimeler) + r")\b"))
    for kategori, kelimeler in _KURALLAR
]


# ── Kanonik kategori kümesi (js/kategoriler.js ile BİREBİR — site filtresi/harita/bildirim bunu kullanır).
# AI sınıflandırıcı (ai_kategori_backfill.py) buradan numaralı liste üretir; AI'ın döndürdüğü NUMARA
# bu tuple'daki dizinle eşlenir → yazılan değer daima geçerli bir filtre seçeneği olur (serbest metin DEĞİL).
KANONIK_KATEGORILER = tuple(sorted({k for k, _ in _KURALLAR}))
# Güvenlik: her kural hedefi (ve DMO/CPV eşleme değerleri) kanonik kümede olmalı — sessiz drift yakalanır.
assert set(DMO_KATEGORI_MAP.values()) <= set(KANONIK_KATEGORILER), "DMO_KATEGORI_MAP kanonik dışı değer içeriyor"
assert set(_CPV2_FALLBACK.values()) <= set(KANONIK_KATEGORILER), "_CPV2_FALLBACK kanonik dışı değer içeriyor"
# js/kategoriler.js'teki 41 kanonik adla SAYICA eşleşmeli (bu dosya o listeyi ÜRETMİYOR, elle senkron
# tutulur — bkz. kategori_siniflandir.py başlığı). Bu assertion yalnız EKLEME/SİLME driftini yakalar;
# bir kategori js'te BAŞKA adla yeniden adlandırılırsa (rename) bu sessiz kalır — o durumda AI'ın/
# ekap_scraper'ın yazdığı yeni ad site filtresinde seçenek olarak görünmez (16 Tem incelemesinde bulundu;
# tam çözüm: 41 adı iki dile de tek bir paylaşılan kaynaktan okutmak — şimdilik ucuz kısmi önlem).
assert len(KANONIK_KATEGORILER) == 41, f"KANONIK_KATEGORILER {len(KANONIK_KATEGORILER)} — js/kategoriler.js ile senkron mu kontrol et"

# Jenerik/boş kovalar: kategori_belirle bir satırı yalnızca bunlardan biriyse 'Diğer'e çekebilir; ZATEN
# spesifik (AI ya da kelime ile atanmış) bir kategoriyi 'Diğer'e geri EZMEZ (backfill idempotent + AI-korur).
JENERIK_KOVALAR = frozenset({
    None, "", "Diğer",
    "Mal Alımı", "Hizmet Alımı", "Mal", "Hizmet",         # eski jenerik EKAP etiketleri
    "İnşaat & Yapım",                                       # eski kısa ad (kanonik "İnşaat - Altyapı..." değil)
})


def kategori_belirle(okas, tur=None, baslik=None):
    """OKAS açıklaması + başlıktan iş-dostu kategori türet. Eşleşme yoksa CPV-2 fallback, sonra tür."""
    metin = _fold(f"{okas or ''} {baslik or ''}")
    if metin.strip():
        for kategori, rx in _DERLENMIS:
            if rx.search(metin):
                return kategori
    # CPV ilk-2-hane fallback (OKAS varsa)
    if okas:
        prefix = "".join(filter(str.isdigit, okas))[:2]
        if prefix in _CPV2_FALLBACK:
            return _CPV2_FALLBACK[prefix]
    # Son çare: ihale türü
    t = _fold(tur or "")
    if "yapim" in t:
        return "İnşaat - Altyapı - Üstyapı - Yapım"
    if "danismanlik" in t:
        return "Mühendislik - Mimarlık - Danışmanlık"
    return "Diğer"


if __name__ == "__main__":
    ornekler = [
        ("15112130 - Piliçler , 03221240 - Domatesler", "Mal", "4 KISIM MUHTELİF GIDA MALZEMELERİ"),
        ("45232120 - Sulama tesis ve yapıları", "Yapım", "Tarımsal Sulama"),
        ("72212781 - Sistem yönetimi yazılım geliştirme", "Hizmet", "Mevcut Harita Yazılımı Geliştirme"),
        ("79710000 - Güvenlik hizmetleri", "Hizmet", "SAMSUN BÖLGE ÖZEL GÜVENLİK"),
        (None, "Hizmet", "Öğrenci taşıma hizmeti alınacaktır"),
        (None, "Mal", "Dekoratif yol aydınlatma direği satın alınacaktır"),
        (None, "Yapım", "Yol yapım işleri ihale edilecek"),
        (None, "Hizmet", "Malzemeli yemek hizmeti alınacaktır"),
        ("33141110 - Yara bandı", "Mal", "Tıbbi sarf malzeme"),
    ]
    for okas, tur, baslik in ornekler:
        print(f"{kategori_belirle(okas, tur, baslik):50s} <- {(baslik or '')[:45]}")
