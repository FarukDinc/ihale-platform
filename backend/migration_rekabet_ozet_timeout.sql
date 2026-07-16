-- rekabet_ozet(): filtresiz çağrı ~351K ilanlar üzerinde ~20 alt-agregasyon yapıyor ve
-- ~3s sürüyor — PostgREST'in varsayılan statement_timeout'una (≈3s) çok yakın olduğu için
-- ARALIKLI "canceling statement due to statement timeout" veriyordu → rekabet-analizi sayfası
-- bazen hiç render olmuyordu. Fonksiyon-yerel timeout override'ı ile güvenilir tamamlanır
-- (mantık/çıktı değişmez; yalnız bu fonksiyon çağrısı süresince timeout yükselir).
ALTER FUNCTION public.rekabet_ozet(text, text, text) SET statement_timeout = '20s';
