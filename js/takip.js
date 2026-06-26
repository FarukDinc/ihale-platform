/**
 * İhalePlatform — Takip Listesi (localStorage tabanlı)
 *
 * DB tablosu gerektirmez; tarayıcı bazında kalıcıdır.
 * İleride kullanıcı bazlı 'takip' tablosu eklenince buradan migrate edilebilir.
 *
 * Kullanım:
 *   Takip.toggle(id)  // ekler/çıkarır, yeni durumu döndürür (true=takipte)
 *   Takip.var(id)     // takipte mi?
 *   Takip.liste()     // tüm takip edilen id'ler
 *   Takip.sayi()      // adet
 */
window.Takip = (() => {
  const ANAHTAR = 'ihale_takip';

  function liste() {
    try {
      return JSON.parse(localStorage.getItem(ANAHTAR)) || [];
    } catch (e) {
      return [];
    }
  }

  function kaydet(arr) {
    localStorage.setItem(ANAHTAR, JSON.stringify(arr));
  }

  function varmi(id) {
    return liste().includes(String(id));
  }

  function toggle(id) {
    id = String(id);
    const arr = liste();
    const idx = arr.indexOf(id);
    if (idx >= 0) {
      arr.splice(idx, 1);
      kaydet(arr);
      return false;
    }
    arr.push(id);
    kaydet(arr);
    return true;
  }

  return { liste, var: varmi, toggle, sayi: () => liste().length };
})();
