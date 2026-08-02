#!/usr/bin/env python3
"""
idare_ad_temizle.py — 26-7 / UV-4: İdare adı temizliği (AI destekli — DeepSeek birincil, Gemini yedek)

SORUN: idare adları EKAP KAYNAĞINDA bozuk gelir —
  (a) büyük/küçük harf + boşluk varyantı: "AFYONKARAHİSAR İl Özel İdaresi" ↔ "... İL ÖZEL İDARESİ"
  (b) kelime-ortası wrap boşluğu: "ALTINPAR K"→ALTINPARK, "HİZMET LERİ"→HİZMETLERİ, "BET ON"→BETON
  (c) kısaltma varyantı: "İŞL.LTD.ŞTİ." ↔ "İŞLETMELERİ LİMİTED ŞİRKETİ"
İdare = kurum-analiz/DETSİS/takip JOIN anahtarı → kör düzeltme TEHLİKELİ. Bu yüzden:
  1) HEURİSTİK aday seç (dupe-grup + wrap imzası),
  2) AI ile (ai_ortak: DeepSeek birincil, Gemini yedek) her adayın DÜZELTİLMİŞ kanonik
     formunu al (meşru "E Tipi"/"1 Nolu"/A.Ş. korunur),
  3) DRY-RUN CSV yaz (logs/idare_remap_oneri.csv) → İNSAN İNCELER,
  4) --apply ile remap (ilanlar + dogrudan_temin_ilanlari + takip_idareler) + MV refresh notu.

Kullanım (VDS'te):
  python idare_ad_temizle.py --dry-run            # aday + AI önerisi -> CSV (yazma YOK)
  python idare_ad_temizle.py --dry-run --limit 60 # hızlı örnek
  python idare_ad_temizle.py --apply --min-guven 0.85   # CSV'deki yüksek güvenli düzeltmeleri uygula

Env (backend/.env): SUPABASE_URL, SUPABASE_SERVICE_KEY, AI_SAGLAYICI, DEEPSEEK_API_KEY,
  (ops.) DEEPSEEK_MODEL / GEMINI_API_KEY
"""
import os, re, sys, csv, json, argparse, time
import httpx
from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))
SB_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
SB_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")
CSV_YOL = os.path.join(os.path.dirname(__file__), "..", "logs", "idare_remap_oneri.csv")

# AI — proje ortak kapısı (sağlayıcı-bağımsız): DeepSeek BİRİNCİL, Gemini YEDEK.
# NOT: Gemini servis hesabı 29 Tem'de öldü (401 "service account is deleted or disabled");
# metin işleri DeepSeek'te. ai_ortak birincil ölürse otomatik yedeğe düşer.
sys.path.insert(0, os.path.dirname(__file__))
from ai_ortak import ai_cagir, ai_durum  # noqa: E402

def _h():
    return {"apikey": SB_KEY, "Authorization": f"Bearer {SB_KEY}", "Content-Type": "application/json"}

def tr_fold(s: str) -> str:
    return (s or "").replace("İ", "i").replace("I", "i").replace("ı", "i") \
        .replace("Ş", "s").replace("ş", "s").replace("Ğ", "g").replace("ğ", "g") \
        .replace("Ü", "u").replace("ü", "u").replace("Ö", "o").replace("ö", "o") \
        .replace("Ç", "c").replace("ç", "c").lower()

# Meşru "tek/kısa token"lar — bunlar bozukluk DEĞİL (cezaevi tipi, okul no vb.)
_MESRU_KISA = re.compile(r"\b([A-DF-HL-NP-UYZa-z]?\s*(Tipi|Nolu|Blok|Grup|Kısım|Sınıf|No))\b", re.IGNORECASE)
# Wrap imzası: kelime-ortasına düşmüş lone kısa parça (tek büyük harf ya da 2-3 harf), meşru değilse
_WRAP = re.compile(r"[a-zçğıöşü]\s+[A-ZÇĞİÖŞÜ](\s|$)|[A-ZÇĞİÖŞÜ]{2,3}\s+[A-ZÇĞİÖŞÜ]{2,}")

def idareleri_getir() -> list[tuple[str, int]]:
    """idare_dizin_json() RPC — tüm idare + toplam ihale (tek istek)."""
    with httpx.Client(timeout=60) as c:
        r = c.post(f"{SB_URL}/rest/v1/rpc/idare_dizin_json", headers=_h(), json={})
        r.raise_for_status()
        return [(row[0], int(row[1] or 0)) for row in (r.json() or []) if row and row[0]]

def adaylari_bul(idareler):
    """(a) dupe-grup üyeleri + (b) wrap imzalı tekiller → aday set."""
    grup = {}
    for ad, adet in idareler:
        grup.setdefault(tr_fold(ad).replace(" ", ""), []).append((ad, adet))
    adaylar = {}
    # (a) folded-no-space grubunda >1 varyant → hepsi aday (aynı kurum, farklı yazım)
    for k, uyeler in grup.items():
        if len(uyeler) > 1:
            for ad, adet in uyeler:
                adaylar[ad] = adet
    # (b) wrap imzalı tekiller (meşru "E Tipi/1 Nolu" hariç)
    for ad, adet in idareler:
        if ad in adaylar:
            continue
        temiz = _MESRU_KISA.sub(" ", ad)
        if _WRAP.search(temiz):
            adaylar[ad] = adet
    return adaylar

AI_SISTEM = (
    "Sen Türkiye kamu idaresi / kurum / şirket adlarını normalize eden bir uzmansın. "
    "Yanıtını YALNIZ geçerli bir JSON nesnesi olarak verirsin, başka hiçbir metin yazmazsın."
)
AI_TALIMAT = (
    "Aşağıda Türkiye kamu idaresi / kurum / şirket adları var. Bazıları EKAP kaynağında BOZUK: "
    "kelime ortasına boşluk girmiş (ör. 'ALTINPAR K'→'ALTINPARK', 'HİZMET LERİ'→'HİZMETLERİ', "
    "'BET ON'→'BETON') ya da AYNI kurum farklı büyük/küçük harf/boşlukla yazılmış. "
    "KURALLAR: "
    "1) Meşru kısaltma/tipleri KORU: 'E Tipi', 'L Tipi', '1 Nolu', 'A.Ş.', 'LTD.ŞTİ.', 'MÜD.'. "
    "2) Sadece bariz kelime-ortası boşluğunu birleştir; emin değilsen DEĞİŞTİRME. "
    "3) Anlamı/kelimeleri EKLEME-ÇIKARMA, yalnız yazımı düzelt. "
    "4) Büyük/küçük harfi Türkçe kurumsal yazıma göre normalize edebilirsin ama İ/ı'ya dikkat et. "
    "YALNIZCA DÜZELTTİĞİN adları döndür — değiştirmediklerini LİSTELEME. "
    "Çıktı formatı (json): "
    '{"sonuc":[{"orijinal":"...","duzeltilmis":"...","guven":0.0}]}  '
    'guven 0-1 arası güven puanıdır. Hiçbir düzeltme yoksa {"sonuc":[]} döndür.'
)

def ai_duzelt(adlar, model=None):
    """ai_ortak üzerinden (DeepSeek birincil, Gemini yedek) düzeltme önerisi al."""
    kullanici = AI_TALIMAT + "\n\nADLAR:\n" + "\n".join(f"- {a}" for a in adlar)
    s = ai_cagir(AI_SISTEM, kullanici, max_tokens=8000, json_mod=True,
                 temperature=0.1, model=model, deneme=3, nerede="idare_ad_temizle")
    if not s["basari"] or not s["metin"]:
        return []
    m = re.search(r"\{.*\}", s["metin"], re.DOTALL)
    if not m:
        return []
    try:
        return json.loads(m.group(0)).get("sonuc", [])
    except Exception as e:
        print(f"  ✗ JSON ayrıştırılamadı ({s.get('saglayici')}): {e}", file=sys.stderr, flush=True)
        return []

def dry_run(limit, model=None):
    idareler = idareleri_getir()
    print(f"Toplam idare: {len(idareler)}")
    adaylar = adaylari_bul(idareler)
    print(f"Aday (bozuk olabilir): {len(adaylar)}")
    ad_listesi = sorted(adaylar, key=lambda a: -adaylar[a])
    if limit:
        ad_listesi = ad_listesi[:limit]
    satirlar, i = [], 0
    while i < len(ad_listesi):
        obek = ad_listesi[i:i + 20]   # 20'lik öbek: 40'ta çıktı max_tokens'ı aşıp JSON kırpılıyordu
        for s in ai_duzelt(obek, model):
            orj = (s.get("orijinal") or "").strip()
            duz = (s.get("duzeltilmis") or "").strip()
            if orj and duz and duz != orj:
                satirlar.append({"orijinal": orj, "duzeltilmis": duz,
                                 "guven": s.get("guven", 0), "ihale": adaylar.get(orj, 0)})
        i += 20
        print(f"  {min(i,len(ad_listesi))}/{len(ad_listesi)} işlendi…", flush=True)
        time.sleep(0.4)   # kota dostu
    satirlar.sort(key=lambda r: -r["ihale"])
    os.makedirs(os.path.dirname(CSV_YOL), exist_ok=True)
    with open(CSV_YOL, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["orijinal", "duzeltilmis", "guven", "ihale"])
        w.writeheader(); w.writerows(satirlar)
    print(f"\n✓ {len(satirlar)} düzeltme önerisi → {CSV_YOL}")
    print("İlk 20 (ihale sayısına göre):")
    for r in satirlar[:20]:
        print(f"  [{r['ihale']:>5}] g={r['guven']}  {r['orijinal']}  →  {r['duzeltilmis']}")

def apply(min_guven, sadece_takip=False):
    if not os.path.exists(CSV_YOL):
        print(f"✗ Önce --dry-run çalıştır (öneri dosyası yok: {CSV_YOL})"); return
    with open(CSV_YOL, encoding="utf-8") as f:
        rows = [r for r in csv.DictReader(f) if float(r.get("guven") or 0) >= min_guven]
    # --sadece-takip: ilanlar+dt zaten güncellendiyse yalnız takip_idareler'i (grant sonrası) yeniden dene.
    tablolar = (("takip_idareler", "idare_ad"),) if sadece_takip else \
        (("ilanlar", "idare"), ("dogrudan_temin_ilanlari", "idare"), ("takip_idareler", "idare_ad"))
    print(f"Uygulanacak remap (güven≥{min_guven}): {len(rows)}  tablolar={[t[0] for t in tablolar]}")
    n, hata = 0, 0
    with httpx.Client(timeout=60) as c:
        for r in rows:
            orj, duz = r["orijinal"], r["duzeltilmis"]
            for tablo, kolon in tablolar:
                # origin /rest/v1 hız limiti (2r/s) + geçici hatalar için throttle & 429/5xx retry;
                # yoksa remap SESSİZCE düşerdi (435 istekte fark edilmez).
                for deneme in range(4):
                    try:
                        resp = c.patch(f"{SB_URL}/rest/v1/{tablo}", headers={**_h(), "Prefer": "return=minimal"},
                                       params={kolon: f"eq.{orj}"}, json={kolon: duz})
                        if resp.status_code in (429, 500, 502, 503, 504):
                            time.sleep(min(2 ** deneme, 8)); continue
                        if resp.status_code >= 400:
                            hata += 1
                            print(f"  ✗ {tablo} '{orj[:30]}…': {resp.status_code} {resp.text[:120]}", file=sys.stderr)
                        break
                    except Exception as e:
                        if deneme == 3:
                            hata += 1
                            print(f"  ✗ {tablo} '{orj[:30]}…': {e}", file=sys.stderr)
                        else:
                            time.sleep(min(2 ** deneme, 8))
                time.sleep(0.5)   # ~2 istek/sn — origin limitinin altında kal
            n += 1
            if n % 25 == 0:
                print(f"  {n}/{len(rows)}… ({hata} hata)", flush=True)
    print(f"\n✓ {n} idare remap edildi ({hata} tablo-yazımı hatası).")
    print("⚠ ŞİMDİ MV + türetilmiş alanları TAZELE (idare sayıları + idare_tur güncellensin):")
    print("  docker exec -i supabase-db psql -U supabase_admin -d postgres -c \\")
    print("    \"REFRESH MATERIALIZED VIEW CONCURRENTLY public.idare_ozet_mv; REFRESH MATERIALIZED VIEW CONCURRENTLY public.dt_idare_ozet_mv;\"")
    print("  docker exec -i supabase-db psql -U postgres -d postgres -c \"SELECT public.idare_tur_tazele();\"")

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--min-guven", type=float, default=0.85)
    ap.add_argument("--model", default=None, help="sağlayıcı öntanım modelini ez (normalde boş: env/DeepSeek)")
    ap.add_argument("--sadece-takip", action="store_true",
                    help="apply'da yalnız takip_idareler'i güncelle (ilanlar+dt zaten yapıldıysa)")
    a = ap.parse_args()
    if not SB_URL or not SB_KEY:
        print("✗ SUPABASE_URL / SUPABASE_SERVICE_KEY eksik (.env)"); sys.exit(1)
    if a.apply:
        apply(a.min_guven, sadece_takip=a.sadece_takip)
    else:
        d = ai_durum()
        if not (d["deepseek_anahtar"] or d["gemini_anahtar"]):
            print("✗ AI anahtarı yok (DEEPSEEK_API_KEY / GEMINI_API_KEY .env'de eksik)"); sys.exit(1)
        print(f"AI: birincil={d['birincil']} yedek={d['yedek']} "
              f"(deepseek={'var' if d['deepseek_anahtar'] else 'YOK'}, "
              f"gemini={'var' if d['gemini_anahtar'] else 'YOK'})")
        dry_run(a.limit, a.model)
