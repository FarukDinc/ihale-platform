#!/usr/bin/env python3
"""
Webshare "Proxy List" dosyasını .env satırlarına çevirir.

Webshare panelinden inen dosya şu formatta:
    ip:port:kullanici:sifre
    ip:port:kullanici:sifre
    ...

proxy_havuz.py ise kullanıcı/şifreyi AYRI bekler (100 proxy'nin hepsi aynı
kimlik bilgisini paylaşır), listede yalnız ip:port ister:
    PROXY_KULLANICI=...
    PROXY_SIFRE=...
    PROXY_LIST=ip1:port1,ip2:port2,...

Webshare IP havuzunu periyodik olarak tazeliyor; liste değiştiğinde bu script
yeniden çalıştırılır.

KULLANIM
────────
    # Sadece ekrana bas (kopyalayıp .env'e yapıştır):
    python proxy_list_hazirla.py ~/webshare.txt

    # Doğrudan backend/.env'i güncelle (varolan PROXY_* satırları değiştirilir):
    python proxy_list_hazirla.py ~/webshare.txt --env-yaz

GÜVENLİK: Bu script sırları EKRANA BASMAZ (--sirlari-goster verilmedikçe).
Webshare dosyasını repoya KOYMAYIN — kimlik bilgisi içerir ve .gitignore'da
yalnızca .env var.
"""

import argparse
import os
import re
import sys
from collections import Counter


def ayristir(yol: str):
    """Webshare dosyasını (ip, port, kullanici, sifre) listesine çevirir."""
    satirlar = []
    with open(yol, "r", encoding="utf-8", errors="replace") as f:
        for ham in f:
            s = ham.strip()
            if not s or s.startswith("#"):
                continue
            parca = s.split(":")
            if len(parca) < 2:
                print(f"  ⚠ atlandı (biçim tanınmadı): {s[:40]}", file=sys.stderr)
                continue
            ip, port = parca[0], parca[1]
            kul = parca[2] if len(parca) > 2 else ""
            sif = parca[3] if len(parca) > 3 else ""
            satirlar.append((ip, port, kul, sif))
    return satirlar


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("dosya", help="Webshare Proxy List dosyası (ip:port:kullanici:sifre)")
    ap.add_argument("--env-yaz", action="store_true", help="backend/.env dosyasını yerinde güncelle")
    ap.add_argument("--sirlari-goster", action="store_true", help="kullanıcı/şifreyi de ekrana bas")
    args = ap.parse_args()

    kayitlar = ayristir(args.dosya)
    if not kayitlar:
        print("✗ Dosyada geçerli satır yok.", file=sys.stderr)
        sys.exit(1)

    kullanicilar = {k for _, _, k, _ in kayitlar if k}
    sifreler = {s for _, _, _, s in kayitlar if s}
    if len(kullanicilar) > 1 or len(sifreler) > 1:
        print(f"✗ Listede {len(kullanicilar)} farklı kullanıcı / {len(sifreler)} farklı şifre var.\n"
              "  proxy_havuz.py tek ortak kimlik varsayıyor — bu liste desteklenmiyor.", file=sys.stderr)
        sys.exit(1)

    kullanici = next(iter(kullanicilar), "")
    sifre = next(iter(sifreler), "")
    ip_port = [f"{ip}:{port}" for ip, port, _, _ in kayitlar]

    # ── Havuz sağlığı: aynı /24 blokta yığılma ────────────────────────────────
    # Bu ÖNEMLİ: IP'lerin hepsi aynı /24'teyse "100 IP" görünse de karşı taraf
    # subnet bazlı engellerse hepsi BİRDEN düşer. Riskin gerçekte ne kadar
    # yayıldığını görmek için raporlanıyor.
    bloklar = Counter(".".join(ip.split(".")[:3]) for ip in [k[0] for k in kayitlar])
    print(f"→ {len(ip_port)} proxy okundu · {len(bloklar)} farklı /24 bloğu", file=sys.stderr)
    for blok, adet in bloklar.most_common(5):
        pay = adet / len(ip_port) * 100
        print(f"   {blok}.0/24 → {adet} IP (%{pay:.0f})", file=sys.stderr)
    if len(bloklar) == 1:
        print("   ⚠ TÜM IP'ler tek /24 bloğunda. Karşı taraf subnet bazlı engellerse\n"
              "     100'ü birden düşer — gerçek dağıtım göründüğünden zayıf.", file=sys.stderr)

    satirlar = [
        f"PROXY_KULLANICI={kullanici if args.sirlari_goster or args.env_yaz else '<dosyadaki 3. alan>'}",
        f"PROXY_SIFRE={sifre if args.sirlari_goster or args.env_yaz else '<dosyadaki 4. alan>'}",
        f"PROXY_LIST={','.join(ip_port)}",
    ]

    if not args.env_yaz:
        print("\n".join(satirlar))
        if not args.sirlari_goster:
            print("\n# (kullanıcı/şifre gizlendi — göstermek için --sirlari-goster)", file=sys.stderr)
        return

    env_yol = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    mevcut = ""
    if os.path.exists(env_yol):
        with open(env_yol, "r", encoding="utf-8") as f:
            mevcut = f.read()
        yedek = env_yol + ".yedek"
        with open(yedek, "w", encoding="utf-8") as f:
            f.write(mevcut)
        print(f"→ yedek alındı: {yedek}", file=sys.stderr)

    for satir in satirlar:
        anahtar = satir.split("=", 1)[0]
        desen = re.compile(rf"^{anahtar}=.*$", re.MULTILINE)
        if desen.search(mevcut):
            mevcut = desen.sub(satir.replace("\\", "\\\\"), mevcut)
        else:
            if mevcut and not mevcut.endswith("\n"):
                mevcut += "\n"
            mevcut += satir + "\n"

    with open(env_yol, "w", encoding="utf-8") as f:
        f.write(mevcut)
    print(f"✓ {env_yol} güncellendi ({len(ip_port)} proxy).", file=sys.stderr)


if __name__ == "__main__":
    main()
