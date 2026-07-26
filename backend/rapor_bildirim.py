#!/usr/bin/env python3
"""Rutin rapor bildirimi (#6) — 26 Tem 2026.
Kullanıcıların kayıtlı rapor kriterlerini (rapor_abonelikleri) gece çalıştırır;
son gönderimden bu yana eşleşen yeni ihale/sonuç varsa bildirimler'e kayıt açar VE
(bildirim_email tercihi açıksa) Resend ile e-posta atar. Mevcut rapor_ihale/rapor_sonuc
RPC'lerini (join+perf hazır) ve notify.py'yi yeniden kullanır. EXPORT DEĞİL.
Env: SUPABASE_URL, SUPABASE_SERVICE_KEY, RESEND_API_KEY. Cron: run_scraper.sh.
"""
import os, sys
from datetime import datetime, timezone, timedelta
import httpx
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
load_dotenv(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env"))
from notify import resend_gonder, auth_email_map, para_fmt, tarih_fmt

SUPABASE_URL = os.environ.get("SUPABASE_URL", "").rstrip("/")
SERVICE_KEY  = os.environ.get("SUPABASE_SERVICE_KEY", "")
SITE_URL     = os.environ.get("SITE_URL", "https://ihaleglobal.com")

def _h():
    return {"apikey": SERVICE_KEY, "Authorization": f"Bearer {SERVICE_KEY}", "Content-Type": "application/json"}

def eslesenler(c, tip, kriter, bas_tarih):
    """Kayıtlı kritere göre bas_tarih'ten itibaren eşleşen ihale/sonuçları getir (rapor RPC)."""
    fn = "rapor_ihale" if tip == "ihale" else "rapor_sonuc"
    body = {
        "p_kelime": kriter.get("kelime") or None,
        "p_il": kriter.get("il") or None,
        "p_kategori": kriter.get("kategori") or None,
        "p_bas": bas_tarih,
        "p_min": kriter.get("min") or None,
        "p_offset": 0, "p_limit": 20,
    }
    if tip == "ihale":
        body["p_durum"] = kriter.get("durum") or None
    r = c.post(f"{SUPABASE_URL}/rest/v1/rpc/{fn}", json=body, headers=_h())
    if r.status_code >= 300:
        print(f"  ✗ {fn} hata {r.status_code}: {r.text[:120]}")
        return []
    return (r.json() or {}).get("satirlar", []) or []

def email_html(ad, tip, satirlar):
    tur = "ihale" if tip == "ihale" else "sonuç"
    sat = ""
    for i in satirlar[:8]:
        bedel = i.get("bedel") or i.get("sozlesme_bedeli") or i.get("kazanan_teklif")
        alt = i.get("idare") or i.get("kazanan_firma") or ""
        il = i.get("il") or ""
        sat += f"""<tr><td style="padding:14px;border-bottom:1px solid #e5e7eb;">
          <div style="font-weight:600;color:#111827;">{(i.get('baslik') or i.get('kazanan_firma') or '—')}</div>
          <div style="font-size:13px;color:#6b7280;margin-top:3px;">{alt} {('· '+il) if il else ''} {('· '+para_fmt(bedel)) if bedel else ''}</div>
        </td><td style="padding:14px;border-bottom:1px solid #e5e7eb;text-align:right;">
          <a href="{SITE_URL}/ihale-detay?id={i.get('id')}" style="background:#f59e0b;color:#1a1a1a;padding:7px 14px;border-radius:6px;text-decoration:none;font-size:13px;font-weight:700;">Detay →</a>
        </td></tr>"""
    return f"""<!DOCTYPE html><html><body style="font-family:Arial,sans-serif;background:#f3f4f6;padding:20px;">
    <div style="max-width:640px;margin:0 auto;background:#fff;border-radius:12px;overflow:hidden;">
      <div style="background:#0F2A47;padding:20px 24px;"><span style="color:#F0A500;font-size:20px;font-weight:800;">İhaleGlobal</span></div>
      <div style="padding:24px;">
        <h2 style="color:#111827;font-size:18px;margin:0 0 4px;">"{ad}" raporunuzda {len(satirlar)} yeni {tur}</h2>
        <p style="color:#6b7280;font-size:14px;margin:0 0 16px;">Kaydettiğiniz kritere uyan yeni fırsatlar:</p>
        <table style="width:100%;border-collapse:collapse;">{sat}</table>
        <p style="color:#9ca3af;font-size:12px;margin-top:18px;">Bu raporu <a href="{SITE_URL}/raporlar" style="color:#f59e0b;">Raporlarım</a> sayfasından yönetebilirsiniz.</p>
      </div></div></body></html>"""

def main():
    if not SUPABASE_URL or not SERVICE_KEY:
        print("✗ SUPABASE_URL/SERVICE_KEY yok"); return
    simdi = datetime.now(timezone.utc)
    with httpx.Client(timeout=40.0) as c:
        r = c.get(f"{SUPABASE_URL}/rest/v1/rapor_abonelikleri",
                  params={"select": "id,kullanici_id,ad,tip,kriter,son_gonderim", "aktif": "eq.true"}, headers=_h())
        if r.status_code >= 300:
            print(f"✗ abonelik çekilemedi {r.status_code}: {r.text[:120]}"); return
        abonelikler = r.json() or []
        if not abonelikler:
            print("✓ rapor_bildirim: aktif abonelik yok."); return

        # e-posta tercihleri
        uids = list({a["kullanici_id"] for a in abonelikler})
        pr = c.get(f"{SUPABASE_URL}/rest/v1/kullanici_profiller",
                   params={"select": "id,firma_adi,bildirim_email", "id": f"in.({','.join(uids)})"}, headers=_h())
        profil = {p["id"]: p for p in (pr.json() or [])} if pr.status_code < 300 else {}
        email_map = auth_email_map()

        bildirim_say = eposta_say = 0
        for a in abonelikler:
            bas = (a.get("son_gonderim") or (simdi - timedelta(days=1)).isoformat())[:10]
            try:
                sat = eslesenler(c, a["tip"], a.get("kriter") or {}, bas)
            except Exception as e:
                print(f"  ✗ {a['ad']}: {type(e).__name__} {e}"); continue
            if not sat:
                continue
            # bildirim (özet)
            bildirim = {
                "kullanici_id": a["kullanici_id"],
                "baslik": f'"{a["ad"]}" raporunda {len(sat)} yeni {"ihale" if a["tip"]=="ihale" else "sonuç"}',
                "icerik": (sat[0].get("baslik") or sat[0].get("kazanan_firma") or "")[:120],
                "tur": "rapor", "aksiyon_url": "raporlar", "okundu": False,
                "olusturulma": simdi.isoformat(),
            }
            rb = c.post(f"{SUPABASE_URL}/rest/v1/bildirimler", json=bildirim, headers=_h())
            if rb.status_code < 300:
                bildirim_say += 1
            # e-posta
            p = profil.get(a["kullanici_id"], {})
            if p.get("bildirim_email"):
                email = email_map.get(str(a["kullanici_id"]))
                if email and resend_gonder(email, f'İhaleGlobal — "{a["ad"]}" raporunda {len(sat)} yeni fırsat', email_html(a["ad"], a["tip"], sat)):
                    eposta_say += 1
            # son_gonderim güncelle
            c.patch(f"{SUPABASE_URL}/rest/v1/rapor_abonelikleri",
                    params={"id": f"eq.{a['id']}"}, json={"son_gonderim": simdi.isoformat()}, headers=_h())

        print(f"✓ rapor_bildirim: {len(abonelikler)} abonelik, {bildirim_say} bildirim, {eposta_say} e-posta.")

if __name__ == "__main__":
    main()
