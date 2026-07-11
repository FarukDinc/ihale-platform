/**
 * İhaleGlobal — Profil Uyum Skoru (paylaşılan modül)
 *
 * Kullanım:
 *   <script src="js/uyum.js"></script>
 *   const profil = await Uyum.profilCek(sb);
 *   const skor = Uyum.hesapla(ilan, profil);   // 0-100
 *
 * Not: ilan.yaklasik_maliyet_min/max kullanılır (yoksa tahmini_bedel'e düşer).
 */
window.Uyum = (() => {

  // Kategori → ihale başlığı anahtar kelimeleri
  const KATEGORI_ANAHTAR_KELIMELER = {
    insaat:       ["inşaat","yapım","bina","altyapı","yıkım","yol","köprü","üstyapı"],
    saglik:       ["sağlık","ilaç","medikal","kozmetik","eczane","klinik","hastane"],
    tibbi_cihaz:  ["tıbbi","laboratuvar","hastane ekipman","sterilizasyon","cihaz"],
    elektronik:   ["elektronik","bilgisayar","yazıcı","iletişim","ölçü","donanım"],
    yazilim:      ["yazılım","bilişim","bilgi yönetim","sistem","uygulama","platform"],
    enerji:       ["enerji","elektrik","aydınlatma","sinyalizasyon","trafo","jeneratör"],
    kanalizasyon: ["kanalizasyon","boru","su","doğalgaz","sıhhi","tesisat"],
    temizlik:     ["temizlik","ilaçlama","geri dönüşüm","dezenfektan","çevre"],
    guvenlik:     ["güvenlik","koruma","bekçilik","özel güvenlik"],
    hirdavat:     ["hırdavat","nalburiye","metal","plastik","demir"],
    makine:       ["makine","motor","konveyör","endüstriyel","sanayi"],
    tasit:        ["taşıt","araç","iş makinesi","yedek parça","otomobil","kamyon"],
    nakliye:      ["nakliye","taşımacılık","lojistik","kargo","servis"],
    gida:         ["gıda","tarım","yiyecek","içecek","un","şeker","tahıl"],
    hazir_yemek:  ["hazır yemek","lokanta","yemek","catering","toplu yemek"],
    klima:        ["klima","soğutma","ısıtma","havalandırma","iklimlendirme"],
    yangin:       ["yangın","söndürme","algılama","ihbar"],
    asansor:      ["asansör","yapı otomasyonu","mekanik güvenlik"],
    kimyasal:     ["kimyasal","dezenfektan","gübre","boya","solvent"],
    tekstil:      ["tekstil","giyim","spor ekipman","kıyafet","üniform"],
    mobilya:      ["mobilya","beyaz eşya","mutfak","züccaciye","büro"],
    matbaa:       ["matbaa","kırtasiye","toner","kartuş","ambalaj","baskı"],
    egitim:       ["eğitim","araştırma","anket","tercümanlık","kurs"],
    is_sagligi:   ["iş sağlığı","iş güvenliği","kask","koruyucu"],
    uydu:         ["uydu","kamera","scada","haberleşme","izleme"],
    muhendislik:  ["mühendislik","mimarlık","danışmanlık","etüt","proje"],
    isletmecilik: ["işletmecilik","işçilik","sosyal hizmet","personel"],
    tarim:        ["ormancılık","bahçıvanlık","bitki","peyzaj","kozlak"],
    sigortacilik: ["sigortacılık","mali","hukuki","muhasebe"],
    gayrimenkul:  ["gayrimenkul","arsa","işyeri","kira","satış"],
    akaryakit:    ["akaryakıt","gazyakıt","madeni yağ","yakıt","benzin","mazot"],
    diger:        []
  };

  async function profilCek(sb) {
    try {
      const { data: { user } } = await sb.auth.getUser();
      if (!user) return null;
      const { data } = await sb.from('profil')
        .select('sektorler,kategoriler,tercih_iller,tercih_turler,min_bedel,max_bedel')
        .eq('user_id', user.id).single();
      return data || null;
    } catch (e) {
      return null;
    }
  }

  function hesapla(ilan, profil) {
    if (!profil) return Math.floor(Math.random() * 20 + 55);
    let puan = 0;

    // Kategori eşleşmesi (40 puan)
    const kategoriler = profil.kategoriler || profil.sektorler || [];
    if (kategoriler.length > 0 && ilan.baslik) {
      const baslikKucuk = ilan.baslik.toLowerCase();
      let maxEslesen = 0;
      for (const kat of kategoriler) {
        const kelimeler = KATEGORI_ANAHTAR_KELIMELER[kat] || [];
        const eslesen = kelimeler.filter(k => baslikKucuk.includes(k)).length;
        if (eslesen > maxEslesen) maxEslesen = eslesen;
      }
      if (maxEslesen >= 2) puan += 40;
      else if (maxEslesen === 1) puan += 25;
      else puan += 5;
    } else if (kategoriler.length === 0) {
      puan += 20;
    }

    // İl eşleşmesi (25 puan)
    const iller = profil.tercih_iller || [];
    if (iller.length === 0 || iller.includes("Tüm Türkiye")) puan += 15;
    else if (ilan.il && iller.includes(ilan.il)) puan += 25;

    // İhale türü (20 puan)
    const turler = profil.tercih_turler || [];
    if (turler.length === 0) puan += 10;
    else if (ilan.tur && turler.includes(ilan.tur)) puan += 20;

    // Yaklaşık maliyet aralığı (15 puan)
    const min = profil.min_bedel || 0;
    const max = profil.max_bedel || 0;
    const bedel = ilan.yaklasik_maliyet_min || ilan.tahmini_bedel || 0;
    if (max === 0 || (bedel >= min && bedel <= max)) puan += 15;
    else if (bedel >= min * 0.5 && bedel <= max * 1.5) puan += 7;

    // Anahtar kelime bonusu (+10) — profil.html'de girilen özel kelimeler
    if (ilan.baslik) {
      const anahtarlar = (localStorage.getItem('ihale_anahtar_kelimeler') || '')
        .split(',').map(k => k.trim().toLowerCase()).filter(Boolean);
      if (anahtarlar.length > 0) {
        const bl = ilan.baslik.toLowerCase();
        if (anahtarlar.some(k => bl.includes(k))) puan += 10;
      }
    }

    return Math.min(puan, 100);
  }

  return { KATEGORI_ANAHTAR_KELIMELER, profilCek, hesapla };
})();
