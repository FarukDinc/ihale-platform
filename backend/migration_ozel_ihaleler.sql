-- Özel İhaleler / e-Satınalma (Promena benzeri) — Faz 1: kapalı-zarf RFQ.
-- Alıcı firma satınalma ihalesi (talep) açar; eşleştirme motoru uygun tedarikçileri önerir;
-- (Faz 2) tedarikçiler gizli teklif verir, alıcı değerlendirir.
-- Türkiye kamu (ilanlar) analizini KİRLETMEZ — ayrı tablolar.

CREATE TABLE IF NOT EXISTS public.satinalma_talepleri (
  id                uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  olusturan_user_id uuid NOT NULL,
  olusturan_firma   text,                                 -- alıcı firma adı
  baslik            text NOT NULL,
  aciklama          text,
  kategori          text,                                 -- eşleştirme motoruyla aynı kategori seti
  il                text,
  miktar            text,                                 -- "500 adet", "1200 m²" gibi serbest
  tahmini_bedel     numeric,
  para_birimi       text DEFAULT 'TRY',
  son_teklif_tarihi timestamptz,
  durum             text NOT NULL DEFAULT 'acik',         -- 'acik' | 'kapali' | 'iptal'
  olusturulma       timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_satinalma_durum ON public.satinalma_talepleri (durum, olusturulma DESC);
CREATE INDEX IF NOT EXISTS idx_satinalma_user  ON public.satinalma_talepleri (olusturan_user_id);

CREATE TABLE IF NOT EXISTS public.tedarikci_teklifleri (
  id                   uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  talep_id             uuid NOT NULL REFERENCES public.satinalma_talepleri(id) ON DELETE CASCADE,
  teklif_veren_user_id uuid NOT NULL,
  teklif_veren_firma   text,
  teklif_bedeli        numeric,
  aciklama             text,
  durum                text NOT NULL DEFAULT 'beklemede',  -- 'beklemede' | 'kabul' | 'red'
  olusturulma          timestamptz NOT NULL DEFAULT now(),
  UNIQUE (talep_id, teklif_veren_user_id)                  -- bir tedarikçi bir talebe tek teklif
);

CREATE INDEX IF NOT EXISTS idx_teklif_talep ON public.tedarikci_teklifleri (talep_id);

-- ── RLS ──────────────────────────────────────────────────────────────
ALTER TABLE public.satinalma_talepleri ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.tedarikci_teklifleri ENABLE ROW LEVEL SECURITY;

-- Talepler: giriş yapmış herkes AÇIK talepleri görür (tedarikçiler fırsatı görsün); sahibi kendini yönetir.
DROP POLICY IF EXISTS "talep_authenticated_okur" ON public.satinalma_talepleri;
CREATE POLICY "talep_authenticated_okur" ON public.satinalma_talepleri
  FOR SELECT TO authenticated USING (true);
DROP POLICY IF EXISTS "talep_sahibi_ekler" ON public.satinalma_talepleri;
CREATE POLICY "talep_sahibi_ekler" ON public.satinalma_talepleri
  FOR INSERT TO authenticated WITH CHECK (auth.uid() = olusturan_user_id);
DROP POLICY IF EXISTS "talep_sahibi_gunceller" ON public.satinalma_talepleri;
CREATE POLICY "talep_sahibi_gunceller" ON public.satinalma_talepleri
  FOR UPDATE TO authenticated USING (auth.uid() = olusturan_user_id);
DROP POLICY IF EXISTS "talep_sahibi_siler" ON public.satinalma_talepleri;
CREATE POLICY "talep_sahibi_siler" ON public.satinalma_talepleri
  FOR DELETE TO authenticated USING (auth.uid() = olusturan_user_id);

-- Teklifler: kapalı-zarf → tedarikçi SADECE kendi teklifini görür; talep sahibi tüm teklifleri görür.
DROP POLICY IF EXISTS "teklif_gizli_okur" ON public.tedarikci_teklifleri;
CREATE POLICY "teklif_gizli_okur" ON public.tedarikci_teklifleri
  FOR SELECT TO authenticated USING (
    auth.uid() = teklif_veren_user_id
    OR auth.uid() = (SELECT olusturan_user_id FROM public.satinalma_talepleri t WHERE t.id = talep_id)
  );
DROP POLICY IF EXISTS "teklif_tedarikci_ekler" ON public.tedarikci_teklifleri;
CREATE POLICY "teklif_tedarikci_ekler" ON public.tedarikci_teklifleri
  FOR INSERT TO authenticated WITH CHECK (auth.uid() = teklif_veren_user_id);

GRANT SELECT, INSERT, UPDATE, DELETE ON public.satinalma_talepleri  TO authenticated;
GRANT SELECT, INSERT                 ON public.tedarikci_teklifleri  TO authenticated;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.satinalma_talepleri  TO service_role;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.tedarikci_teklifleri TO service_role;

NOTIFY pgrst, 'reload schema';
