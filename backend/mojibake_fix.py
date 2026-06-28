"""
Mevcut DB kayıtlarındaki Türkçe karakter bozulmasını (mojibake) düzeltir.
Örn: "Ä°stanbul" → "İstanbul", "ÅŸehir" → "şehir"

Kullanım:
    python mojibake_fix.py --dry-run   # sadece listele, değiştirme
    python mojibake_fix.py             # düzelt ve kaydet
    python mojibake_fix.py --limit 100 # ilk 100 kayıt
"""

import os, sys, argparse
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

try:
    from supabase import create_client
except ImportError:
    print("✗ supabase kurulu değil: pip install supabase")
    sys.exit(1)

SUPA_URL     = os.environ.get("SUPABASE_URL", "")
SUPA_SERVICE = os.environ.get("SUPABASE_SERVICE_KEY", "")
sb = create_client(SUPA_URL, SUPA_SERVICE)

def duzelt(s: str | None) -> str | None:
    if not s:
        return s
    try:
        fixed = s.encode("latin-1").decode("utf-8")
        if any(c in fixed for c in "çğıöşüÇĞİÖŞÜ"):
            return fixed
    except (UnicodeEncodeError, UnicodeDecodeError):
        pass
    return s

def bozuk_mu(s: str | None) -> bool:
    """Latin-1/UTF-8 karışık encode belirtisi olan karakterler var mı."""
    if not s:
        return False
    belirtiler = ["Ã", "Ä", "Å", "ÅŸ", "Ä°", "Ã¶", "Ã¼", "Ã§", "ÄŸ", "Ä±"]
    return any(b in s for b in belirtiler)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="Listele ama kaydetme")
    parser.add_argument("--limit", type=int, default=0, help="Kaç kayıt işlensin (0=tümü)")
    args = parser.parse_args()

    print(f"\n{'='*55}")
    print(f"Mojibake Fix — {'DRY RUN' if args.dry_run else 'CANLI'}")
    print(f"{'='*55}\n")

    # Bozuk kayıtları çek (baslik veya idare'de mojibake belirtisi)
    offset, bozuk_toplam, duzeltilen = 0, 0, 0
    while True:
        q = sb.table("ilanlar").select("id,baslik,idare,il").range(offset, offset + 999)
        if args.limit:
            q = sb.table("ilanlar").select("id,baslik,idare,il").limit(args.limit)
        res = q.execute()
        kayitlar = res.data or []
        if not kayitlar:
            break

        for k in kayitlar:
            baslik_bozuk = bozuk_mu(k.get("baslik"))
            idare_bozuk  = bozuk_mu(k.get("idare"))
            il_bozuk     = bozuk_mu(k.get("il"))

            if not (baslik_bozuk or idare_bozuk or il_bozuk):
                continue

            bozuk_toplam += 1
            yeni_baslik = duzelt(k["baslik"]) if baslik_bozuk else k["baslik"]
            yeni_idare  = duzelt(k["idare"])  if idare_bozuk  else k["idare"]
            yeni_il     = duzelt(k["il"])     if il_bozuk     else k["il"]

            if args.dry_run:
                if baslik_bozuk:
                    print(f"  baslik: {k['baslik'][:50]!r}")
                    print(f"       → {yeni_baslik[:50]!r}")
            else:
                sb.table("ilanlar").update({
                    "baslik": yeni_baslik,
                    "idare":  yeni_idare,
                    "il":     yeni_il,
                }).eq("id", k["id"]).execute()
                duzeltilen += 1

        if len(kayitlar) < 1000 or args.limit:
            break
        offset += 1000

    print(f"\nBozuk kayıt: {bozuk_toplam}")
    if not args.dry_run:
        print(f"Düzeltilen:  {duzeltilen}")
    else:
        print("(dry-run — hiçbir şey değiştirilmedi)")

if __name__ == "__main__":
    main()
