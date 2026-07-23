#!/usr/bin/env python3
"""kategori_model_uygula.py — lokal sınıflandırıcıyı jenerik kova satırlarına uygular (API'siz).

kategori_model_egit.py ile eğitilen modeli kullanır. GÜVEN EŞİĞİ altındaki tahminler YAZILMAZ
(satır 'Diğer' kalır) — yanlış kategoriye atmaktansa boş bırakmak yeğdir.

Ölçüm (23 Tem): etiketli test %92,5 doğruluk; ZOR ('Diğer') popülasyonda Gemini ile eşik 0.70'te
%89,2 uyum / %88,5 kapsama. Maliyet: $0 (Gemini'de aynı iş ~$30/962K).

Akış (1M satır için verimli): psql COPY ile aday dışa aktar → chunk'lar hâlinde tahmin →
geçici tabloya COPY → tek UPDATE ... FROM ile yaz.

Kullanım:
  python kategori_model_uygula.py --tablo dogrudan_temin_ilanlari --esik 0.70
  python kategori_model_uygula.py --tablo ilanlar --esik 0.70 --kuru   # yazma, sadece rapor
"""
import argparse, csv, os, subprocess, sys, tempfile, time
import joblib
import numpy as np

MODEL_YOL = "/opt/ihale-platform/backend/kategori_model.joblib"
JENERIK = ("Diğer", "Mal Alımı", "Hizmet Alımı")


def psql(sql, cikti=None):
    """docker exec psql çalıştırır; cikti verilirse STDOUT dosyaya yazılır."""
    cmd = ["docker", "exec", "-i", "supabase-db", "psql", "-U", "postgres", "-d", "postgres", "-c", sql]
    if cikti:
        with open(cikti, "w", encoding="utf-8") as f:
            return subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, text=True)
    return subprocess.run(cmd, capture_output=True, text=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tablo", default="dogrudan_temin_ilanlari")
    ap.add_argument("--esik", type=float, default=0.70)
    ap.add_argument("--kuru", action="store_true", help="yazma, sadece dağılım raporla")
    ap.add_argument("--chunk", type=int, default=100_000)
    args = ap.parse_args()

    t0 = time.time()
    jen = ",".join(f"'{k}'" for k in JENERIK)
    aday_csv = "/tmp/kategori_aday.csv"
    print(f"→ Aday satırlar dışa aktarılıyor ({args.tablo})…")
    r = psql(
        f"COPY (SELECT id, baslik FROM public.{args.tablo} "
        f"WHERE (kategori IS NULL OR kategori IN ({jen})) AND baslik IS NOT NULL AND length(baslik)>5) "
        f"TO STDOUT WITH (FORMAT CSV)", aday_csv)
    if r.returncode != 0:
        print("✗ COPY hatası:", r.stderr[:300]); sys.exit(1)

    ids, basliklar = [], []
    with open(aday_csv, newline="", encoding="utf-8") as f:
        for s in csv.reader(f):
            if len(s) >= 2 and len(s[1]) > 5:
                ids.append(s[0]); basliklar.append(s[1])
    print(f"  aday: {len(ids):,}")
    if not ids:
        print("Aday yok."); return

    m = joblib.load(MODEL_YOL)
    vec, clf = m["vec"], m["clf"]
    print(f"→ Tahmin (eşik {args.esik})…")

    yazilacak = []   # (id, kategori)
    dagilim = {}
    for i in range(0, len(basliklar), args.chunk):
        parca = basliklar[i:i + args.chunk]
        V = vec.transform(parca)
        P = clf.predict(V)
        O = clf.predict_proba(V).max(axis=1)
        for j, (p, o) in enumerate(zip(P, O)):
            if o >= args.esik:
                yazilacak.append((ids[i + j], p))
                dagilim[p] = dagilim.get(p, 0) + 1
        print(f"  {min(i+args.chunk, len(basliklar)):,}/{len(basliklar):,} işlendi ({time.time()-t0:.0f}s)")

    kaps = 100.0 * len(yazilacak) / len(ids)
    print(f"\n✓ Eşiği geçen: {len(yazilacak):,} / {len(ids):,} (kapsama %{kaps:.1f})")
    print("— En çok atanan 10 kategori —")
    for k, v in sorted(dagilim.items(), key=lambda t: -t[1])[:10]:
        print(f"  {v:>8,}  {k[:60]}")

    if args.kuru:
        print("\n(kuru çalışma — yazılmadı)"); return

    # Geçici tablo + tek UPDATE (1M satır için en hızlı yol)
    tah_csv = "/tmp/kategori_tahmin.csv"
    with open(tah_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerows(yazilacak)

    # ⚠️ SUNUCU-TARAFLI `COPY ... FROM '/yol'` KULLANMA: Supabase'de `postgres` superuser DEĞİL
    # (bkz. [[studio-3000-exposure]] dersi) → izin hatası verir. COPY FROM STDIN kullanılır.
    # Ayrıca TEMP tablo psql oturumları arasında yaşamaz → normal tablo + sonda DROP.
    print("\n→ Veritabanına yazılıyor (staging tablo + COPY STDIN + UPDATE FROM)…")
    r = psql("DROP TABLE IF EXISTS _kat_tahmin; CREATE TABLE _kat_tahmin(id uuid, kategori text);")
    if r.returncode != 0:
        print("✗ staging hatası:", r.stderr[:300]); sys.exit(1)

    with open(tah_csv, "rb") as f:
        p = subprocess.run(["docker", "exec", "-i", "supabase-db", "psql", "-U", "postgres",
                            "-d", "postgres", "-c", "COPY _kat_tahmin FROM STDIN WITH (FORMAT CSV)"],
                           stdin=f, capture_output=True, text=True)
    print("  ", (p.stdout.strip() or p.stderr.strip())[:150])
    if p.returncode != 0:
        print("✗ COPY hatası"); sys.exit(1)

    r = psql(f"UPDATE public.{args.tablo} t SET kategori = p.kategori FROM _kat_tahmin p "
             f"WHERE t.id = p.id AND (t.kategori IS NULL OR t.kategori IN ({jen}));")
    print("  ", (r.stdout.strip() or r.stderr.strip())[:200])
    psql("DROP TABLE IF EXISTS _kat_tahmin;")
    print(f"✓ Bitti ({time.time()-t0:.0f}s)")


if __name__ == "__main__":
    main()
