# Rakip Analizi — ihaleciler.com (22 Tem 2026)

Chrome üzerinden girişli olarak sayfa sayfa incelendi. Karşılaştırma: **ihaleciler.com** (rakip) vs **ihaleglobal.com** (biz).

---

## 0. ÖZET — En kritik 3 fark
1. **Veri kaynağı & geçmiş derinliği:** Onlarda EKAP + **Gazete** + **İstihbarat** kaynağı ve **2,63M sözleşmeli DT** (geçmişe derin). Bizde EKAP + DMO/Jandarma/KA, DT ~1,5M ve sağlıklı kapsama ancak 2025-09'dan. → *(Backfill başlatıldı.)*
2. **Kalem/belge derinliği:** Her ihalede **Malzeme Listesi (kalem kalem ürün+miktar)** + 4 belge (İhale İlanı, Sonuç İlanı, İdari Şartname, Teknik Şartname). Bizde bu kalem/belge katmanı yok.
3. **Katılım/teklif verisi:** "Ort. katılımcı" ve "Ort. geçerli teklif" metrikleri var (sadece kazanan değil, TÜM katılımcı/teklif sayısı). Bizde sadece kazanan verisi var.

---

## 1. VERİ KAYNAĞI & KAPSAM

| | ihaleciler.com | Biz (ihaleglobal) |
|---|---|---|
| EKAP ihaleleri | ✅ 9.166/gün | ✅ |
| **Gazete ihaleleri** | ✅ 1.422/gün | ❌ |
| **İstihbarat ihaleleri** (ihbar/ön-duyuru) | ✅ 2.042/gün | ❌ |
| DMO / Jandarma / KA | (EKAP içinde) | ✅ |
| Sözleşmeli DT toplam | **2.629.472** | ~1.495.674 (2025-09'dan tam) |
| Uluslararası ihaleler (TED/AB, Gürcistan) | ❌ | ✅ **bizim avantajımız** |
| Dünya dış ticaret analizi | ❌ | ✅ **bizim avantajımız** |

---

## 2. ONLARDA OLUP BİZDE OLMAYAN (öncelik sırasıyla)

### 🔴 Yüksek değer
1. **Gazete + İstihbarat kaynakları** — EKAP dışı yerel gazete ilanları + ihbar/ön-duyuru. Kamu-dışı ihale fırsatları.
2. **Malzeme Listesi (kalem bazlı)** — her ihalenin içindeki ürün/malzeme kalemleri + adet (ör. "17 kalem"). Tedarikçi için altın değerinde: "kim tam olarak neyi, ne kadar alıyor".
3. **Katılım/teklif verisi** — "Ort. katılımcı", "Ort. geçerli teklif". İhaleye kaç firma girdi, kaç geçerli teklif verildi. Rekabet yoğunluğu analizi. (Bizde sadece kazanan var; katılımcı/kaybeden verisi yok.)
4. **Şartname & ilan belgeleri** — İhale İlanı, Sonuç İlanı, İdari Şartname, Teknik Şartname doğrudan erişim/indirme.

### 🟠 Orta değer
5. **Kayıtlı serbest aramalar ("Arama önerilerim")** — kullanıcı istediği anahtar kelimeyi (firma adı, ürün) kaydeder; her kayıt için hızlı aksiyonlar: Listele / Analiz / Bugün yayınlananlar / Bugün yapılacaklar / Yeni eklenenler. (Bizde profil-bazlı eşleştirme var ama serbest kayıtlı arama + bu hızlı aksiyonlar yok.)
6. **Okundu takibi ("Okuduklarım")** — hangi ihaleyi gördüğünü işaretler; "Okuduklarımı gizle/göster". Büyük hacimde çok pratik.
7. **On-demand "Analiz"** — HERHANGİ bir arama sonucuna (filtreli) Yıllık / Sektör / İdare kırılımı: ort. katılımcı, ort. geçerli teklif, devam eden, tamamlanan, ort. + toplam sözleşme bedeli. (Bizde analiz sabit sayfalarda, sorguya bağlı değil.)
8. **"Rapor"** — arama sonucunu rapor olarak dışa aktarma.
9. **Devam eden vs Tamamlanan iş ayrımı** — firma ve idare bazında aktif/süren işler ayrı gösteriliyor. (Bizde ciro/adet var ama aktif-tamamlanan ayrımı yok.)
10. **Sözleşme listem** — kullanıcının takip ettiği sözleşmeler ayrı liste.

### 🟡 Düşük değer / kozmetik
11. **TL + EUR sözleşme** — döviz cinsli sözleşmeler ayrı gösteriliyor (Kalyon ₺175B + €558M).
12. **Resmi iş-grubu sınıflandırma** — yüklenicileri KİK yapım iş grupları (A/B/C/D/E: köprü, tünel, bina, tesisat, enerji, haberleşme…) ile filtreleme.
13. **Benzer ihale geçmişi** (per-ihale) — bizim "benzer ihaleler"e benzer, mevcut.
14. **İçerik türü filtreleri** — Düzeltme İlanı / İptal İlanı / Zeyilname ayrı takip.
15. **Teklif türü filtreleri** — E-ihale, E-eksiltme, Kısmi teklif, Birim fiyat/Götürü bedel, Yerli/yabancı istekli.
16. **Favori (yıldız) + görüntülenme sayısı** — per-ihale.

---

## 3. BİZDE OLUP ONLARDA OLMAYAN (avantajlarımız — korunmalı)
- **Uluslararası ihaleler** (TED/AB + Gürcistan) — onlarda yok.
- **Dünya dış ticaret analizi** (Comtrade/WITS harita) — onlarda yok.
- **Harita** (firma yoğunluğu + açık RFQ, il bazlı) — onlarda yok.
- **e-Satınalma / RFQ pazaryeri** (alıcı-tedarikçi) — onlarda yok.
- **Profil-bazlı uyum skoru + eşleştirme** (uygun firmalar/benzer ihaleler motoru).
- **Modern UI + açık/koyu tema + mobil uyum** (onlar klasik/masaüstü-ağırlıklı, mavi-turuncu eski arayüz).
- **AI kategorizasyon** (jenerik→kanonik).

---

## 3.5 İŞ MODELİ & HESAP/GÜVENLİK (Hesabım sayfasından)

**İş modeli — süre-bazlı tek üyelik (kademe yok):**
- "Üyelik başvurusu 12 ay" ve "Üyelik yenileme 6 ay" ürünleri. Örnek fiyatlar: 12 ay ₺2.000 (2024), 6 ay ₺1.800 (Eki 2025), 6 ay ₺2.250 (Nis 2026) → **~₺3.600-4.500/yıl**, tek üyelik seviyesi.
- Ödeme: Kredi/Banka kartı. "Kalan süre: N gün" + "Süre uzat".
- Bizim modelimiz FARKLI: kademeli plan (Ücretsiz / standart ₺1.490 / kurumsal ₺3.990) + kredi/kupon. → Fiyat konumlandırması gözden geçirilebilir; onların tek-üyelik ~₺300-375/ay bandı.

**Hesap/güvenlik özellikleri (bizde eksik olabilecekler):**
- **2FA (iki aşamalı güvenlik)** — açılabilir.
- **Oturum yönetimi** — tüm aktif oturumlar (cihaz/IP/ilk-son giriş), tek tek veya toplu "sonlandır". Güçlü güvenlik + hesap paylaşımı kontrolü.
- **Çoklu firma profili** ("Profil ekle") — bir hesaba birden çok VKN/firma profili; çok-firmalı kullanıcı/müşavir için.
- **Fatura geçmişi + faturayı görüntüle** — düzgün faturalandırma akışı.
- **Site tercihleri:** dil, zaman dilimi, arama görünümü, mobil görünüm, tema (açık/koyu — onlarda da var).

---

## 4. ÖNCELİKLİ GELİŞTİRME YOL HARİTASI

| # | İş | Değer | Efor | Not |
|---|-----|-------|------|-----|
| 1 | **Tarihsel DT + ihale backfill** (2,6M'e ulaş) | 🔴 | Orta | Başladı (dt_list_backfill) |
| 2 | **Malzeme Listesi (kalem) çekimi** | 🔴 | Orta-Yüksek | ✅ **BİTTİ** — `ihtiyacKalemiOkasList` → `kalemler` jsonb, detay sayfasında kart |
| 3 | **Katılım/teklif verisi** (ort. katılımcı, geçerli teklif) | 🔴 | Orta | ✅ **BİTTİ** — detayda "Katılımcı: N (M geçerli teklif)" |
| 4 | **Şartname/ilan belge erişimi** (İdari+Teknik) | 🟠 | Orta | ✅ **BİTTİ** — EKAP doküman sayfası İKN ile değil iç hash ile açılıyordu; hash liste yanıtında zaten geliyordu → `ekap_ihale_id` kolonu (ek istek maliyeti YOK). İndirme/CAPTCHA/Storage'a gerek kalmadı. **Geçmiş de KAPANDI**: hash `ihale_sonuclari.tum_teklifler → sozlesme_bilgi.ihaleId` içinde zaten duruyormuş → tek UPDATE ile **336.289 ihale**, kapsam %0,07→%17,2, sıfır kazıma. Link doğrulandı (HTTP 302 → EKAP IlanDokumanDownload.aspx) |
| 5 | **Serbest kayıtlı aramalar + hızlı aksiyonlar** | 🟠 | Düşük-Orta | ✅ **BİTTİ** — `kayitli_aramalar` tablosu + `js/kullanici-veri.js` senkronu (localStorage birincil, DB senkron) |
| 6 | **Okundu takibi** | 🟠 | Düşük | ✅ **BİTTİ** — `ilan_okundu` tablosu, aynı senkron katmanı; artık cihazlar arası |
| 7 | **On-demand analiz** (aramaya bağlı) | 🟠 | Orta | ✅ **BİTTİ** — ihaleler'de "📊 Bu Aramayı Analiz Et" → filtreler URL ile rekabet-analizi'ne taşınıyor. Yol boyunca **sessiz hata bulundu ve düzeltildi**: rekabet-analizi kategori dropdown'ı eski taksonomiydi, 26 seçenekten 25'i `toplam:0` döndürüyordu |
| 8 | **Gazete + İstihbarat kaynakları** | 🟠 | Yüksek | Yeni scraper'lar (yerel gazete + ihbar); veri edinimi zor |
| 9 | Devam eden/tamamlanan ayrımı, TL+EUR, iş-grubu | 🟡 | ~~Düşük~~ **Orta** | ⛔ **VERİ ENGELİ (23 Tem ölçüldü)** — arayüz işi DEĞİL. `ihale_sonuclari`'nda `is_baslama_tarihi` / `is_bitis_tarihi` / `is_suresi_gun` **539.203 satırın hepsinde NULL**, `ham_json` da %100 boş → ayrım türetilemez. Önce scraper'ın sonuç detayından bu alanları çekmesi gerek. Boş/uydurma sütun EKLENMEDİ. TL+EUR: sözleşmelerde para birimi kolonu yok (hepsi TL) — rakiptekinin karşılığı bizde yok |

---

## 5. İNCELENEN SAYFALAR (bu tur)
✅ Anasayfa (faceted browse + kayıtlı aramalar + günlük sayaçlar) · Yükleniciler (dizin + metrikler + iş-grupları) · İhale listesi & detay özellikleri (Sözleşme/Malzeme listesi + 4 belge + Benzer geçmiş) · Analiz aracı (yıllık/sektör/idare + katılım metrikleri) · Detaylı Ara (içerik/idare/kayıt-no) · **Hesabım** (iş modeli + 2FA/oturum/profil/fatura).

**İncelenmeyen (bir sonraki tur):** İdareler/Sektörler/Şehirler detay sayfaları (yüklenici deseniyle aynı olması muhtemel) · KİK Kararları · Bültenlerim/Bildirimler uyarı-yapılandırma detayı · Takip listem/Sözleşme listem/Okuduklarım (kişisel liste) · mobil uygulama / API varlığı.

*(Not: bazı butonlar (Bültenlerim, yüklenici Analiz) Chrome'da modal olarak açıldı ya da boş yüklendi; site büyük ölçüde form-tabanlı, doğrudan URL navigasyonu sık sık anasayfaya düşüyor. Girişli hesap: OMER FARUK DİNC / DİNÇ LAZER — kişisel veriler rapora dahil edilmedi.)*
