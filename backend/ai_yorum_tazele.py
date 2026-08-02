# -*- coding: utf-8 -*-
"""
Gece YORUM TAZELEME — veri güncellendikten SONRA çalışır (run_scraper.sh sonunda, MV'lerden sonra).

SORUN: kurum AI yorumu 7 günlük hızlı-yol cache'iyle döner; veri o pencere içinde değişse bile
yorum en fazla 7 gün gecikmeyle güncellenir (hash kontrolü yalnız yavaş-yolda, 7+ gün sonra).

ÇÖZÜM (bu script): cache'li her kurum yorumunun veri-hash'ini TAZE grounding ile yeniden hesaplar;
hash DEĞİŞTİYSE (veri materyal olarak değişti — hacim //100 kovası, top usul/firma, DT hacmi/kazananı)
cache kaydını SİLER. Kullanıcı bir sonraki görüntülemede güncel veriye dayalı TAZE yorum alır.
Böylece yorum, gece verisiyle ~1 gün içinde senkron kalır; hash değişmeyen kurumlar (küçük dalgalanma)
dokunulmadan hızlı cache'te kalır (tutarlılık + AI maliyeti yok).

Neden SİLME (proaktif yeniden üretim değil): yeniden üretim AI token'ı bizim cebimizden harcar
(kullanıcı belki bir daha bakmaz). Silme, mevcut kredili on-demand modele uyar — talep gelince üretilir.

DOKUNULMAYAN: firma_iletisim (web-grounding, bizim verimizle değişmez). Firma yorumu (yukleniciler.ai_yorum)
şu an hash'siz (yalnız 7 gün) — ayrı bir düzenleme gerekir (bkz. YAPILACAKLAR).

Kullanım (cron): venv/bin/python ai_yorum_tazele.py
"""
import os
import sys
import time

from dotenv import load_dotenv

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), ".env"))

from supabase import create_client

from ai_yorum import _kurum_grounding, _kaba_hash
from firma_ai_yorum import firma_kirilim_topla, firma_veri_hash


def main():
    url = os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_SERVICE_KEY") or os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    if not url or not key:
        print("ai_yorum_tazele: SUPABASE_URL / SUPABASE_SERVICE_KEY eksik — atlanıyor", flush=True)
        return 0
    sb = create_client(url, key)

    try:
        rows = sb.table("ai_yorumlari").select("varlik_anahtar, veri_hash").eq(
            "varlik_tip", "kurum").execute().data or []
    except Exception as e:
        print(f"ai_yorum_tazele: cache okunamadı: {e}", flush=True)
        return 1

    silinen, korunan, atlanan, hata = 0, 0, 0, 0
    t0 = time.time()
    for r in rows:
        idare = r.get("varlik_anahtar")
        eski_hash = r.get("veri_hash")
        if not idare:
            continue
        try:
            g = _kurum_grounding(sb, idare)
            if not g:
                # Grounding üretilemedi (geçici hata / veri yok) → cache'e DOKUNMA (yanlış silme yapma)
                atlanan += 1
                continue
            if _kaba_hash(g) != eski_hash:
                sb.table("ai_yorumlari").delete().eq("varlik_tip", "kurum").eq(
                    "varlik_anahtar", idare).execute()
                silinen += 1
            else:
                korunan += 1
        except Exception as e:
            hata += 1
            print(f"  ⚠ {str(idare)[:50]}: {type(e).__name__}: {str(e)[:100]}", flush=True)

    sure = time.time() - t0
    print(f"kurum yorum tazeleme: {len(rows)} cache · {silinen} geçersiz kılındı (veri değişti) · "
          f"{korunan} korundu · {atlanan} atlandı · {hata} hata · {sure:.0f}s", flush=True)

    # ── FİRMA yorumları (yukleniciler.ai_yorum + ai_yorum_hash) ─────────────────────────
    # Kurumla AYNI mantık; farklar: (1) cache yukleniciler'de (ai_yorumlari değil); (2) ESKİ
    # hash'siz kayıtlar (kolon yeni) → hash geri-doldurulur, yorum KORUNUR (haksız yeniden-ücret
    # olmasın); (3) geçersiz kılma = ai_yorum/ai_yorum_tarih/ai_yorum_hash NULL (satır silinmez).
    PROFIL = ("ad, normalize_ad, ai_yorum_hash, toplam_sozlesme_sayisi, toplam_ciro, il, sektor, "
              "seg_parlayan, seg_sonen, seg_ilk_kez, seg_150mn, ciro_son_12ay, ciro_onceki_12ay, "
              "buyume_yuzde, ortak_girisim")
    try:
        # Sahte supabase wrapper'da .filter/.not_.is_ YOK; negasyon .not_(col, op, val) ile:
        # → ai_yorum_tarih=not.is.null (dolu cache satırları).
        frows = sb.table("yukleniciler").select(PROFIL).not_(
            "ai_yorum_tarih", "is", "null").execute().data or []
    except Exception as e:
        print(f"ai_yorum_tazele: firma cache okunamadı: {e}", flush=True)
        frows = []

    f_sil, f_koru, f_backfill, f_atla, f_hata = 0, 0, 0, 0, 0
    t1 = time.time()
    for r in frows:
        ad = r.get("ad")
        norm = r.get("normalize_ad")
        if not ad or not norm:
            continue
        try:
            kir = firma_kirilim_topla(sb, ad, r)
            if not any(kir.get(g) for g in ("idare", "kategori", "il", "yil")) and not kir.get("dt_kazanimlari"):
                f_atla += 1  # veri yok / geçici RPC hatası → cache'e DOKUNMA (yanlış silme yapma)
                continue
            yeni = firma_veri_hash(kir)
            eski = r.get("ai_yorum_hash")
            if not eski:
                # Eski hash'siz kayıt → hash'i geri-doldur, yorumu KORU
                sb.table("yukleniciler").update({"ai_yorum_hash": yeni}).eq("normalize_ad", norm).execute()
                f_backfill += 1
            elif yeni != eski:
                sb.table("yukleniciler").update(
                    {"ai_yorum": None, "ai_yorum_tarih": None, "ai_yorum_hash": None}
                ).eq("normalize_ad", norm).execute()
                f_sil += 1
            else:
                f_koru += 1
        except Exception as e:
            f_hata += 1
            print(f"  ⚠ firma {str(ad)[:50]}: {type(e).__name__}: {str(e)[:100]}", flush=True)
    print(f"firma yorum tazeleme: {len(frows)} cache · {f_sil} geçersiz kılındı · {f_koru} korundu · "
          f"{f_backfill} hash geri-dolduruldu · {f_atla} atlandı · {f_hata} hata · {time.time()-t1:.0f}s", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
