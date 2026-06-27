/**
 * İhalePlatform — Ödeme Başlatma Edge Function
 *
 * Çağrı: supabase.functions.invoke("odeme-baslat", { body: { plan_kodu, ... } })
 *
 * Akış:
 *   1. Supabase JWT'yi doğrula → user al
 *   2. iyzico sandbox/prod'a ödeme isteği gönder
 *   3. Başarılıysa profil.plan = 'pro' güncelle
 *
 * Gerekli secrets (Supabase Dashboard → Edge Functions → Secrets):
 *   IYZICO_API_KEY, IYZICO_SECRET_KEY
 *   IYZICO_SANDBOX=true  (false → prod)
 */

import { serve } from "https://deno.land/std@0.177.0/http/server.ts";
import { createClient } from "https://esm.sh/@supabase/supabase-js@2";

const IYZICO_API_KEY = Deno.env.get("IYZICO_API_KEY") ?? "";
const IYZICO_SECRET  = Deno.env.get("IYZICO_SECRET_KEY") ?? "";
const IYZICO_BASE    = Deno.env.get("IYZICO_SANDBOX") === "false"
  ? "https://api.iyzipay.com"
  : "https://sandbox-api.iyzipay.com";

const CORS = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Headers": "authorization, x-client-info, apikey, content-type",
};

// iyzico HMAC-SHA256 imzası
async function hmac256(secret: string, data: string): Promise<string> {
  const key = await crypto.subtle.importKey(
    "raw", new TextEncoder().encode(secret),
    { name: "HMAC", hash: "SHA-256" }, false, ["sign"]
  );
  const buf = await crypto.subtle.sign("HMAC", key, new TextEncoder().encode(data));
  return btoa(String.fromCharCode(...new Uint8Array(buf)));
}

// iyzico PKI string formatı: [key=val,key=[...],...]
function pkiStr(obj: unknown): string {
  if (Array.isArray(obj))
    return `[${obj.map(pkiStr).join(", ")}]`;
  if (obj !== null && typeof obj === "object") {
    const parts = Object.entries(obj as Record<string, unknown>)
      .filter(([, v]) => v !== undefined && v !== null && v !== "")
      .map(([k, v]) => `${k}=${pkiStr(v)}`);
    return `[${parts.join(",")}]`;
  }
  return String(obj);
}

const planFiyat: Record<string, string> = {
  pro:       "1490.00",
  standart:  "1490.00",
  kurumsal:  "3990.00",
};

serve(async (req) => {
  if (req.method === "OPTIONS") return new Response("ok", { headers: CORS });

  const json = (body: unknown, status = 200) =>
    new Response(JSON.stringify(body), {
      status,
      headers: { ...CORS, "Content-Type": "application/json" },
    });

  try {
    // Supabase istemcisi (service role — profil güncelleme için)
    const sb = createClient(
      Deno.env.get("SUPABASE_URL")!,
      Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!
    );

    // JWT doğrula
    const jwt = (req.headers.get("authorization") ?? "").replace("Bearer ", "");
    const { data: { user }, error: authErr } = await sb.auth.getUser(jwt);
    if (authErr || !user) return json({ basari: false, hata: "Giriş gerekli" }, 401);

    const {
      plan_kodu = "pro",
      kart_sahibi_ad,
      kart_sahibi_soyad,
      kart_no,
      son_kullanma_ay,
      son_kullanma_yil,
      cvc,
      taksit = 1,
    } = await req.json();

    if (!IYZICO_API_KEY || !IYZICO_SECRET)
      return json({ basari: false, hata: "iyzico anahtarları tanımlı değil" }, 500);

    const fiyat = planFiyat[plan_kodu] ?? "1490.00";
    const convId   = `ihale-${user.id.slice(0, 8)}-${Date.now()}`;
    const randomKey = crypto.randomUUID().replace(/-/g, "");

    // Profil bilgisi (opsiyonel, fallback var)
    const { data: profil } = await sb.from("profil")
      .select("firma_adi, telefon, adres, il")
      .eq("user_id", user.id).single();

    const yil = String(son_kullanma_yil).length === 2
      ? `20${son_kullanma_yil}`
      : String(son_kullanma_yil);

    const payload = {
      locale:         "tr",
      conversationId: convId,
      price:          fiyat,
      paidPrice:      fiyat,
      currency:       "TRY",
      installment:    String(taksit),
      basketId:       `plan-${plan_kodu}-${user.id.slice(0, 8)}`,
      paymentChannel: "WEB",
      paymentGroup:   "SUBSCRIPTION",
      paymentCard: {
        cardHolderName: `${kart_sahibi_ad} ${kart_sahibi_soyad}`,
        cardNumber:     kart_no,
        expireMonth:    String(son_kullanma_ay).padStart(2, "0"),
        expireYear:     yil,
        cvc:            String(cvc),
        registerCard:   "0",
      },
      buyer: {
        id:                  user.id.slice(0, 8),
        name:                kart_sahibi_ad,
        surname:             kart_sahibi_soyad,
        gsmNumber:           profil?.telefon ?? "+905000000000",
        email:               user.email,
        identityNumber:      "74300864791", // Sandbox test TC kimlik
        registrationAddress: profil?.adres ?? "Test Adres No:1",
        ip:                  "85.34.78.112",
        city:                profil?.il ?? "Istanbul",
        country:             "Turkey",
      },
      shippingAddress: {
        contactName: `${kart_sahibi_ad} ${kart_sahibi_soyad}`,
        city:        profil?.il ?? "Istanbul",
        country:     "Turkey",
        address:     profil?.adres ?? "Test Adres No:1",
      },
      billingAddress: {
        contactName: `${kart_sahibi_ad} ${kart_sahibi_soyad}`,
        city:        profil?.il ?? "Istanbul",
        country:     "Turkey",
        address:     profil?.adres ?? "Test Adres No:1",
      },
      basketItems: [{
        id:        `plan-${plan_kodu}`,
        name:      `İhalePlatform Pro — Aylık Abonelik`,
        category1: "SaaS Yazılım",
        itemType:  "VIRTUAL",
        price:     fiyat,
      }],
    };

    const pki       = pkiStr(payload);
    const signature = await hmac256(IYZICO_SECRET, IYZICO_API_KEY + randomKey + pki);
    const authHeader = `IYZWS apiKey:${IYZICO_API_KEY}, randomKey:${randomKey}, signature:${signature}`;

    const iyzicoRes = await fetch(`${IYZICO_BASE}/payment/auth`, {
      method: "POST",
      headers: {
        "Content-Type":         "application/json",
        "Authorization":        authHeader,
        "x-iyzi-rnd":           randomKey,
        "x-iyzi-client-version":"iyzipay-node-2.0.50",
      },
      body: JSON.stringify(payload),
    });

    const veri = await iyzicoRes.json();

    if (veri.status === "success") {
      const planAdi = plan_kodu === "kurumsal" ? "kurumsal" : "pro";
      const simdi   = new Date();
      const bitis   = new Date(simdi.getTime() + 30 * 24 * 3600 * 1000);
      await sb.from("profil").upsert(
        {
          user_id:           user.id,
          plan:              planAdi,
          plan_baslangic:    simdi.toISOString(),
          plan_bitis:        bitis.toISOString(),
          iyzico_payment_id: veri.paymentId ?? null,
        },
        { onConflict: "user_id" }
      );
      return json({
        basari:    true,
        mesaj:     "Ödeme başarılı! Pro planınız aktifleştirildi.",
        paymentId: veri.paymentId,
        convId,
      });
    }

    return json({
      basari: false,
      hata:   veri.errorMessage ?? "Ödeme işlemi başarısız",
      kod:    veri.errorCode,
    });

  } catch (err) {
    console.error("odeme-baslat hata:", err);
    return json({ basari: false, hata: String(err) }, 500);
  }
});
