"""
bulten_gonder.py — Bülten E-posta Gönderici
--------------------------------------------
Çalışma zamanı: gece scraper bittikten sonra (run_scraper.sh'de)

Akış:
  1. Tüm aktif bültenleri çek (email_aktif=true)
  2. Her bülten için: son gönderimden bu yana eklenen eşleşen ilanları bul
  3. Eşleşme varsa e-posta gönder, son_gonderim güncelle

Env: SUPABASE_URL, SUPABASE_SERVICE_KEY, RESEND_API_KEY
"""

import os
import json
import requests
import logging
from datetime import datetime, timezone, timedelta
from supabase import create_client

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    datefmt='%H:%M:%S',
)
log = logging.getLogger(__name__)

SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://lpgelwfoarhouollhwur.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")
RESEND_KEY   = os.environ.get("RESEND_API_KEY", "")
FROM_EMAIL   = os.environ.get("BILDIRIM_FROM_EMAIL", "noreply@ihaleglobal.com")
SITE_URL     = os.environ.get("SITE_URL", "https://ihaleglobal.com")


def sb():
    return create_client(SUPABASE_URL, SUPABASE_KEY)


def kullanici_email_map():
    """GoTrue admin API — {user_id: {email, ad}} haritası."""
    emap = {}
    try:
        page = 1
        while True:
            r = requests.get(
                f"{SUPABASE_URL}/auth/v1/admin/users",
                headers={"apikey": SUPABASE_KEY, "Authorization": f"Bearer {SUPABASE_KEY}"},
                params={"page": page, "per_page": 200},
                timeout=15,
            )
            if r.status_code != 200:
                break
            users = r.json().get("users", [])
            if not users:
                break
            for u in users:
                if u.get("email"):
                    meta = u.get("user_metadata") or {}
                    emap[str(u["id"])] = {
                        "email": u["email"],
                        "ad": meta.get("full_name") or u["email"].split("@")[0],
                    }
            if len(users) < 200:
                break
            page += 1
    except Exception as e:
        log.warning(f"Auth listesi alınamadı: {e}")
    return emap


def para_fmt(v):
    if not v:
        return "—"
    if v >= 1_000_000_000:
        return f"₺{v/1_000_000_000:.1f}Mr"
    if v >= 1_000_000:
        return f"₺{v/1_000_000:.1f}M"
    if v >= 1_000:
        return f"₺{v/1_000:.0f}K"
    return f"₺{v:,.0f}"


def tarih_fmt(t):
    if not t:
        return "—"
    try:
        d = datetime.fromisoformat(str(t).replace("Z", "+00:00"))
        return d.strftime("%d.%m.%Y")
    except Exception:
        return str(t)[:10]


def eslesme_bul(db, filtre: dict, since: str) -> list[dict]:
    """Bülten filtresine uyan, since'den sonra eklenen ilanları döndür."""
    q = db.table("ilanlar").select(
        "id,baslik,idare,il,tur,usul,son_teklif_tarihi,yaklasik_maliyet_min,ekap_id"
    ).gte("olusturulma", since).eq("durum", "aktif").order("olusturulma", desc=True).limit(50)

    if filtre.get("kelime"):
        k = filtre["kelime"]
        q = q.ilike("baslik", f"%{k}%")
    if filtre.get("il"):
        q = q.eq("il", filtre["il"])
    if filtre.get("tur"):
        q = q.eq("tur", filtre["tur"])
    if filtre.get("usul"):
        q = q.ilike("usul", f"%{filtre['usul']}%")
    if filtre.get("min_bedel"):
        try:
            q = q.gte("yaklasik_maliyet_min", int(filtre["min_bedel"]))
        except (ValueError, TypeError):
            pass
    if filtre.get("max_bedel"):
        try:
            q = q.lte("yaklasik_maliyet_min", int(filtre["max_bedel"]))
        except (ValueError, TypeError):
            pass

    try:
        r = q.execute()
        return r.data or []
    except Exception as e:
        log.warning(f"Eşleşme sorgusu hatası: {e}")
        return []


def bulten_email_html(kullanici_ad: str, bulten_ad: str, filtre: dict, ilanlar: list) -> str:
    filtre_ozet = []
    if filtre.get("kelime"):
        filtre_ozet.append(f"Kelime: <strong>{filtre['kelime']}</strong>")
    if filtre.get("il"):
        filtre_ozet.append(f"İl: <strong>{filtre['il']}</strong>")
    if filtre.get("tur"):
        filtre_ozet.append(f"Tür: <strong>{filtre['tur']}</strong>")
    if filtre.get("min_bedel"):
        filtre_ozet.append(f"Min. Bedel: <strong>{para_fmt(filtre['min_bedel'])}</strong>")
    filtre_text = " &nbsp;·&nbsp; ".join(filtre_ozet) or "Tüm ihaleler"

    satirlar = ""
    for i in ilanlar[:20]:
        son_teklif = tarih_fmt(i.get("son_teklif_tarihi"))
        bedel = para_fmt(i.get("yaklasik_maliyet_min"))
        link = f"{SITE_URL}/ihale-detay?id={i['id']}"
        satirlar += f"""
        <tr>
          <td style="padding:16px 24px;border-bottom:1px solid #e5e7eb;">
            <div style="font-weight:600;color:#111827;margin-bottom:4px;line-height:1.4;">
              <a href="{link}" style="color:#111827;text-decoration:none;">{i.get('baslik','—')}</a>
            </div>
            <div style="font-size:12px;color:#6b7280;margin-bottom:6px;">
              {i.get('idare','—')} &nbsp;·&nbsp; {i.get('il','') or ''} &nbsp;·&nbsp; {i.get('tur','') or ''}
            </div>
            <div style="display:flex;gap:10px;align-items:center;flex-wrap:wrap;">
              <span style="font-size:12px;background:#fef3c7;color:#92400e;padding:2px 8px;border-radius:4px;font-weight:600;">
                Son teklif: {son_teklif}
              </span>
              <span style="font-size:12px;color:#6b7280;">Tahmini: {bedel}</span>
              <a href="{link}" style="font-size:12px;color:#f59e0b;font-weight:700;text-decoration:none;margin-left:auto;">
                Detay →
              </a>
            </div>
          </td>
        </tr>"""

    return f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#f3f4f6;font-family:Inter,Helvetica,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f3f4f6;padding:32px 16px;">
    <tr><td align="center">
      <table width="600" cellpadding="0" cellspacing="0"
             style="background:white;border-radius:12px;overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,.1);">

        <!-- HEADER -->
        <tr>
          <td style="background:#0A1628;padding:24px 32px;">
            <span style="font-size:22px;font-weight:800;color:white;">
              İhale<span style="color:#F0A500;">Global</span>
            </span>
          </td>
        </tr>

        <!-- BAŞLIK -->
        <tr>
          <td style="padding:24px 32px 16px;border-bottom:1px solid #e5e7eb;">
            <p style="margin:0 0 6px;font-size:13px;color:#9ca3af;font-weight:600;text-transform:uppercase;letter-spacing:.05em;">
              ⭐ Bülten: {bulten_ad}
            </p>
            <h1 style="margin:0 0 8px;font-size:20px;font-weight:700;color:#111827;">
              {len(ilanlar)} yeni eşleşen ihale
            </h1>
            <p style="margin:0;font-size:13px;color:#6b7280;">
              Merhaba {kullanici_ad} — filtrelerinize uygun ihaleler geldi.<br>
              <span style="font-size:12px;">{filtre_text}</span>
            </p>
          </td>
        </tr>

        <!-- İHALE LİSTESİ -->
        <tr>
          <td>
            <table width="100%" cellpadding="0" cellspacing="0">
              {satirlar}
            </table>
          </td>
        </tr>

        <!-- CTA -->
        <tr>
          <td style="padding:20px 32px;text-align:center;border-top:1px solid #e5e7eb;">
            <a href="{SITE_URL}/ihaleler"
               style="display:inline-block;background:#0A1628;color:white;padding:11px 24px;
                      border-radius:7px;text-decoration:none;font-size:13px;font-weight:700;">
              Tüm İhalelere Git →
            </a>
          </td>
        </tr>

        <!-- FOOTER -->
        <tr>
          <td style="padding:14px 32px;background:#f9fafb;border-top:1px solid #e5e7eb;">
            <p style="margin:0;font-size:12px;color:#9ca3af;text-align:center;">
              Bu bülteni kapatmak için
              <a href="{SITE_URL}/bildirimler" style="color:#f59e0b;">Bildirimler</a> sayfanızdan
              "<strong>{bulten_ad}</strong>" bültenini kapatın.
              <br>© 2026 İhaleGlobal &nbsp;·&nbsp; ihaleglobal.com
            </p>
          </td>
        </tr>

      </table>
    </td></tr>
  </table>
</body>
</html>"""


def email_gonder(to: str, konu: str, html: str) -> bool:
    if not RESEND_KEY:
        log.warning("RESEND_API_KEY yok — e-posta atlanıyor")
        return False
    try:
        r = requests.post(
            "https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {RESEND_KEY}", "Content-Type": "application/json"},
            json={"from": FROM_EMAIL, "to": [to], "subject": konu, "html": html},
            timeout=15,
        )
        if r.status_code in (200, 201):
            return True
        log.warning(f"Resend hata {r.status_code}: {r.text[:120]}")
        return False
    except Exception as e:
        log.warning(f"E-posta gönderme exception: {e}")
        return False


def main():
    if not SUPABASE_KEY:
        log.error("SUPABASE_SERVICE_KEY gerekli")
        return

    db = sb()
    simdi = datetime.now(timezone.utc)
    gun_once = (simdi - timedelta(days=1)).isoformat()

    # Aktif bültenleri çek
    try:
        r = db.table("bultenler").select(
            "id,kullanici_id,ad,filtre,frekans,email_aktif,son_gonderim"
        ).eq("email_aktif", True).execute()
        bultenler = r.data or []
    except Exception as e:
        log.error(f"Bülten listesi alınamadı: {e}")
        return

    if not bultenler:
        log.info("Aktif bülten yok, çıkılıyor")
        return

    log.info(f"{len(bultenler)} aktif bülten bulundu")
    kullanicilar = kullanici_email_map()

    toplam_gonderilen = 0

    for bulten in bultenler:
        bid       = bulten["id"]
        uid       = bulten["kullanici_id"]
        ad        = bulten["ad"]
        filtre    = bulten.get("filtre") or {}
        frekans   = bulten.get("frekans", "gunluk")
        son_g     = bulten.get("son_gonderim")

        # Haftalık bülten: son 7 gün
        if frekans == "haftalik":
            since = (simdi - timedelta(days=7)).isoformat()
        else:
            since = son_g or gun_once

        # Kullanıcı bilgisi
        kinfo = kullanicilar.get(str(uid))
        if not kinfo:
            log.debug(f"Bülten {bid}: kullanıcı {uid} bulunamadı, atlanıyor")
            continue

        # Eşleşme bul
        eslesme = eslesme_bul(db, filtre, since)
        log.info(f"Bülten '{ad}' ({uid[:8]}…): {len(eslesme)} eşleşme")

        if not eslesme:
            continue

        # E-posta gönder
        html = bulten_email_html(kinfo["ad"], ad, filtre, eslesme)
        konu = f"⭐ {ad} — {len(eslesme)} yeni ihale | İhaleGlobal"
        ok   = email_gonder(kinfo["email"], konu, html)

        if ok:
            # son_gonderim güncelle
            try:
                db.table("bultenler").update(
                    {"son_gonderim": simdi.isoformat(), "guncelleme": simdi.isoformat()}
                ).eq("id", bid).execute()
            except Exception as e:
                log.warning(f"son_gonderim güncellenemedi {bid}: {e}")
            toplam_gonderilen += 1
            log.info(f"  ✓ E-posta gönderildi → {kinfo['email']}")

    log.info(f"Bülten gönderimi tamamlandı. {toplam_gonderilen}/{len(bultenler)} bülten gönderildi.")


if __name__ == "__main__":
    main()
