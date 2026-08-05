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
| ✅ B1 | `migration_firma_birlikte_iki_evren.sql` (firma_ozet/dizin_birlikte) | toplama | ciro+bedel tek "Toplam Ciro"; sıralama anahtarı da toplam | ✅ ihale ciro/sözleşme AYRI + DT bedel/sözleşme AYRI (hiç toplanmaz); sıralama `GREATEST(ihale,dt)`; KPI 2 ayrı kutucuk (İhale Cirosu / DT Bedeli); v1-firmalar+firma-analiz iki-değerli hücre (5 Ağu) | ~1g |
| ✅ B2 | `firma_dizin_birlikte` → FULL OUTER (firma tarafı) | tek-evren | ihale-çıpalı LEFT JOIN → yalnız-DT firma yok (213K/280K = %76!) | ✅ **FULL OUTER JOIN** normalize_ad=firma_norm → DT-only firmalar görünür; perf: `firma_kurum_norm` anti-join MV (19,3s→0,38s, önceki kırılganlığı da giderdi); gece cron'a refresh eklendi (5 Ağu). **Kurum tarafı (idare_dizin_json ⟗) = B2b, ayrı** | ~1g |
| ✅ B3 | `v1-kurum-analiz.html:1449` | tek-evren | idare_dizin_json DT alanları dönüyor ama map r[4]/r[5] düşürüyor | ✅ Map+tablo+KPI'ya DT + DETSİS dedup eklendi (5 Ağu) | ~1-2s |
| B4 | `migration_idare_dedup_detsis.sql:39` (idare_dizin_json) | isim-anahtar | DT/harcama İSİMLE join → ad varyantında sessiz-0 | `dt_idare_ozet_mv`+`idare_harcama_mv`'ye detsis_no ekle, detsis ile join | ~0.5g |
| ✅ B5 | `v1-kurum-analiz.html` kurum_ozet/kurum_dt_ozet + 4 sorgu | isim-anahtar | KURUM=ad `ilike('idare')` → birleşmiş kurumun tek varyantı | ✅ kurum_ozet/kurum_dt_ozet +p_detsis, KURUM_DETSIS wiring, 4 sorgu `.filter(detsis eq)`, v1-kurumlar link (5 Ağu). **analiz_pivot(firma) = B5b (dinamik SQL, ayrı)** | ~0.5g |
| ✅ B6 | `v1-harita.html:690` | tek-evren | harita sektör yoğunluğu yalnız İhale; `il_sektor_ozet_dt` çağrılmıyor | ✅ sektör katmanına İhale/DT toggle (h-smod, il_sektor_ozet↔il_sektor_ozet_dt, per-mod cache); il-panel firmaMod'u zaten vardı. `il_firma_dagilimi` (genel/KAYITLI firma) evren-bağımsız→dokunulmadı (5 Ağu) | ~1g |
| ✅ B7 | `v1-sektorler.html:87` | tek-evren | `kategori_sayim` yalnız İhale; DT sektör yok | ✅ `kategori_sayim_dt()` RPC (SECDEF anon-açık, dt_kategori_sayim_mv) + frontend "Doğrudan Temin" ayrı kolon (kategori anahtarında birleşir, toplanmaz) (5 Ağu) | ~0.5g |
| ✅ B8 | `migration_uygun_firmalar_v3_3.sql:67` | isim-anahtar | `GROUP BY kazanan_firma` (ad) → firma ikiye bölünür | ✅ her iki dal `GROUP BY normalize_firma` + array_agg görünen ad; dogrulandi 20/20 distinct, 0 cift (5 Ağu) | ~2s |
| ✅ B9 | `migration_firmam_dt_destek.sql:85` (firma_dt_icin_acik_ihaleler) | isim-anahtar | DT firma profili `kazanan_firma=ad` → varyat kaçar | ✅ `normalize_firma(...)` (5 Ağu; idx_dt_sonuc_firma_norm) | ~1s |
| ✅ B10 | `migration_kurum_dt_ozet.sql:68` | isim-anahtar | top-12 kazanan `GROUP BY kazanan_firma` (ad) | ✅ `GROUP BY normalize_firma` + array_agg görünen ad (5 Ağu, B5 ile) | ~1s |

## Spekülatif / düşük (muhtemelen bilinçli)
- `kurum_ozet.sql:39` jenerik-ad substring (81 "İl Sağlık Müd." tek kova) — detsis'e geçiş büyük yeniden tasarım.
- `firma-analiz.html:1163` legacy sayfa (v1-firma-analiz kanonik) — kullanılmıyorsa kaldır/yönlendir.
- `v1-uyumluluk.html:570` uygun-ihale yalnız İhale — DT sekmesi veya başlık notu.
- `takip_sektorler.sql:36` takip yalnız İhale — bilinçli olabilir, UI'da belirt.
