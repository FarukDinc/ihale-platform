# İKİ EVREN SÖZLEŞMESİ — İhale (4734) vs Doğrudan Temin

> Tek kaynak kural kitabı. Firma/kurum/sektör ekranı yapan HER geliştirici (insan veya AI) buna uyar.
> Amaç: iki ayrı veri evreninin (İhale + DT) dikişinde tekrar eden hataları (eksik taraf, yanlış toplama,
> ad-çakışması) bitirmek. Bkz. bellek `iki-evren-ihale-dt`.

## 1. İki evren nedir

Her varlık (firma / kurum / sektör / il) İKİ AYRI tablo-anahtar-MV setinde yaşar:

| | 📄 İhale (4734 sayılı) | ⚡ Doğrudan Temin |
|---|---|---|
| İlan | `ilanlar` | `dogrudan_temin_ilanlari` |
| Sonuç | `ihale_sonuclari` | `dogrudan_temin_sonuclari` |
| Firma özeti | `yukleniciler` | `firma_dt_toplam` |
| Kurum özeti | `idare_ozet_mv` / `idare_harcama_mv` | `dt_idare_ozet_mv` |
| Firma-eşleştirme | `firma_icin_acik_ihaleler` | `firma_dt_icin_acik_ihaleler` |
| Kurum kırılım | `analiz_pivot` (ihale) | `firma_dt_kirilim` / DT pivot |

**Ölçek FARKLI:** ihale sözleşmesi milyonlar; DT medyanı ~₺37K. → **ASLA toplanmaz** (ihaleciler.com toplar; biz toplamayız — yanıltır).

## 2. Kural 1 — KANONİK KİMLİK ANAHTARI (asla görünen ad)

Bir varlığı iki evrende eşleştirirken **görünen adı (`ad`) KULLANMA** — aynı firma iki defterde farklı yazılabilir
(ör. "BEL-PA…" vs "ANKARA BB - BEL-PA…"; ÜNTES en-yeni ihale yazımı ≠ en-yeni DT yazımı).

- **Firma:** `normalize_firma(ad)` → IMMUTABLE; A.Ş./LTD/SAN/TİC eklerini + noktalamayı eritir.
  Zaten hazır: `yukleniciler.normalize_ad` = `firma_dt_toplam.firma_norm` = `normalize_firma(kazanan_firma)`.
  **Join = `y.normalize_ad = d.firma_norm`.**
- **Kurum/idare:** `detsis_no` (DETSİS resmi kodu). İsim varyantı buna bağlanır.
- `tr_fold` (arama-fold) YALNIZ serbest-metin ARAMA içindir — şirket ekini SÖKMEZ → **varlık eşleştirmede kullanma.**

## 3. Kural 2 — STANDART EŞLİ VERİ ŞEKLİ

Bir varlığın iki-evren verisini döndüren her RPC şu şekli verir:

```
{ ad, il,
  has_ihale: bool, has_dt: bool,
  ihale: { sozlesme, ciro, … } | null,   // taraf yoksa null
  dt:    { sozlesme, bedel, … } | null }
```

Referans: `firmam_getir()` (bkz. `backend/migration_firmam_iki_evren.sql`). Geriye-dönük alanlar
(`firma_id`, `dt_mi`) korunur (eski tüketiciler: `js/firmam.js`, `v1-uyumluluk.html`).

## 4. Kural 3 — UI: DAİMA İKİ ETİKETLİ BLOK, ASLA TOPLAMA

- Üstte **📄 İhale** bölümü, altında **⚡ Doğrudan Temin** bölümü. Taraf yoksa o blok hiç basılmaz (`has_*` guard).
- **Tek "genel toplam" YOK.** Her blok kendi totalini gösterir. Ortalama/sayı yalnız kendi bloğu içinde
  (`(ih.ciro+dt.bedel)/…` **YASAK**).
- DOM id'leri namespace'li: ihale `v1-*`, DT `v1-dt-*` (aynı id'ye iki blok yazıp ezmesin).
- Rozet: firma İhale+DT ikisini de kazandıysa iki rozet (`İhale` + `⚡ DT`).

## 5. Yeni özellik kontrol listesi

- [ ] Varlığı iki evrende de aradım mı? (yalnız-DT firma/kurum kaçmasın)
- [ ] Eşleştirmeyi kanonik anahtarla mı yaptım? (`normalize_firma` / `detsis_no`, **ad değil**)
- [ ] İki tarafı AYRI mı gösteriyorum? Toplamadım mı?
- [ ] Taraf yoksa `has_*` ile guard'ladım mı? (boş RPC atmıyorum, boş blok basmıyorum)

## Referans uygulama
`firmam_getir()` (backend) + `v1-analiz.html` firma 2-parça paneli.
