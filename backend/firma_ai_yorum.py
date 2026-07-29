"""
AI Firma Yorumu — ÖNCELİK 10 Faz D1.

İlke (YAPILACAKLAR.md'de yazılı): AI'ı ham LLM çağrısı olarak değil, analiz_pivot RPC'sinin
ÜRETTİĞİ SAYILARI prompt'a gömen bir yapı olarak kur. Sayılar bizim SQL'imizden geliyor
(halüsinasyon riski düşük), AI sadece bu sayıları Türkçe yorum/öngörüye çeviriyor.

Akış:
  1. api.py'deki /ai/firma-yorum endpoint'i analiz_pivot('idare'|'kategori'|'il'|'yil', p_firma=...)
     RPC'lerini çağırıp kırılımları toplar.
  2. Bu modüldeki firma_yorum_uret() o kırılımları JSON olarak AI'a verir.
  3. Sonuç yukleniciler.ai_yorum + ai_yorum_tarih'e cache'lenir (7 gün) — bkz. migration_yuklenici_agg.sql.

Kullanım (api.py içinden):
    from firma_ai_yorum import firma_yorum_uret
    metin = firma_yorum_uret(firma_adi="ABC İNŞAAT", kirilimlar={"idare": [...], "kategori": [...], ...})

SAĞLAYICI (29 Tem): buradaki TEK AI çağrısı düz METİN/CHAT'tir (prompt'a yalnız JSON'a
çevrilmiş sayılar giriyor; görüntü/bayt/embedding YOK) → ai_ortak.ai_cagir'a bağlandı.
Birincil DeepSeek, yedek Gemini (env AI_SAGLAYICI ile ters çevrilebilir); anahtar seçimi
ve yedeğe düşme ai_ortak'ın işi, bu modül sağlayıcı bilmez.
⚠️ Prompt METNİ DEĞİŞTİRİLMEDİ: çıktı kullanıcıya gösteriliyor (4-6 cümle, düz metin,
madde işaretsiz) — üslup/uzunluk sözleşmesi aynen korunuyor.

Env: DEEPSEEK_API_KEY / GEMINI_API_KEY (backend/.env) — ai_ortak okur, bu modül okumaz.
"""

import json
import os

from dotenv import load_dotenv

from ai_ortak import ai_cagir, ai_hata_logla

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

# Geriye uyum: eski kod/araçlar bu sabiti import edebilir diye duruyor. Artık KULLANILMIYOR —
# anahtar seçimi (DeepSeek ↔ Gemini) ai_ortak içinde, çağrı anında yapılıyor.
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")

# Çıktı 4-6 cümlelik Türkçe düz metin; Türkçe'de token/karakter oranı yüksek olduğu için
# cümlenin ortadan kesilmemesi (finish_reason='length') adına cömert tutuldu.
AI_MAX_TOKEN = 900

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
        # Sistem rolü BOŞ: rol tanımı ("Sen bir kamu ihale rekabet analistisin...") prompt'un
        # kendi içinde — Gemini'ye giden metinle birebir aynı girdi korunsun diye bölünmedi.
        # Boş yanıt / ağ hatası / anahtar yokluğu ai_ortak içinde loglanıyor (sessiz yutma yok),
        # sözleşme aynı kalsın diye dönüş yine {basari, metin, hata}.
        sonuc = ai_cagir("", prompt, max_tokens=AI_MAX_TOKEN, nerede="firma_yorum_uret")
        if not sonuc["basari"] or not sonuc["metin"]:
            return {"basari": False, "metin": None,
                    "hata": sonuc.get("hata") or "AI boş yanıt döndü."}
        return {"basari": True, "metin": sonuc["metin"], "hata": None}
    except Exception as e:
        # Beklenmedik hata (prompt kurulumu vb.) — mevcut yakalama davranışı korunuyor.
        return {"basari": False, "metin": None, "hata": ai_hata_logla("firma_yorum_uret", e)}
