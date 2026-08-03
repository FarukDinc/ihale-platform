# UV-6 — Kurum Merkezi + Firmalar yeniden tasarım notu (rakip ihalepro örnekli)

> Durum: **tasarım notu** (kod öncesi). Rakip: `app.ihalepro.com`. İnceleme 3 Ağu 2026.
> Kural: logo/marka/metin KOPYALANMAZ, yalnız yapı/akış örnek alınır.

## 1. Rakip (ihalepro) yapısı — gözlem
**Kurum Merkezi (2 seviye, düz):**
- **Kurumlar** = ~36 ÜST KATEGORİ (5018 sayılı Kanun cetvel mantığı): bakanlıklar (ADALET, İÇİŞLERİ, ÇEVRE…) + işlevsel gruplar: **BELEDİYELER, KİTLER, İL ÖZEL İDARELERİ, MAHALLİ İDARE BİRLİKLERİ, DÖNER SERMAYE, DİĞER ÖZEL BÜTÇELİ, 5018 KAPSAMI DIŞINDAKİ DİĞER İDARELER, DİĞER**.
- **İdareler** = 50.630 tekil idare (alt seviye, ayrı sekme).
- Her kategori/idare kartı: Aktif İhale · Geçmiş İhale · Sözleşme · Toplam Tutar (çok para birimi/yıl).
- Breadcrumb "Kurum Merkezi"; sol menüde Kurumlar → {Tüm Kurumlar, Tüm İdareler}.

**Firmalar:** 443.258 firma (**ihale ∪ DT birleşik evren**) + **Parlayan Yıldızlar** (1.883) segmenti; kart metrikleri İhale/Sözleşme/Tutar; misafirde `*****` maskeli.

## 2. Bizim mevcut yapı — harita
| Sayfa | Ne var | Kaynak |
|---|---|---|
| `v1-kurumlar` | Basit "İşveren Kurumlar" listesi (Tüm/Takip; sütun: idare, il, toplam/aktif ihale, **toplam/aktif DT**) | `idare_dizin_json()` (idare_ozet_mv) |
| `v1-kurum-analiz ?gorunum=liste` | İdare Dizini: KPI (Toplam/Aktif İdare, Toplam/Aktif İhale) + filtre + tablo | `idare_dizin_json()` |
| `v1-kurum-analiz ?gorunum=agac` | **DERİN DETSİS AĞACI** (bakanlık→GM→taşra, tembel dal, kapsama %, "Bağlantısız Kurumlar" kovası) | `idare_agac_dallar/ara/yol/bagsiz_*`, `idare_dal_son_ihaleler/dt` (detsis_no+ust, kendi/dal ihale+DT) |
| `v1-kurum-analiz ?kurum=` | Tek-kurum analizi: ihale+DT KPI, sekmeler, İhale⇄DT | `kurum_ozet`, `kurum_dt_ozet`, `analiz_pivot` |
| `v1-firma-analiz` | Firma dizini (liste/harita, **İhale/DT/İkisi** mod) + detay | `yuklenici_ozet/firma_ozet_dt/birlikte`, `firma_dizin_dt/birlikte`, harita RPC'leri |
| `v1-firmalar` | Basit Yüklenici Firmalar (segment: Parlayan/Sönen/İlk Kez/150Mn+) + #2 DT ekleri | `yukleniciler` + `firma_dt_toplu/firma_dizin_dt` |

## 3. Boşluk (rakip ↔ biz)
- ✅ **Firma tarafı zaten hizalı/önde:** ihale∪DT birleşik (#2 ile), segmentler, il haritası. Rakip 443K = DT dahil; biz de DT'yi kattık. Ufak: birleşik firma sayısını (ihale∪DT) tek KPI olarak göster.
- ✅ **Derin ağaç bizde VAR ve rakipten zengin** (DETSİS, kapsama %, bağlantısız kovası).
- ❌ **EKSİK 1:** Temiz **~36 kategorili "Kurumlar" girişi** yok (5018 taksonomisi). Kullanıcı 50K idareyi tek listede/derin ağaçta buluyor; rakibin sunduğu "bakanlık/BELEDİYELER/KİTLER…" üst-kırılım LANDING'i yok.
- ❌ **EKSİK 2:** Kurumlar 2 sayfaya bölük (`v1-kurumlar` liste + `v1-kurum-analiz` ağaç/analiz). Rakip tek "Kurum Merkezi" çatısı (Kurumlar / İdareler sekmeleri).

## 4. Öneri (en iyi = ikisinin birleşimi)
**"Kurum Merkezi" tek çatı** — 3 görünüm, tek sayfa/menü:
1. **Kurumlar (VARSAYILAN)** = ~36 üst kategori kartı (5018 cetveli): bakanlıklar + BELEDİYELER/KİTLER/İL ÖZEL/MAHALLİ İDARE BİRLİKLERİ/DÖNER SERMAYE/5018-dışı/DİĞER. Her kart: aktif/geçmiş ihale + DT + sözleşme + tutar. Kategoriye tıkla → o kategorinin idareleri.
2. **İdareler** = tüm tekil idareler (mevcut İdare Dizini; arama+filtre).
3. **Ağaç (gelişmiş)** = mevcut DETSİS derin ağacı (olduğu gibi — güçlü fark).

**Yeni gereken tek şey: `kurum_kategori` (5018 taksonomi) katmanı** — her idareyi ~36 kategoriye eşleyen sınıflandırma + kategori-özet RPC (`kurum_kategori_ozet()`). Taban: mevcut `idare_tur` sınıflandırıcı (813K sınıflı, bkz [[idare-tur-siniflandirici]]) 5018 kovalarına haritalanır; belediye/İÖİ/KİT zaten türden çıkar.

**Firma tarafı:** büyük yapı hazır; yalnız (a) birleşik firma sayısı KPI'ı, (b) liste/dizinde İhale/DT/İkisi mod tutarlılığı (firma-analiz'de var, v1-firmalar'a taşınabilir).

## 5. Fazlar
- **Faz A (backend):** `kurum_kategori` eşleme (idare_tur→5018 kova) + `kurum_kategori_ozet()` RPC (kategori başına ihale/DT/sözleşme/tutar) + kategori→idare listesi RPC.
- **Faz B (frontend):** `v1-kurumlar`'ı "Kurum Merkezi"ne dönüştür: Kurumlar (kategori kartları) / İdareler / Ağaç sekmeleri; v1-kurum-analiz ağaç+analiz olduğu gibi hedef.
- **Faz C:** Firma tarafı ufak hizalama (birleşik sayı + mod tutarlılığı).

## 6. Karar bekleyen
- Taksonomi: rakibin ~36 5018-kategorisi birebir mi, yoksa bizim idare_tur kovalarımızla mı? (öneri: 5018 cetveli + belediye/KİT/İÖİ + DİĞER — rakiple aynı zihinsel model)
- Derin DETSİS ağacı KALSIN (gelişmiş sekme) — öneri: evet, silme; kategori-landing onun üstüne eklenir.
