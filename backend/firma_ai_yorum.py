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

import hashlib
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
AI_MAX_TOKEN = 1200  # DT + segment zenginleştirmesiyle yorum uzadı (900'de kesiliyordu, 1 Ağu)

AI_YORUM_GECERLILIK_GUN = 7  # bkz. plan: "7 gün geçerli" cache


def firma_kirilim_topla(supabase, firma_adi: str, mevcut_kayit: dict | None = None) -> dict:
    """
    Firma yorum grounding'i: analiz_pivot(idare/kategori/il/yil) + firma_dt_ozet (DT kazanımları) +
    firma_profili (segment/büyüme/ciro). api.py /ai/firma-yorum endpoint'i VE gece tazeleme
    (ai_yorum_tazele.py) BURADAN beslenir → tek kaynak (kurum tarafındaki _kurum_grounding muadili).
    mevcut_kayit: yukleniciler satırı (profil alanları); None ise firma_profili eklenmez.
    """
    kirilimlar = {}
    for grup in ("idare", "kategori", "il", "yil"):
        try:
            r = supabase.rpc("analiz_pivot", {"p_grup": grup, "p_firma": firma_adi}).execute()
            kirilimlar[grup] = (r.data or [])[:8]
        except Exception:
            kirilimlar[grup] = []
    try:
        dt = supabase.rpc("firma_dt_ozet", {"p_firma_ad": firma_adi}).execute().data
        if isinstance(dt, list):
            dt = dt[0] if dt else None
        if dt and (dt.get("dt_sayisi") or 0):
            kirilimlar["dt_kazanimlari"] = dt
    except Exception:
        pass
    if mevcut_kayit:
        segler = [ad for ad, v in (("parlayan yıldız", mevcut_kayit.get("seg_parlayan")),
                                   ("sönen", mevcut_kayit.get("seg_sonen")),
                                   ("ilk kez ihaleye giren", mevcut_kayit.get("seg_ilk_kez")),
                                   ("150mn+ büyük ölçek", mevcut_kayit.get("seg_150mn"))) if v]
        kirilimlar["firma_profili"] = {
            "toplam_sozlesme": mevcut_kayit.get("toplam_sozlesme_sayisi"),
            "toplam_ciro": mevcut_kayit.get("toplam_ciro"),
            "ana_il": mevcut_kayit.get("il"),
            "sektorler": mevcut_kayit.get("sektor"),
            "ciro_son_12ay": mevcut_kayit.get("ciro_son_12ay"),
            "ciro_onceki_12ay": mevcut_kayit.get("ciro_onceki_12ay"),
            "buyume_yuzde": mevcut_kayit.get("buyume_yuzde"),
            "ortak_girisim_yapar_mi": mevcut_kayit.get("ortak_girisim"),
            "segmentler": segler,
        }
    return kirilimlar


def firma_veri_hash(kirilimlar: dict) -> str:
    """Materyal-değişim imzası (kurum _kaba_hash muadili): sözleşme kovası (//10) + top-3 idare +
    top-3 kategori + yıl listesi + DT kovası (//10) + segmentler. Firma ölçeği küçük → kova //10
    (kurumda //100). Küçük dalgalanmada yorum YENİDEN ÜRETİLMEZ (tutarlılık + AI maliyeti yok)."""
    prof = kirilimlar.get("firma_profili") or {}
    idare_list = kirilimlar.get("idare") or []
    toplam = prof.get("toplam_sozlesme")
    if not toplam:
        toplam = sum((x.get("ihale_sayisi") or 0) for x in idare_list)
    sozlesme_kova = (toplam or 0) // 10
    idare3 = [x.get("grup_deger") for x in idare_list[:3]]
    kat3 = [x.get("grup_deger") for x in (kirilimlar.get("kategori") or [])[:3]]
    yillar = sorted(str(x.get("grup_deger")) for x in (kirilimlar.get("yil") or []))
    dt = kirilimlar.get("dt_kazanimlari") or {}
    dt_kova = (dt.get("dt_sayisi") or 0) // 10
    segler = sorted(prof.get("segmentler") or [])
    imza = json.dumps([sozlesme_kova, idare3, kat3, yillar, dt_kova, segler],
                      ensure_ascii=False, sort_keys=True)
    return hashlib.md5(imza.encode("utf-8")).hexdigest()


def _prompt_olustur(firma_adi: str, kirilimlar: dict) -> str:
    veri_json = json.dumps(kirilimlar, ensure_ascii=False, indent=2, default=str)
    return f"""Sen bir kamu ihale rekabet analistisin. Aşağıda "{firma_adi}" adlı firmanın
EKAP verisinden derlenmiş GERÇEK istatistikleri var: idare/sektör/il/yıl kırılımları (ihale sayısı +
ortalama tenzilat %), ayrıca varsa "dt_kazanimlari" (DOĞRUDAN TEMİN kazanımları — ihaleden AYRI evren)
ve "firma_profili" (toplam ciro, son 12 ay büyüme, segment etiketleri, ortak girişim eğilimi).
Bu sayılara SADIK KAL, uydurma bilgi ekleme.

VERİ:
{veri_json}

Bu veriye dayanarak, bir rakip ihale teklifçisine yönelik KISA (5-7 cümle, madde işaretsiz düz
metin) bir Türkçe analiz yaz. Şunlara değin:
- Bu firma hangi idare(ler)de/sektör(ler)de baskın (en çok iş aldığı yerler)
- Tenzilat davranışı agresif mi ihtiyatlı mı (ortalama tenzilat yüzdelerine bak).
  ÖNEMLİ: ort_tenzilat null ise o kırılımda tenzilat HESAPLANAMIYOR demektir (kısımlı ihalede
  EKAP kısım bazlı yaklaşık maliyet yayımlamıyor) — null'lar için tenzilat yorumu YAPMA,
  tenzilat verisi olmadığını belirt ya da bu maddeyi atla. Null'u sıfır/düşük tenzilat sanma.
- DOĞRUDAN TEMİN (dt_kazanimlari) VARSA: firmanın ihale dışında DT ile de iş aldığını belirt
  (dt_sayisi/bedel); ihale + DT birlikte firmanın gerçek büyüklüğünü gösterir (ikisini TOPLAMA,
  ayrı ayrı belirt — ölçek farkı var).
- firma_profili VARSA: segment etiketleri (parlayan yıldız = büyüyor, sönen = küçülüyor) ve
  buyume_yuzde ile son 12 ay yönelimini yorumla; ortak girişim yapıyorsa bunu bir davranış sinyali say.
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
