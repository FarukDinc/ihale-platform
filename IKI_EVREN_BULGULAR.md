# İKİ EVREN — Dikiş-Hatası Bulguları (bug-avı, 5 Ağu 2026)

> Kaynak: `iki-evren-bug-avi` workflow (4 denetim ajanı). Reçete: `IKI_EVREN.md`.
> Durum: ✅ düzeltildi · ⏳ sıradaki · 📋 bekliyor

## 3 tema
1. **TOPLAMA** — "İkisi/Birlikte" görünümlerinde ihale cirosu (milyon) + DT bedeli (~₺37K medyan) TEK sayıya toplanıyor → yanıltıcı. (Kural 3 ihlali.)
2. **DT-ONLY KAYBOLUYOR** — firma+kurum "birleşik" dizinleri ihale-çıpalı LEFT JOIN → yalnız-DT firma/kurum listede YOK (ama KPI UNION ile sayıyor → KPI↔liste tutarsız).
3. **İSİM-ANAHTAR** — `normalize_firma`/`detsis_no` yerine ham ad ile eşleşme → varyant sessiz-0 veya ikiye bölünmüş; ayrıca v1-harita/v1-sektorler DT evrenini hiç göstermiyor.

## Öncelikli liste

| # | Yer | Desen | Sorun | Düzeltme | Efor |
|---|---|---|---|---|---|
| B1 | `migration_firma_ozet_modlar.sql:39` + `firma_dizin_birlikte` (4 dosya senkron) | toplama | ciro+bedel tek "Toplam Ciro"; sıralama anahtarı da toplam | İhale ciro / DT bedel **ayrı alan**; sıralama tek-evren üzerinden; 4 tanım senkron | ~1g |
| B2 | `firma_dizin_birlikte` (:29) + `idare_dizin_json` (:38) | tek-evren | ihale-çıpalı LEFT JOIN → yalnız-DT firma/kurum yok | **FULL OUTER JOIN** (firma: normalize_ad=firma_norm; kurum: idare_ozet⟗dt_idare_ozet) | ~1g |
| ✅ B3 | `v1-kurum-analiz.html:1449` | tek-evren | idare_dizin_json DT alanları dönüyor ama map r[4]/r[5] düşürüyor | ✅ Map+tablo+KPI'ya DT + DETSİS dedup eklendi (5 Ağu) | ~1-2s |
| B4 | `migration_idare_dedup_detsis.sql:39` (idare_dizin_json) | isim-anahtar | DT/harcama İSİMLE join → ad varyantında sessiz-0 | `dt_idare_ozet_mv`+`idare_harcama_mv`'ye detsis_no ekle, detsis ile join | ~0.5g |
| ✅ B5 | `v1-kurum-analiz.html` kurum_ozet/kurum_dt_ozet + 4 sorgu | isim-anahtar | KURUM=ad `ilike('idare')` → birleşmiş kurumun tek varyantı | ✅ kurum_ozet/kurum_dt_ozet +p_detsis, KURUM_DETSIS wiring, 4 sorgu `.filter(detsis eq)`, v1-kurumlar link (5 Ağu). **analiz_pivot(firma) = B5b (dinamik SQL, ayrı)** | ~0.5g |
| B6 | `v1-harita.html:690,787` | tek-evren | harita+firma yoğunluğu yalnız İhale; `il_sektor_ozet_dt` çağrılmıyor | v1-firma-analiz İhale/DT toggle desenini kopyala | ~1g |
| B7 | `v1-sektorler.html:87` | tek-evren | `kategori_sayim` yalnız İhale; DT sektör yok | `kategori_sayim_dt` ekle, İhale/DT ayrı kolon | ~0.5g |
| B8 | `migration_uygun_firmalar_v3_3.sql:67` | isim-anahtar | `GROUP BY kazanan_firma` (ad) → firma ikiye bölünür | `GROUP BY normalize_firma(...)` | ~2s |
| ✅ B9 | `migration_firmam_dt_destek.sql:85` (firma_dt_icin_acik_ihaleler) | isim-anahtar | DT firma profili `kazanan_firma=ad` → varyat kaçar | ✅ `normalize_firma(...)` (5 Ağu; idx_dt_sonuc_firma_norm) | ~1s |
| ✅ B10 | `migration_kurum_dt_ozet.sql:68` | isim-anahtar | top-12 kazanan `GROUP BY kazanan_firma` (ad) | ✅ `GROUP BY normalize_firma` + array_agg görünen ad (5 Ağu, B5 ile) | ~1s |

## Spekülatif / düşük (muhtemelen bilinçli)
- `kurum_ozet.sql:39` jenerik-ad substring (81 "İl Sağlık Müd." tek kova) — detsis'e geçiş büyük yeniden tasarım.
- `firma-analiz.html:1163` legacy sayfa (v1-firma-analiz kanonik) — kullanılmıyorsa kaldır/yönlendir.
- `v1-uyumluluk.html:570` uygun-ihale yalnız İhale — DT sekmesi veya başlık notu.
- `takip_sektorler.sql:36` takip yalnız İhale — bilinçli olabilir, UI'da belirt.
