/**
 * TEK DOĞRULUK KAYNAĞI — iş-dostu kategori taksonomisi (~41 kanonik).
 * kategori_siniflandir.py'nin ÜRETTİĞİ adlarla BİREBİR aynı olmalı; ilanlar.kategori /
 * uluslararasi_ihaleler.kategori / satinalma_talepleri.kategori hepsi bu adları saklar.
 * profil.html buradan besleniyor (eskiden 31 kısa anahtar kullanıyordu → uyumsuzdu).
 * `eski`: profil.sektorler'deki eski kısa anahtar (geri-uyum + migration eşlemesi için).
 */
window.KATEGORILER = [
  { kod: "Akaryakıt - Gazyakıt - Madeni Yağ",                    emoji: "⛽",  aciklama: "Yakıt ve yağ alımları",              eski: "akaryakit" },
  { kod: "Asansör - Yapı Otomasyon - Mekanik Güvenlik",         emoji: "🛗", aciklama: "Asansör, mekanik güvenlik sistemleri", eski: "asansor" },
  { kod: "Eğitim - Araştırma - Anket - Tercümanlık",            emoji: "📚", aciklama: "Kurs, anket, eğitim hizmetleri",     eski: "egitim" },
  { kod: "Elektronik - Bilgisayar - İletişim - Ölçü Aletleri",  emoji: "💻", aciklama: "Donanım, iletişim, ölçü aletleri",   eski: "elektronik" },
  { kod: "Endüstriyel Makine - Motor - Konveyör",               emoji: "⚙️", aciklama: "Sanayi makineleri, motor, konveyör", eski: "makine" },
  { kod: "Enerji - Aydınlatma - Sinyalizasyon - Elektrik Tesisatı", emoji: "⚡", aciklama: "Elektrik tesisatı, aydınlatma", eski: "enerji" },
  { kod: "Gayrimenkul - Arsa Satışı - Kantin",                  emoji: "🏠", aciklama: "Kiralama, arsa/işyeri satışı",       eski: "gayrimenkul" },
  { kod: "Gıda - Tarım Ürünleri - Yiyecek - İçecek",            emoji: "🌾", aciklama: "Gıda ürünleri, tarım malzemeleri",   eski: "gida" },
  { kod: "Hayvancılık - Veterinerlik - Hayvan Yemi",            emoji: "🐄", aciklama: "Hayvancılık, veterinerlik, yem",     eski: null },
  { kod: "Hazır Yemek - Lokantacılık",                          emoji: "🍽️", aciklama: "Toplu yemek, catering hizmetleri",   eski: "hazir_yemek" },
  { kod: "Hırdavat - Nalburiye - Metal ve Plastik",             emoji: "🔧", aciklama: "Nalburiye, metal ve plastik ürünler", eski: "hirdavat" },
  { kod: "İnşaat - Altyapı - Üstyapı - Yapım",                  emoji: "🏗️", aciklama: "Bina, yol, köprü, yıkım işleri",     eski: "insaat" },
  { kod: "İnşaat Malzemeleri",                                  emoji: "🧱", aciklama: "Yapı malzemeleri, hazır beton",      eski: null },
  { kod: "İş Sağlığı - İş Güvenliği ve Ekipmanları",           emoji: "⛑️", aciklama: "İSG ekipman, danışmanlık",          eski: "is_sagligi" },
  { kod: "İşletmecilik - İşçilik - Sosyal Hizmetler",          emoji: "👷", aciklama: "Sosyal hizmet, işçilik",             eski: "isletmecilik" },
  { kod: "Kanalizasyon - Boru - Su - Doğalgaz - Sıhhi Tesisat", emoji: "🚰", aciklama: "Boru, su, doğalgaz, sıhhi tesisat",  eski: "kanalizasyon" },
  { kod: "Kent Mobilyaları - Prefabrik - Doğramacılık",        emoji: "🪑", aciklama: "Kent mobilyası, prefabrik yapı",     eski: null },
  { kod: "Kimyasal Maddeler - Dezenfektan - Gübre",            emoji: "🧪", aciklama: "Kimyasal maddeler, gübre",           eski: "kimyasal" },
  { kod: "Klima - Soğutma - Isıtma - Havalandırma",            emoji: "❄️", aciklama: "HVAC, iklimlendirme",               eski: "klima" },
  { kod: "Madencilik - Sondaj - Doğal Kaynaklar",             emoji: "⛏️", aciklama: "Maden, sondaj, doğal kaynak",        eski: null },
  { kod: "Matbaa - Kırtasiye - Toner - Kartuş - Ambalaj",      emoji: "🖨️", aciklama: "Baskı, kırtasiye, ambalaj",         eski: "matbaa" },
  { kod: "Menkul Mallar - Araç ve Hurda Satışı",              emoji: "🚙", aciklama: "Araç ve hurda satış ihaleleri",      eski: null },
  { kod: "Mobilya - Beyaz Eşya - Mutfak - Züccaciye",         emoji: "🛋️", aciklama: "Büro mobilyaları, beyaz eşya",       eski: "mobilya" },
  { kod: "Mühendislik - Mimarlık - Danışmanlık",              emoji: "📐", aciklama: "Teknik danışmanlık, proje",          eski: "muhendislik" },
  { kod: "Nakliye - Servis - Taşımacılık",                    emoji: "🚚", aciklama: "Lojistik, kargo, servis",            eski: "nakliye" },
  { kod: "Odun - Kömür - Katıyakıt",                          emoji: "🪵", aciklama: "Yakacak, katı yakıt",                eski: null },
  { kod: "Ormancılık - Bahçıvanlık - Peyzaj",                 emoji: "🌳", aciklama: "Peyzaj, bahçıvanlık, ağaçlandırma",  eski: "tarim" },
  { kod: "Özel Güvenlik - Koruma - Bekçilik",                 emoji: "🛡️", aciklama: "Güvenlik, koruma, bekçilik",        eski: "guvenlik" },
  { kod: "Reklam - Tabela - Billboard - Tanıtım",             emoji: "📢", aciklama: "Reklam, tabela, tanıtım",            eski: null },
  { kod: "Sağlık - Medikal - İlaç - Kozmetik",               emoji: "🏥", aciklama: "Hastane, ilaç, kozmetik",            eski: "saglik" },
  { kod: "Sanat Eserleri - Müzik Aletleri - Heykel",         emoji: "🎨", aciklama: "Sanat eseri, müzik aleti",           eski: null },
  { kod: "Savunma Sanayi - Silah - Denizcilik - Havacılık",  emoji: "🛩️", aciklama: "Savunma, denizcilik, havacılık",    eski: null },
  { kod: "Sigortacılık - Mali ve Hukuki Hizmetler",          emoji: "⚖️", aciklama: "Hukuki ve mali hizmetler",          eski: "sigortacilik" },
  { kod: "Tekstil - Giyim - Spor Ekipmanları",               emoji: "👕", aciklama: "Kıyafet, spor ekipmanları",         eski: "tekstil" },
  { kod: "Temizlik - İlaçlama - Geri Dönüşüm",               emoji: "🧹", aciklama: "Temizlik, ilaçlama hizmetleri",      eski: "temizlik" },
  { kod: "Turizm - Organizasyon - Ödüllendirme",             emoji: "🎉", aciklama: "Organizasyon, turizm, etkinlik",     eski: null },
  { kod: "Taşıt - İş Makinesi - Yedek Parça",                emoji: "🚗", aciklama: "Araç, iş makinesi, yedek parça",     eski: "tasit" },
  { kod: "Tıbbi Cihaz - Laboratuvar - Hastane Ekipmanları",  emoji: "🔬", aciklama: "Lab malzemeleri, hastane ekipmanı",  eski: "tibbi_cihaz" },
  { kod: "Uydu Takip - Kamera - Scada - Haberleşme",         emoji: "📡", aciklama: "İzleme, haberleşme sistemleri",      eski: "uydu" },
  { kod: "Yangın Algılama - Söndürme",                       emoji: "🔥", aciklama: "Yangın ihbar ve söndürme sistemleri", eski: "yangin" },
  { kod: "Yazılım - Bilişim - Bilgi Yönetim",                emoji: "🖥️", aciklama: "Yazılım, bilişim, BT hizmetleri",    eski: "yazilim" },
];

// eski kısa anahtar -> kanonik kod (profil geri-uyum + migration)
window.KATEGORI_ESKI_MAP = window.KATEGORILER.reduce((m, k) => {
  if (k.eski) m[k.eski] = k.kod;
  return m;
}, {});
