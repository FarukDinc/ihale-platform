#!/usr/bin/env python3
"""kategori_model_egit.py — LOKAL kategori sınıflandırıcısı (API'siz, ücretsiz).

NEDEN: jenerik "Diğer/Mal Alımı/Hizmet Alımı" kovasındaki ilanları kanonik 41 kategoriye
oturtmak için Gemini kullanıyorduk (~$18/567K + her gece süregelen maliyet). Elimizde
1,39M ETİKETLİ örnek (başlık → kategori) var → kendi sınıflandırıcımızı eğitip aynı işi
SIFIR API maliyetiyle yapabiliriz. DT tarafındaki 962K "Diğer" için de aynı model kullanılır.

Eğitim verisi: ilanlar'dan kategori NOT IN (jenerik kovalar) olan satırlar (psql COPY ile CSV).
Model: TF-IDF (kelime 1-2gram + karakter 3-5gram) → SGDClassifier(modified_huber).
  · char n-gram Türkçe ekleri/yazım varyantlarını yakalar (kısa, gürültülü başlıklarda kritik)
  · modified_huber → predict_proba var → GÜVEN EŞİĞİ uygulanabilir (emin değilse 'Diğer' kalsın)

Kullanım:
  python kategori_model_egit.py                 # eğit + değerlendir + kaydet
  python kategori_model_egit.py --esik 0.55     # farklı güven eşiğiyle kapsama/doğruluk raporu
"""
import argparse, csv, sys, time
import joblib
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import SGDClassifier
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split
from sklearn.pipeline import FeatureUnion

CSV_YOL   = "/tmp/kategori_egitim.csv"
MODEL_YOL = "/opt/ihale-platform/backend/kategori_model.joblib"


def veri_yukle(yol):
    basliklar, kategoriler = [], []
    with open(yol, newline="", encoding="utf-8") as f:
        for satir in csv.reader(f):
            if len(satir) < 2:
                continue
            b, k = satir[0].strip(), satir[1].strip()
            if len(b) > 5 and k:
                basliklar.append(b)
                kategoriler.append(k)
    return basliklar, kategoriler


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--esik", type=float, default=0.50, help="güven eşiği (altı 'Diğer' bırakılır)")
    ap.add_argument("--ornek", type=int, default=0, help="hızlı deneme için örneklem (0=tümü)")
    args = ap.parse_args()

    t0 = time.time()
    X, y = veri_yukle(CSV_YOL)
    print(f"→ Eğitim verisi: {len(X):,} başlık · {len(set(y))} kategori")
    if args.ornek and args.ornek < len(X):
        idx = np.random.RandomState(42).choice(len(X), args.ornek, replace=False)
        X = [X[i] for i in idx]; y = [y[i] for i in idx]
        print(f"  (örneklem: {len(X):,})")

    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.03, random_state=42, stratify=y)
    print(f"  eğitim {len(Xtr):,} / test {len(Xte):,}")

    # Kelime + karakter n-gram birleşimi: kelime anlamı + Türkçe ek/yazım varyantı
    vec = FeatureUnion([
        ("kelime", TfidfVectorizer(analyzer="word", ngram_range=(1, 2), min_df=3,
                                   max_features=300_000, sublinear_tf=True, lowercase=True)),
        ("karakter", TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), min_df=5,
                                     max_features=300_000, sublinear_tf=True, lowercase=True)),
    ])
    print("→ TF-IDF üretiliyor…")
    Xtr_v = vec.fit_transform(Xtr)
    print(f"  boyut: {Xtr_v.shape} ({time.time()-t0:.0f}s)")

    print("→ Model eğitiliyor (SGD/modified_huber)…")
    clf = SGDClassifier(loss="modified_huber", alpha=1e-6, max_iter=12, tol=1e-4,
                        random_state=42, n_jobs=-1, class_weight="balanced")
    clf.fit(Xtr_v, ytr)

    Xte_v = vec.transform(Xte)
    tahmin = clf.predict(Xte_v)
    dogruluk = accuracy_score(yte, tahmin)
    print(f"\n✓ TEST DOĞRULUĞU (eşiksiz): {dogruluk:.4f}")

    # Güven eşiğiyle: emin olunanların doğruluğu + kapsama
    olas = clf.predict_proba(Xte_v)
    guven = olas.max(axis=1)
    for esik in (0.40, 0.50, 0.60, 0.70, 0.80):
        maske = guven >= esik
        if maske.sum() == 0:
            continue
        d = accuracy_score(np.array(yte)[maske], tahmin[maske])
        print(f"  eşik {esik:.2f} → kapsama %{100*maske.mean():.1f} · doğruluk {d:.4f}")

    print("\n— En zayıf 8 kategori (f1) —")
    rap = classification_report(yte, tahmin, output_dict=True, zero_division=0)
    siralı = sorted(((k, v["f1-score"], v["support"]) for k, v in rap.items()
                     if isinstance(v, dict) and k not in ("accuracy", "macro avg", "weighted avg")),
                    key=lambda t: t[1])
    for k, f1, sup in siralı[:8]:
        print(f"  {f1:.2f}  n={int(sup):>6}  {k[:60]}")

    joblib.dump({"vec": vec, "clf": clf, "dogruluk": dogruluk}, MODEL_YOL, compress=3)
    print(f"\n✓ Model kaydedildi: {MODEL_YOL} ({time.time()-t0:.0f}s toplam)")


if __name__ == "__main__":
    main()
