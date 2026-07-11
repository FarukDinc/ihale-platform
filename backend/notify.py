"""
İhaleGlobal — E-posta Bildirim Servisi

Akış:
  1. Supabase'den bildirim_email=true olan kullanıcıları çek
  2. Her kullanıcının takip ettiği ihalelerden deadline yaklaşanları bul
  3. Resend API ile HTML e-posta gönder
  4. bildirimler tablosuna kayıt yaz

Env:
  SUPABASE_URL, SUPABASE_SERVICE_KEY, RESEND_API_KEY

Kurulum:
  pip install supabase requests
"""

import os
import json
import requests
from datetime import datetime, timezone, timedelta
from supabase import create_client

SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://lpgelwfoarhouollhwur.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY", "")
RESEND_KEY   = os.environ.get("RESEND_API_KEY", "")

FROM_EMAIL   = os.environ.get("BILDIRIM_FROM_EMAIL", "noreply@ihaleglobal.com")
SITE_URL     = os.environ.get("SITE_URL", "https://ihaleglobal.com")


def sb_client():
    return create_client(SUPABASE_URL, SUPABASE_KEY)


def auth_email_map():
    """GoTrue admin API'sinden {user_id: email} haritası çek (service key ile).
    Sahte supabase wrapper auth.admin desteklemediği için doğrudan REST çağrısı."""
    if not SUPABASE_KEY:
        return {}
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
                print(f"❌ Auth listesi hatası {r.status_code}: {r.text[:120]}")
                break
            users = r.json().get("users", [])
            if not users:
                break
            for u in users:
                if u.get("email"):
                    emap[str(u["id"])] = u["email"]
            if len(users) < 200:
                break
            page += 1
    except Exception as e:
        print(f"❌ Auth listesi exception: {e}")
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
    return f"₺{v}"


def tarih_fmt(t):
    if not t:
        return "—"
    try:
        d = datetime.fromisoformat(str(t).replace("Z", "+00:00"))
        return d.strftime("%d.%m.%Y %H:%M")
    except Exception:
        return str(t)


def email_html(kullanici_adi, ihaleler):
    """Deadline yaklaşan ihaleler için HTML e-posta şablonu."""
    satirlar = ""
    for i in ihaleler:
        kalan = i["kalan_gun"]
        if kalan == 0:
            gun_etiketi = '<span style="background:#ef4444;color:white;padding:2px 8px;border-radius:4px;font-size:12px;font-weight:700;">BUGÜN SON GÜN</span>'
        elif kalan <= 3:
            gun_etiketi = f'<span style="background:#f97316;color:white;padding:2px 8px;border-radius:4px;font-size:12px;font-weight:700;">{kalan} GÜN KALDI</span>'
        else:
            gun_etiketi = f'<span style="background:#f59e0b;color:#1a1a1a;padding:2px 8px;border-radius:4px;font-size:12px;font-weight:700;">{kalan} gün kaldı</span>'

        satirlar += f"""
        <tr>
          <td style="padding:16px;border-bottom:1px solid #e5e7eb;">
            <div style="font-weight:600;color:#111827;margin-bottom:4px;">{i['baslik']}</div>
            <div style="font-size:13px;color:#6b7280;margin-bottom:8px;">{i['idare']} — {i['il'] or ''}</div>
            <div style="display:flex;gap:12px;align-items:center;flex-wrap:wrap;">
              {gun_etiketi}
              <span style="font-size:13px;color:#6b7280;">Son teklif: {tarih_fmt(i['son_teklif_tarihi'])}</span>
              <span style="font-size:13px;color:#6b7280;">Tahmini: {para_fmt(i.get('yaklasik_maliyet_min'))}</span>
            </div>
          </td>
          <td style="padding:16px;border-bottom:1px solid #e5e7eb;text-align:right;vertical-align:middle;">
            <a href="{SITE_URL}/ihale-detay?id={i['id']}"
               style="display:inline-block;background:#f59e0b;color:#1a1a1a;padding:8px 16px;border-radius:6px;text-decoration:none;font-size:13px;font-weight:700;">
              Detay →
            </a>
          </td>
        </tr>"""

    return f"""<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
<body style="margin:0;padding:0;background:#f3f4f6;font-family:Inter,Helvetica,sans-serif;">
  <table width="100%" cellpadding="0" cellspacing="0" style="background:#f3f4f6;padding:32px 16px;">
    <tr><td align="center">
      <table width="600" cellpadding="0" cellspacing="0" style="background:white;border-radius:12px;overflow:hidden;box-shadow:0 1px 3px rgba(0,0,0,0.1);">

        <!-- HEADER -->
        <tr>
          <td style="background:#0A1628;padding:24px 32px;">
            <span style="font-size:22px;font-weight:800;color:white;">İhale<span style="color:#F0A500;">Platform</span></span>
          </td>
        </tr>

        <!-- BAŞLIK -->
        <tr>
          <td style="padding:28px 32px 12px;border-bottom:1px solid #e5e7eb;">
            <h1 style="margin:0 0 8px;font-size:20px;font-weight:700;color:#111827;">
              ⏰ Son Teklif Tarihi Yaklaşıyor
            </h1>
            <p style="margin:0;font-size:14px;color:#6b7280;">
              Merhaba {kullanici_adi}, takip ettiğiniz {len(ihaleler)} ihale için son tarih yaklaşıyor.
            </p>
          </td>
        </tr>

        <!-- İHALE TABLOSU -->
        <tr>
          <td>
            <table width="100%" cellpadding="0" cellspacing="0">
              {satirlar}
            </table>
          </td>
        </tr>

        <!-- CTA -->
        <tr>
          <td style="padding:24px 32px;text-align:center;border-top:1px solid #e5e7eb;">
            <a href="{SITE_URL}/takipte"
               style="display:inline-block;background:#0A1628;color:white;padding:12px 28px;border-radius:8px;text-decoration:none;font-size:14px;font-weight:700;">
              Tüm Takip Listemi Gör →
            </a>
          </td>
        </tr>

        <!-- FOOTER -->
        <tr>
          <td style="padding:16px 32px;background:#f9fafb;border-top:1px solid #e5e7eb;">
            <p style="margin:0;font-size:12px;color:#9ca3af;text-align:center;">
              Bu e-postayı almak istemiyorsanız
              <a href="{SITE_URL}/bildirimler" style="color:#f59e0b;">bildirim tercihlerinizi güncelleyin</a>.
              <br>© 2026 İhaleGlobal
            </p>
          </td>
        </tr>

      </table>
    </td></tr>
  </table>
</body>
</html>"""


def resend_gonder(to_email, subject, html):
    """Resend API ile e-posta gönder. Başarılıysa True döndürür."""
    if not RESEND_KEY:
        print(f"  ⚠ RESEND_API_KEY yok — e-posta atlandı: {to_email}")
        return False
    try:
        r = requests.post(
            "https://api.resend.com/emails",
            headers={"Authorization": f"Bearer {RESEND_KEY}", "Content-Type": "application/json"},
            json={"from": FROM_EMAIL, "to": [to_email], "subject": subject, "html": html},
            timeout=15,
        )
        if r.status_code in (200, 201):
            return True
        print(f"  ✗ Resend hata {r.status_code}: {r.text[:120]}")
        return False
    except Exception as e:
        print(f"  ✗ Resend exception: {e}")
        return False


def bildirim_kaydet(sb, kullanici_id, baslik, icerik, ilan_id=None):
    """bildirimler tablosuna kayıt (şema: kullanici_id, tur, baslik, icerik, okundu, ilan_id, aksiyon_url)."""
    try:
        kayit = {
            "kullanici_id": kullanici_id,
            "tur": "ihale",
            "baslik": baslik,
            "icerik": icerik,
            "okundu": False,
        }
        if ilan_id:
            kayit["ilan_id"] = ilan_id
            kayit["aksiyon_url"] = f"/ihale-detay?id={ilan_id}"
        sb.table("bildirimler").insert(kayit).execute()
    except Exception as e:
        print(f"  ⚠ bildirim kayıt hatası: {e}")


def main():
    if not SUPABASE_KEY:
        print("❌ SUPABASE_SERVICE_KEY eksik")
        return

    sb = sb_client()
    simdi = datetime.now(timezone.utc)

    print("=" * 55)
    print("İHALE PLATFORM — Bildirim Servisi")
    print(f"Zaman: {simdi.strftime('%d.%m.%Y %H:%M:%S UTC')}")
    print("=" * 55)

    # E-posta bildirimleri açık kullanıcıları çek (profil tablosundan)
    try:
        profil_res = sb.table("profil").select(
            "user_id, firma_adi, bildirim_email, bildirim_son_teklif, bildirim_gun_oncesi"
        ).eq("bildirim_email", True).execute()
        kullanicilar = profil_res.data or []
    except Exception as e:
        print(f"❌ Profil çekme hatası: {e}")
        return

    print(f"E-posta bildirimi açık: {len(kullanicilar)} kullanıcı")

    # Auth kullanıcılarının e-postalarını GoTrue admin API'sinden al
    email_map = auth_email_map()

    gondeilen = 0
    for profil in kullanicilar:
        user_id = profil.get("user_id")
        email   = email_map.get(str(user_id))
        if not email:
            continue

        gun_oncesi = profil.get("bildirim_gun_oncesi") or 3
        esik_tarihi = simdi + timedelta(days=gun_oncesi)

        # Bu kullanıcının takip ettiği ihaleleri çek
        try:
            takip_res = sb.table("takipler").select("ilan_id").eq("kullanici_id", user_id).execute()
            ilan_ids = [r["ilan_id"] for r in (takip_res.data or [])]
        except Exception as e:
            print(f"  ⚠ {email} takip listesi hatası: {e}")
            continue

        if not ilan_ids:
            continue

        # Deadline yaklaşan ihaleleri filtrele
        try:
            ilan_res = sb.table("ilanlar").select(
                "id, baslik, idare, il, son_teklif_tarihi, yaklasik_maliyet_min"
            ).in_("id", ilan_ids).eq("durum", "aktif").lte(
                "son_teklif_tarihi", esik_tarihi.isoformat()
            ).gte("son_teklif_tarihi", simdi.isoformat()).execute()
            yaklaşan = ilan_res.data or []
        except Exception as e:
            print(f"  ⚠ {email} ihale sorgusu hatası: {e}")
            continue

        if not yaklaşan:
            continue

        # Gün sayısını ekle
        for ilan in yaklaşan:
            if ilan.get("son_teklif_tarihi"):
                try:
                    bitis = datetime.fromisoformat(str(ilan["son_teklif_tarihi"]).replace("Z", "+00:00"))
                    ilan["kalan_gun"] = max(0, (bitis.date() - simdi.date()).days)
                except Exception:
                    ilan["kalan_gun"] = 0

        kullanici_adi = profil.get("firma_adi") or email.split("@")[0]
        subject = f"⏰ {len(yaklaşan)} takip ihalende son tarih yaklaşıyor — İhaleGlobal"
        html = email_html(kullanici_adi, yaklaşan)

        print(f"\n  → {email}: {len(yaklaşan)} ihale yaklaşıyor")
        basarili = resend_gonder(email, subject, html)

        # Her ihale için bildirim kaydı
        for ilan in yaklaşan:
            kalan = ilan.get("kalan_gun", 0)
            baslik = f"{'Bugün son gün!' if kalan == 0 else f'{kalan} gün kaldı'}: {ilan['baslik'][:60]}"
            bildirim_kaydet(sb, user_id, baslik, ilan["baslik"], ilan["id"])

        if basarili:
            gondeilen += 1
            print(f"  ✓ E-posta gönderildi")

    print(f"\n{'='*55}")
    print(f"✅ {gondeilen}/{len(kullanicilar)} e-posta gönderildi")


if __name__ == "__main__":
    main()
