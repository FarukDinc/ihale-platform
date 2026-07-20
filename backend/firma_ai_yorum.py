"""
AI Firma Yorumu — ÖNCELİK 10 Faz D1.

İlke (YAPILACAKLAR.md'de yazılı): AI'ı ham LLM çağrısı olarak değil, analiz_pivot RPC'sinin
ÜRETTİĞİ SAYILARI prompt'a gömen bir yapı olarak kur. Sayılar bizim SQL'imizden geliyor
(halüsinasyon riski düşük), AI sadece bu sayıları Türkçe yorum/öngörüye çeviriyor.

Akış:
  1. api.py'deki /ai/firma-yorum endpoint'i analiz_pivot('idare'|'kategori'|'il'|'yil', p_firma=...)
     RPC'lerini çağırıp kırılımları toplar.
  2. Bu modüldeki firma_yorum_uret() o kırılımları JSON olarak Gemini'ye verir.
  3. Sonuç yukleniciler.ai_yorum + ai_yorum_tarih'e cache'lenir (7 gün) — bkz. migration_yuklenici_agg.sql.

Kullanım (api.py içinden):
    from firma_ai_yorum import firma_yorum_uret
    metin = firma_yorum_uret(firma_adi="ABC İNŞAAT", kirilimlar={"idare": [...], "kategori": [...], ...})

Env: GEMINI_API_KEY (backend/.env) — analyzer.py ile aynı konfigürasyon.

SDK: google-genai (Backlog #34). Eski google.generativeai bırakıldı. İstemci gemini_ortak
üzerinden TEMBEL kurulur — api.py bu modülü top-level import ettiği için, anahtar yokken
modül seviyesinde Client() kurmak tüm API'yi import anında çökertirdi.
"""

import json
import os

from dotenv import load_dotenv

from gemini_ortak import VARSAYILAN_MODEL, gemini_hata_logla, istemci_al, yanit_metni

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

AI_YORUM_GECERLILIK_GUN = 7  # bkz. plan: "7 gün geçerli" cache


def _prompt_olustur(firma_adi: str, kirilimlar: dict) -> str:
    veri_json = json.dumps(kirilimlar, ensure_ascii=False, indent=2, default=str)
    return f"""Sen bir kamu ihale rekabet analistisin. Aşağıda "{firma_adi}" adlı firmanın
EKAP sonuç ilanlarından derlenmiş GERÇEK istatistikleri var (idare/sektör/il/yıl kırılımları,
her biri ihale sayısı + ortalama tenzilat % içeriyor). Bu sayılara SADIK KAL, uydurma bilgi ekleme.

VERİ:
{veri_json}

Bu veriye dayanarak, bir rakip ihale teklifçisine yönelik KISA (4-6 cümle, madde işaretsiz düz
metin) bir Türkçe analiz yaz. Şunlara değin:
- Bu firma hangi idare(ler)de/sektör(ler)de baskın (en çok iş aldığı yerler)
- Tenzilat davranışı agresif mi ihtiyatlı mı (ortalama tenzilat yüzdelerine bak).
  ÖNEMLİ: ort_tenzilat null ise o kırılımda tenzilat HESAPLANAMIYOR demektir (kısımlı ihalede
  EKAP kısım bazlı yaklaşık maliyet yayımlamıyor) — null'lar için tenzilat yorumu YAPMA,
  tenzilat verisi olmadığını belirt ya da bu maddeyi atla. Null'u sıfır/düşük tenzilat sanma.
- Varsa yıllara göre bir yönelim/artış-azalış sinyali
- Bu firmayla aynı ihalede karşılaşan bir rakibe kısa bir tavsiye cümlesi

Sadece analiz metnini yaz, başlık/madde işareti/markdown kullanma."""


def firma_yorum_uret(firma_adi: str, kirilimlar: dict) -> dict:
    """
    kirilimlar: {"idare": [...], "kategori": [...], "il": [...], "yil": [...]} — her biri
    analiz_pivot RPC satırları (grup_deger, ihale_sayisi, ort_tenzilat, ...).
    Döner: {"basari": bool, "metin": str|None, "hata": str|None}
    """
    if not any(kirilimlar.values()):
        return {"basari": False, "metin": None, "hata": "Yeterli veri yok (kırılımlar boş)."}
    try:
        prompt = _prompt_olustur(firma_adi, kirilimlar)
        response = istemci_al().models.generate_content(model=VARSAYILAN_MODEL, contents=prompt)
        # Boş yanıtı sessizce "veri yok" saymıyoruz: güvenlik bloğu/token limiti nedeni log'a düşsün.
        metin, bos_neden = yanit_metni(response)
        if not metin:
            gemini_hata_logla("firma_yorum_uret/boş yanıt", bos_neden)
            return {"basari": False, "metin": None, "hata": f"Gemini boş yanıt döndü ({bos_neden})."}
        return {"basari": True, "metin": metin, "hata": None}
    except Exception as e:
        # google.genai.errors.APIError de Exception türevi — mevcut yakalama korunuyor.
        return {"basari": False, "metin": None, "hata": gemini_hata_logla("firma_yorum_uret", e)}
