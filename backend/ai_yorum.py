"""
AI Yorum Modülü — grounded + cache'li kurum/firma/ihale yorumlama (PREMIUM).

TUTARLILIK İLKESİ (kullanıcının kaygısı): AI serbest konuşmaz; GERÇEK SQL verisini yorumlar.
Yorum, grounding verisinin KABA HASH'iyle ai_yorumlari'na cache'lenir → veri materyal değişmedikçe
AYNI yorum döner (tutarlı + AI maliyeti yok). ai_ortak → DeepSeek (kıyasla: eşit kalite + hızlı).

Şu an: KURUM (kurum_ozet + analiz_pivot firma = tekrar-kazananlar). firma/ihale aynı desenle eklenecek.
UYDURMA YASAK: yalnız verilene dayan; tahmin/varsayım bir sayıya/geçmişe dayanmalı.
"""
import hashlib
import json

from ai_ortak import ai_cagir

_KURUM_SISTEM = (
    "Sen kamu ihale verisi analistisin. Sana verilen GERÇEK istatistiklere (SQL'den) dayanarak bir "
    "kamu KURUMU hakkında kısa, veri-temelli bir değerlendirme yaz. SAYI UYDURMA; yalnız verilen "
    "sayıları yorumla. Tahmin/varsayım yaparsan MUTLAKA bir veriye (yıllık desen vb.) dayandır. "
    "Türkçe, 5-7 cümle, düz metin (başlık/madde/markdown YOK). Sonda kesin sonuç olmadığını belirt."
)


def _kurum_grounding(supabase, idare: str) -> dict | None:
    """kurum_ozet + tekrar-kazanan firmalar → kompakt grounding sözlüğü. Veri yoksa None."""
    try:
        ozet = supabase.rpc("kurum_ozet", {"p_idare": idare}).execute().data or {}
    except Exception:
        return None
    if isinstance(ozet, str):
        try:
            ozet = json.loads(ozet)
        except (ValueError, TypeError):
            ozet = {}
    kpi = (ozet or {}).get("kpi") or {}
    if not kpi.get("toplam"):
        return None  # bu kurumda ihale yok → yorum yok
    firmalar = []
    try:
        piv = supabase.rpc("analiz_pivot", {"p_grup": "firma", "p_idare": idare}).execute().data or []
        for f in piv[:5]:
            firmalar.append({"ad": f.get("grup_deger"), "ihale_sayisi": f.get("ihale_sayisi"),
                             "ort_tenzilat": f.get("ort_tenzilat")})
    except Exception:
        pass
    return {
        "kurum": idare,
        "toplam_ihale": kpi.get("toplam"),
        "aktif_ihale": kpi.get("aktif"),
        "il_sayisi": kpi.get("il_sayisi"),
        "tur_dagilim": (ozet.get("tur") or [])[:5],
        "usul_dagilim": (ozet.get("usul") or [])[:6],
        "yillik_trend": (ozet.get("yillik") or []),
        "sektor_dagilim": (ozet.get("kategori") or [])[:6],
        "il_dagilim": (ozet.get("il") or [])[:5],
        "tekrar_kazananlar": firmalar,
    }


def _kaba_hash(g: dict) -> str:
    """Materyal-değişimde değişen KABA imza: hacim kovası (±100 tolere) + top-3 usul + top-3 firma +
    son yıl. Gece küçük dalgalanma yorumu YENİDEN ÜRETMEZ (tutarlılık + maliyet)."""
    toplam_kova = (g.get("toplam_ihale") or 0) // 100
    usul3 = [u.get("k") for u in (g.get("usul_dagilim") or [])[:3]]
    firma3 = [f.get("ad") for f in (g.get("tekrar_kazananlar") or [])[:3]]
    son_yil = (g.get("yillik_trend") or [{}])[-1].get("k") if g.get("yillik_trend") else None
    imza = json.dumps([toplam_kova, usul3, firma3, son_yil], ensure_ascii=False, sort_keys=True)
    return hashlib.md5(imza.encode("utf-8")).hexdigest()


def _kurum_prompt(g: dict) -> str:
    return (
        "Şu kamu kurumunu değerlendir (JSON GERÇEK verilerdir):\n"
        + json.dumps(g, ensure_ascii=False, indent=1, default=str) + "\n\n"
        "Değinilecekler: (1) ihale hacmi ve YILLIK TREND (artıyor/azalıyor/durağan mı — yillik_trend'den); "
        "(2) tercih edilen USUL — açık ihale mi yoksa pazarlık/istisna/3-g ağırlıklı mı; pazarlık/istisna "
        "ağırlığı DÜŞÜK REKABET/az şeffaflık sinyalidir, bunu veriyle belirt; (3) sektör/tür odağı; "
        "(4) TEKRAR KAZANAN firmalar — birkaç firma ihalelerin çoğunu alıyorsa yerleşik tedarikçi/düşük "
        "rekabet olabilir (ihtiyatlı, sayıyla söyle, itham etme); (5) tekliflere hazırlanan firmaya kısa "
        "bir çıkarım. Yalnız yorum metnini yaz."
    )


def kurum_yorumla(supabase, idare: str, zorla: bool = False) -> dict:
    """Kurum için grounded+cache'li AI yorumu. Döner:
    {"basari", "yorum", "kaynak": "cache"|"yeni", "uretildi_mi": bool(yeni AI çağrısı), "hata"}."""
    if not idare or len(idare.strip()) < 3:
        return {"basari": False, "yorum": None, "hata": "kurum adı geçersiz", "uretildi_mi": False}
    g = _kurum_grounding(supabase, idare)
    if not g:
        return {"basari": False, "yorum": None, "hata": "Bu kurumda yorumlanacak ihale verisi yok", "uretildi_mi": False}
    h = _kaba_hash(g)

    # Cache kontrol (veri değişmediyse aynı yorum → tutarlılık + bedava)
    if not zorla:
        try:
            c = supabase.table("ai_yorumlari").select("yorum,veri_hash").eq(
                "varlik_tip", "kurum").eq("varlik_anahtar", idare).limit(1).execute().data
            if c and c[0].get("veri_hash") == h and c[0].get("yorum"):
                return {"basari": True, "yorum": c[0]["yorum"], "kaynak": "cache",
                        "uretildi_mi": False, "hata": None}
        except Exception:
            pass

    # Yeni yorum üret (veri yeni/değişti)
    r = ai_cagir(_KURUM_SISTEM, _kurum_prompt(g), max_tokens=700, temperature=0.3, nerede="kurum_yorumla")
    if not r.get("basari") or not r.get("metin"):
        return {"basari": False, "yorum": None, "hata": r.get("hata") or "AI boş yanıt", "uretildi_mi": False}
    yorum = r["metin"].strip()
    try:
        supabase.table("ai_yorumlari").upsert({
            "varlik_tip": "kurum", "varlik_anahtar": idare, "yorum": yorum, "veri_hash": h,
        }, on_conflict="varlik_tip,varlik_anahtar").execute()
    except Exception as e:
        print(f"  ⚠ ai_yorumlari cache yazılamadı (kurum): {e}")
    return {"basari": True, "yorum": yorum, "kaynak": "yeni", "uretildi_mi": True, "hata": None}
