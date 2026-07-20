"""
İhale Şartname Analizörü - Tam Versiyon
- Metin PDF: pdfplumber → Gemini text
- Taranmış PDF: Gemini Vision (File API)
- Dinamik kredi sistemi
- Kırmızı alarm motoru
- Güvenli JSON parse

Kurulum:
    pip install google-genai pdfplumber requests python-dotenv

Kullanım:
    GEMINI_API_KEY=xxx python analyzer.py

SDK: google-genai (Backlog #34). Eski google.generativeai bırakıldı — "support ended"
durumdaydı ve File API'si canlıda kırıktı (bkz. taranmis_pdf_analiz_et notu).
"""

import os
import json
import re
import time
import tempfile
import zipfile
import requests
import pdfplumber
from pathlib import Path
from dotenv import load_dotenv
from google.genai import types

from gemini_ortak import VARSAYILAN_MODEL, gemini_hata_logla, istemci_al, yanit_metni

load_dotenv()

# ── Yapılandırma ──────────────────────────────────────────
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "xxxgeminikeyxxx")
MODEL = VARSAYILAN_MODEL
# İstemci gemini_ortak.istemci_al() ile TEMBEL kurulur: worker.py bu modülü top-level
# import ediyor, anahtar yokken modül seviyesinde Client() kurmak worker'ı import
# anında çökertirdi (eski SDK'nın genai.configure'ı sessizce geçiyordu).

# Sayfa başına minimum karakter — altındaysa taranmış say
TARANMIS_ESIGI = 50

# ── Kırmızı Alarm Kuralları ───────────────────────────────
# Buradan kolayca güncellenebilir, prompt'a gömülü değil
KIRMIZI_ALARM_KURALLARI = """
KIRMIZI ALARM TETİKLEYİCİLER (Bunlardan herhangi biri varsa kırmızı alarm üret):

MALİ RİSKLER:
- "Fiyat farkı verilmeyecektir" → Enflasyonda zarar riski
- "Avans verilmeyecektir" → Nakit akışı baskısı
- Kesin teminat oranı %6 üzeri → Yüksek nakit blokajı
- "Götürü bedel" + belirsiz iş tanımı → Maliyet tahmini imkansız
- Ödeme süresi 90 günü aşıyorsa → Finansman riski

SÜRE RİSKLERİ:
- Günlük cezai şart %0.3 üzeri → Tehlikeli
- "Süre uzatımı verilmez" ifadesi
- İş süresi kısaysa işin büyüklüğüne göre → Teslim riski
- Gecikme halinde sözleşme feshi şartı

YETERLİLİK TUZAKLARI:
- "Benzer iş" tanımı çok dar veya spesifik
- İş deneyim belgesi tutarı tahmini bedelin %50 üzeri
- Aynı anda birden fazla sözleşme yasağı
- Özel lisans/izin gerektiren işler

OPERASYONEL RİSKLER:
- Yerli malı zorunluluğu
- Özel güvenlik/gizlilik gerektiren lokasyon
- Alt yüklenici yasağı veya sıkı kısıtı
- Teknik şartnamede belirsiz/ölçülemeyen kriterler
"""

# ── PDF İndirme ───────────────────────────────────────────
def pdf_indir(url: str) -> str | None:
    """
    URL'den dosyayı indirir. EKAP'ın "İhale Dokümanı" (islem_id=1) bundle'ı genelde
    ZIP olarak gelir (bkz. ekap_scraper.belge_indir_yukle) — bu durumda içindeki
    ilk .pdf üyesi çıkarılıp onun yolu döndürülür (analiz tek bir PDF bekliyor).
    """
    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/125.0.0.0 Safari/537.36"
            )
        }
        r = requests.get(url, headers=headers, timeout=30, stream=True)
        r.raise_for_status()
        icerik = r.content

        if icerik[:4] == b"PK\x03\x04":
            with tempfile.TemporaryDirectory() as tmpdir:
                zip_yolu = os.path.join(tmpdir, "belge.zip")
                with open(zip_yolu, "wb") as f:
                    f.write(icerik)
                with zipfile.ZipFile(zip_yolu) as zf:
                    pdf_uyeler = [n for n in zf.namelist() if n.lower().endswith(".pdf")]
                    if not pdf_uyeler:
                        print("  ✗ ZIP içinde PDF bulunamadı")
                        return None
                    # En büyük PDF genelde asıl şartname (ekler/formlar daha küçük olur)
                    en_buyuk = max(pdf_uyeler, key=lambda n: zf.getinfo(n).file_size)
                    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
                    tmp.write(zf.read(en_buyuk))
                    tmp.close()
                    return tmp.name

        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
        tmp.write(icerik)
        tmp.close()
        return tmp.name
    except Exception as e:
        print(f"  ✗ PDF indirilemedi: {e}")
        return None


# ── PDF Tip Tespiti + Metin Çıkarma ──────────────────────
def pdf_analiz_et(dosya_yolu: str) -> dict:
    """
    PDF'i inceler:
    - Metin varsa çıkarır → kredi: 1
    - Taranmışsa tespit eder → kredi: 2
    """
    try:
        metin_parcalari = []
        sayfa_sayisi = 0

        with pdfplumber.open(dosya_yolu) as pdf:
            sayfa_sayisi = len(pdf.pages)
            for page in pdf.pages[:60]:  # Max 60 sayfa
                metin = page.extract_text()
                if metin:
                    metin_parcalari.append(metin)

        toplam_metin = "\n\n".join(metin_parcalari)
        karakter_yogunlugu = len(toplam_metin) / max(sayfa_sayisi, 1)

        if karakter_yogunlugu < TARANMIS_ESIGI:
            print(f"  ⚠️  Taranmış PDF tespit edildi ({karakter_yogunlugu:.0f} kar/sayfa) → 2 kredi")
            return {
                "durum": "taranmis",
                "kredi": 2,
                "metin": None,
                "sayfa_sayisi": sayfa_sayisi
            }
        else:
            print(f"  ✅ Metin PDF ({karakter_yogunlugu:.0f} kar/sayfa, {len(toplam_metin)} kar) → 1 kredi")
            return {
                "durum": "metin",
                "kredi": 1,
                "metin": toplam_metin[:50000],  # Token limiti
                "sayfa_sayisi": sayfa_sayisi
            }

    except Exception as e:
        print(f"  ✗ PDF analiz hatası: {e}")
        return {"durum": "hata", "kredi": 0, "metin": None}


# ── Güvenli JSON Parse ────────────────────────────────────
def json_parse_et(yanit_metni: str) -> dict:
    """
    Gemini'nin döndürdüğü metinden JSON'u güvenle çıkarır.
    ```json ... ``` bloğu olsa da olmasa da çalışır.
    """
    # Önce ```json bloğu ara
    eslesme = re.search(r"```json\s*(.*?)\s*```", yanit_metni, re.DOTALL)
    if eslesme:
        json_str = eslesme.group(1)
    else:
        # Direkt { } bloğu ara
        eslesme = re.search(r"\{.*\}", yanit_metni, re.DOTALL)
        if eslesme:
            json_str = eslesme.group(0)
        else:
            json_str = yanit_metni

    try:
        return json.loads(json_str)
    except json.JSONDecodeError:
        # Son çare: Gemini'ye düzelt dedirt
        print("  ⚠️  JSON parse hatası, düzeltiliyor...")
        return {"hata": "JSON parse edilemedi", "ham_yanit": yanit_metni[:500]}


# ── Ana Prompt ────────────────────────────────────────────
def prompt_olustur(sirket_profili: dict, metin: str = None) -> str:
    profil_str = json.dumps(sirket_profili, ensure_ascii=False, indent=2)
    metin_bolumu = f"\nŞARTNAME METNİ:\n{metin}" if metin else "\n[PDF görsel olarak gönderildi, içeriği analiz et]"

    return f"""
Sen üst düzey bir Stratejik İhale Analisti ve Risk Uzmanısın.
Aşağıdaki kamu ihalesi şartnamesini, verilen müşteri profiline göre analiz et.

MÜŞTERİ PROFİLİ:
{profil_str}

{KIRMIZI_ALARM_KURALLARI}

ÇIKTIYI SADECE AŞAĞIDAKİ JSON FORMATINDA VER, BAŞKA HİÇBİR METİN EKLEME:
{{
    "ozet": {{
        "baslik": "İhalenin kısa başlığı",
        "idare": "İhaleyi yapan kurum",
        "tahmini_bedel": "Varsa yaklaşık maliyet, yoksa Belirtilmemiş",
        "sure": "İşin süresi",
        "yer": "İşin yapılacağı yer",
        "konu": "İhalenin konusu 2 cümle"
    }},
    "uygunluk_skoru": 0,
    "karar": "GİR / DÜŞÜN / GIRME",
    "karar_gerekce": "1-2 cümle neden bu karar",
    "kirmizi_alarmlar": [
        "Tespit edilen her tehlikeli madde ayrı string olarak"
    ],
    "firsatlar": [
        "Firmaya avantaj sağlayan maddeler"
    ],
    "giris_engelleri": {{
        "mali": ["Ciro şartı, teminat vb"],
        "teknik": ["Sertifika, belge, ekipman"],
        "deneyim": ["İş deneyim belgesi şartları"]
    }},
    "mali_yuk": {{
        "gecici_teminat": "Tutar veya oran",
        "kesin_teminat": "Tutar veya oran",
        "odeme_suresi": "Kaç günde ödeme",
        "fiyat_farki": "Var/Yok",
        "avans": "Var/Yok"
    }},
    "aksiyon_listesi": [
        "Bu ihaleye girebilmek için yapılması gerekenler"
    ]
}}
{metin_bolumu}
"""


# ── Gemini Analiz — Metin PDF ─────────────────────────────
def metin_pdf_analiz_et(metin: str, sirket_profili: dict) -> dict:
    try:
        prompt = prompt_olustur(sirket_profili, metin)
        response = istemci_al().models.generate_content(model=MODEL, contents=prompt)
        yanit, bos_neden = yanit_metni(response)
        if not yanit:
            # Boş yanıt json_parse_et'e girip sessizce boş/None analize dönüşmesin.
            return {"hata": gemini_hata_logla("metin_pdf_analiz/boş yanıt", bos_neden)}
        return json_parse_et(yanit)
    except Exception as e:
        return {"hata": gemini_hata_logla("metin_pdf_analiz", e)}


# ── Gemini Analiz — Taranmış PDF (Vision) ────────────────
INLINE_LIMIT_BYTES = 18 * 1024 * 1024  # ~18MB ham dosya (base64 + prompt ile 20MB istek sınırına yaklaşmadan)

def taranmis_pdf_analiz_et(dosya_yolu: str, sirket_profili: dict) -> dict:
    """
    Taranmış/görsel PDF'i Gemini Vision'a verir.
    ÖNCELİK: inline veri (generate_content'e ham bayt). Bu sıralama ESKİ SDK'da zorunluydu:
    google.generativeai'nin upload_file() akışı $discovery/rest uç noktasında "API key not
    valid" veriyordu (canlıda doğrulandı — aynı anahtarla generate_content çalışıyordu).
    google-genai'ye geçişle (Backlog #34) File API standart uç noktayı kullanıyor, yani o
    hatanın ORTADAN KALKMASI bekleniyor — ANCAK canlıda henüz doğrulanmadı (migrasyon ağ
    çağrısı yapmadan yürütüldü). İnline yolu yine de önce deniyoruz: sınır altındaki
    dosyalar için tek istek daha hızlı ve yükleme/silme turunu tamamen atlar.
    """
    boyut = os.path.getsize(dosya_yolu)
    prompt = prompt_olustur(sirket_profili)

    if boyut <= INLINE_LIMIT_BYTES:
        try:
            print(f"  → Gemini Vision'a inline gönderiliyor ({boyut//1024}KB)...")
            with open(dosya_yolu, "rb") as f:
                pdf_bytes = f.read()
            response = istemci_al().models.generate_content(
                model=MODEL,
                contents=[prompt, types.Part.from_bytes(data=pdf_bytes, mime_type="application/pdf")],
            )
            yanit, bos_neden = yanit_metni(response)
            if not yanit:
                return {"hata": gemini_hata_logla("vision_inline/boş yanıt", bos_neden)}
            return json_parse_et(yanit)
        except Exception as e:
            return {"hata": gemini_hata_logla("vision_inline", e)}

    # Büyük dosya — File API
    yuklenen_dosya = None
    try:
        print(f"  → Dosya inline sınırını aşıyor ({boyut//1024//1024}MB) — Gemini File API'ye yükleniyor...")
        yuklenen_dosya = istemci_al().files.upload(
            file=dosya_yolu,
            config=types.UploadFileConfig(mime_type="application/pdf"),
        )

        # İşlenene kadar bekle. Eski kod durum ne olursa olsun döngü bitince devam ediyordu:
        # FAILED dosyada 60sn boşuna bekleyip sonra anlamsız bir API hatası veriyordu. Artık
        # FAILED anında kesiliyor, zaman aşımı da AÇIKÇA raporlanıyor (sessiz geçiş yok).
        durum_adi = None
        for _ in range(30):
            dosya_durumu = istemci_al().files.get(name=yuklenen_dosya.name)
            durum = getattr(dosya_durumu, "state", None)
            durum_adi = getattr(durum, "name", None) or str(durum)
            if durum_adi == "ACTIVE":
                break
            if durum_adi == "FAILED":
                hata_detay = getattr(dosya_durumu, "error", None)
                return {"hata": gemini_hata_logla(
                    "vision_file_api", f"dosya işlenemedi (state=FAILED, detay={hata_detay})")}
            time.sleep(2)
        else:
            return {"hata": gemini_hata_logla(
                "vision_file_api", f"dosya 60sn içinde ACTIVE olmadı (son state={durum_adi})")}

        response = istemci_al().models.generate_content(
            model=MODEL,
            contents=[prompt, types.Part.from_uri(
                file_uri=yuklenen_dosya.uri, mime_type="application/pdf")],
        )
        yanit, bos_neden = yanit_metni(response)
        if not yanit:
            return {"hata": gemini_hata_logla("vision_file_api/boş yanıt", bos_neden)}
        return json_parse_et(yanit)

    except Exception as e:
        return {"hata": gemini_hata_logla("vision_file_api", e)}

    finally:
        if yuklenen_dosya:
            try:
                istemci_al().files.delete(name=yuklenen_dosya.name)
            except Exception as e:
                # Silme hatası analizi bozmaz (dosya 48 saatte kendiliğinden düşer) ama
                # sessiz kalmasın: kota sızıntısı buradan başlar.
                print(f"  ⚠ Gemini File API temizliği başarısız ({yuklenen_dosya.name}): {e}", flush=True)


# ── Ana Pipeline ──────────────────────────────────────────
def ihale_analiz_et(
    pdf_url: str,
    sirket_profili: dict,
    kullanici_kredi: int = 999  # Test için yüksek
) -> dict:
    """
    Tam analiz pipeline.
    Gerçek sistemde kullanici_kredi Supabase'den gelecek.
    """
    print(f"\n{'='*55}")
    print("ANALİZ BAŞLIYOR")
    print(f"URL: {pdf_url[:70]}")
    print(f"{'='*55}")

    # 1. PDF indir
    print("\n1. PDF indiriliyor...")
    dosya_yolu = pdf_indir(pdf_url)
    if not dosya_yolu:
        return {"basari": False, "hata": "PDF indirilemedi", "kredi": 0}

    try:
        # 2. PDF tipini tespit et
        print("2. PDF tipi tespit ediliyor...")
        pdf_bilgi = pdf_analiz_et(dosya_yolu)

        if pdf_bilgi["durum"] == "hata":
            return {"basari": False, "hata": "PDF okunamadı", "kredi": 0}

        gereken_kredi = pdf_bilgi["kredi"]

        # 3. Kredi kontrolü
        if kullanici_kredi < gereken_kredi:
            return {
                "basari": False,
                "hata": "Yetersiz kredi",
                "gereken_kredi": gereken_kredi,
                "mevcut_kredi": kullanici_kredi,
                "pdf_turu": pdf_bilgi["durum"]
            }

        # 4. Gemini analizi
        print(f"3. Gemini analiz ediyor ({pdf_bilgi['durum']} modu)...")
        if pdf_bilgi["durum"] == "metin":
            rapor = metin_pdf_analiz_et(pdf_bilgi["metin"], sirket_profili)
        else:
            rapor = taranmis_pdf_analiz_et(dosya_yolu, sirket_profili)

        # metin_pdf_analiz_et/taranmis_pdf_analiz_et/json_parse_et Gemini hatasında
        # {"hata": "..."} döner — bu ÖNCEDEN kontrol edilmeden "başarılı" sayılıp kredi
        # düşülüyordu (kullanıcı boş/hatalı rapor için ücretlendiriliyordu). Artık engelleniyor.
        if rapor.get("hata") and not any(k for k in rapor if k != "hata" and k != "ham_yanit"):
            print(f"  ✗ Analiz başarısız, kredi düşülmeyecek: {rapor['hata']}")
            return {"basari": False, "hata": f"AI analiz hatası: {rapor['hata']}", "kredi": 0}

        # 5. Sonuç
        rapor["_meta"] = {
            "pdf_turu": pdf_bilgi["durum"],
            "harcanan_kredi": gereken_kredi,
            "sayfa_sayisi": pdf_bilgi.get("sayfa_sayisi", 0),
            "pdf_url": pdf_url
        }

        print(f"\n✅ Analiz tamamlandı — {gereken_kredi} kredi harcandı")
        return {"basari": True, "rapor": rapor, "harcanan_kredi": gereken_kredi}

    finally:
        # Geçici dosyayı her zaman sil
        Path(dosya_yolu).unlink(missing_ok=True)


# ── Test ──────────────────────────────────────────────────
if __name__ == "__main__":

    ORNEK_FIRMA = {
        "ad": "DNC Teknik Hizmetler",
        "faaliyet_alanlari": ["teknik hizmet", "bakım onarım", "elektrik", "mekanik"],
        "calisma_illeri": ["Ankara", "İstanbul", "İzmir"],
        "calisani": 25,
        "yillik_ciro_tl": 5000000,
        "belgeler": ["ISO 9001", "İSG belgesi", "Ticaret sicil"],
        "referanslar": ["hastane teknik hizmet", "kamu binası bakım"],
        "kacinilanlar": ["inşaat", "yemek", "temizlik"]
    }

    # Gerçek bir PDF URL ile test et
    TEST_URL = "https://www.w3.org/WAI/WCAG21/Techniques/pdf/PDF1.pdf"

    sonuc = ihale_analiz_et(
        pdf_url=TEST_URL,
        sirket_profili=ORNEK_FIRMA,
        kullanici_kredi=5
    )

    print("\n" + "="*55)
    print(json.dumps(sonuc, ensure_ascii=False, indent=2))

    with open("analiz_sonucu.json", "w", encoding="utf-8") as f:
        json.dump(sonuc, f, ensure_ascii=False, indent=2)
    print("\n💾 analiz_sonucu.json kaydedildi")
