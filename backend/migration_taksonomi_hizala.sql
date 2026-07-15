-- Taksonomi hizalama: profil.sektorler (eski kısa anahtar) ile ilanlar.kategori (kanonik ad) uyumsuzdu.
-- 1) ilanlar'daki ESKİ etiket "İnşaat & Yapım" (eski sınıflandırıcıdan) kanonikle birleştir.
-- 2) profil.sektorler / profil.kategoriler kısa anahtarlarını kanonik adlara çevir.
-- Kanonik adlar js/kategoriler.js ile BİREBİR aynı olmalı.

-- 1) Eski inşaat etiketi normalize (uluslararasi/satinalma'da bu etiket yok, sadece ilanlar).
UPDATE public.ilanlar
   SET kategori = 'İnşaat - Altyapı - Üstyapı - Yapım'
 WHERE kategori = 'İnşaat & Yapım';

-- 2) profil kısa anahtar -> kanonik ad eşlemesi
WITH kod_map(eski, kanonik) AS (VALUES
  ('akaryakit',   'Akaryakıt - Gazyakıt - Madeni Yağ'),
  ('asansor',     'Asansör - Yapı Otomasyon - Mekanik Güvenlik'),
  ('egitim',      'Eğitim - Araştırma - Anket - Tercümanlık'),
  ('elektronik',  'Elektronik - Bilgisayar - İletişim - Ölçü Aletleri'),
  ('makine',      'Endüstriyel Makine - Motor - Konveyör'),
  ('enerji',      'Enerji - Aydınlatma - Sinyalizasyon - Elektrik Tesisatı'),
  ('gayrimenkul', 'Gayrimenkul - Arsa Satışı - Kantin'),
  ('gida',        'Gıda - Tarım Ürünleri - Yiyecek - İçecek'),
  ('hazir_yemek', 'Hazır Yemek - Lokantacılık'),
  ('hirdavat',    'Hırdavat - Nalburiye - Metal ve Plastik'),
  ('insaat',      'İnşaat - Altyapı - Üstyapı - Yapım'),
  ('is_sagligi',  'İş Sağlığı - İş Güvenliği ve Ekipmanları'),
  ('isletmecilik','İşletmecilik - İşçilik - Sosyal Hizmetler'),
  ('kanalizasyon','Kanalizasyon - Boru - Su - Doğalgaz - Sıhhi Tesisat'),
  ('kimyasal',    'Kimyasal Maddeler - Dezenfektan - Gübre'),
  ('klima',       'Klima - Soğutma - Isıtma - Havalandırma'),
  ('matbaa',      'Matbaa - Kırtasiye - Toner - Kartuş - Ambalaj'),
  ('mobilya',     'Mobilya - Beyaz Eşya - Mutfak - Züccaciye'),
  ('muhendislik', 'Mühendislik - Mimarlık - Danışmanlık'),
  ('nakliye',     'Nakliye - Servis - Taşımacılık'),
  ('tarim',       'Ormancılık - Bahçıvanlık - Peyzaj'),
  ('guvenlik',    'Özel Güvenlik - Koruma - Bekçilik'),
  ('saglik',      'Sağlık - Medikal - İlaç - Kozmetik'),
  ('sigortacilik','Sigortacılık - Mali ve Hukuki Hizmetler'),
  ('tekstil',     'Tekstil - Giyim - Spor Ekipmanları'),
  ('temizlik',    'Temizlik - İlaçlama - Geri Dönüşüm'),
  ('tasit',       'Taşıt - İş Makinesi - Yedek Parça'),
  ('tibbi_cihaz', 'Tıbbi Cihaz - Laboratuvar - Hastane Ekipmanları'),
  ('uydu',        'Uydu Takip - Kamera - Scada - Haberleşme'),
  ('yangin',      'Yangın Algılama - Söndürme'),
  ('yazilim',     'Yazılım - Bilişim - Bilgi Yönetim')
),
-- her profil için: eski anahtarları kanonike çevir, 'diger' gibi eşleşmeyeni AT, tekilleştir
yeni AS (
  SELECT p.user_id,
         array_agg(DISTINCT m.kanonik) FILTER (WHERE m.kanonik IS NOT NULL) AS arr
  FROM public.profil p,
       LATERAL unnest(p.sektorler) e
  LEFT JOIN kod_map m ON m.eski = e OR m.kanonik = e   -- zaten kanonikse de koru
  WHERE p.sektorler IS NOT NULL AND array_length(p.sektorler, 1) > 0
  GROUP BY p.user_id
)
UPDATE public.profil p
   SET sektorler   = COALESCE(y.arr, '{}'),
       kategoriler = COALESCE(y.arr, '{}')
  FROM yeni y
 WHERE p.user_id = y.user_id;
