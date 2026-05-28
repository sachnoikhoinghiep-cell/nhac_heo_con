/**
 * Supabase Edge Function: sepay-webhook
 *
 * Nhận webhook từ SePay khi phát hiện giao dịch chuyển khoản.
 * Tự động kích hoạt gói dịch vụ khi payment_code khớp.
 *
 * Deploy:
 *   supabase functions deploy sepay-webhook --no-verify-jwt
 *
 * Env vars cần set trong Supabase Dashboard → Settings → Edge Functions:
 *   SEPAY_WEBHOOK_SECRET  — token bí mật, cấu hình trong SePay dashboard
 *   SUPABASE_URL          — tự inject bởi Supabase
 *   SUPABASE_SERVICE_ROLE_KEY — tự inject bởi Supabase
 */

import { createClient } from "https://esm.sh/@supabase/supabase-js@2.39.0";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------
interface SepayPayload {
  id: number;
  gateway: string;
  transactionDate: string;
  accountNumber: string;
  subAccount?: string;
  code?: string;
  content: string;
  transferType: string;           // "in" = nhận tiền, "out" = gửi tiền
  transferAmount: number;
  accumulated: number;
  referenceCode?: string;
  description?: string;
}

const PLAN_DAYS: Record<string, number> = {
  "Ngày": 1, "Tuần": 7, "Tháng": 30, "Năm": 365,
};

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------
function extractPaymentCode(content: string): string | null {
  // Tìm SONIC + 8 ký tự chữ hoa/số trong nội dung chuyển khoản
  const match = content.toUpperCase().match(/SONIC[A-Z0-9]{8}/);
  return match ? match[0] : null;
}

function addDays(date: Date, days: number): Date {
  return new Date(date.getTime() + days * 86_400_000);
}

// ---------------------------------------------------------------------------
// Main handler
// ---------------------------------------------------------------------------
Deno.serve(async (req: Request) => {
  const corsHeaders = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "authorization, content-type",
  };

  if (req.method === "OPTIONS") {
    return new Response("ok", { headers: corsHeaders });
  }

  if (req.method !== "POST") {
    return new Response("Method Not Allowed", { status: 405 });
  }

  // ── Xác thực webhook secret ─────────────────────────────────────────────
  // SePay gửi API Key dạng: Authorization: <key>  (không có "Bearer")
  // Hỗ trợ cả hai format để tương thích
  const secret = Deno.env.get("SEPAY_WEBHOOK_SECRET") ?? "";
  if (secret) {
    const auth = req.headers.get("Authorization") ?? "";
    if (auth !== secret && auth !== `Bearer ${secret}`) {
      console.warn("Unauthorized webhook attempt, auth:", auth.slice(0, 20));
      return new Response("Unauthorized", { status: 401 });
    }
  }

  // ── Parse payload ────────────────────────────────────────────────────────
  let payload: SepayPayload;
  try {
    payload = await req.json();
  } catch {
    return new Response("Invalid JSON", { status: 400 });
  }

  console.log("SePay webhook:", JSON.stringify(payload));

  // Chỉ xử lý giao dịch nhận tiền
  if (payload.transferType !== "in") {
    return new Response(
      JSON.stringify({ success: true, message: "skipped: outgoing" }),
      { headers: { ...corsHeaders, "Content-Type": "application/json" } }
    );
  }

  // ── Tìm payment code trong nội dung CK ──────────────────────────────────
  const code = extractPaymentCode(payload.content ?? "");
  if (!code) {
    console.log("No payment code in:", payload.content);
    return new Response(
      JSON.stringify({ success: true, message: "no payment code" }),
      { headers: { ...corsHeaders, "Content-Type": "application/json" } }
    );
  }

  const supabase = createClient(
    Deno.env.get("SUPABASE_URL")!,
    Deno.env.get("SUPABASE_SERVICE_ROLE_KEY")!
  );

  // ── Tìm payment_request khớp ────────────────────────────────────────────
  const { data: payment, error: findErr } = await supabase
    .from("payment_requests")
    .select("*, subscription_plans(name, duration_days)")
    .eq("payment_code", code)
    .eq("status", "pending")
    .single();

  if (findErr || !payment) {
    console.log("Payment not found:", code, findErr?.message);
    return new Response(
      JSON.stringify({ success: true, message: "payment not found" }),
      { headers: { ...corsHeaders, "Content-Type": "application/json" } }
    );
  }

  // ── Kiểm tra số tiền ────────────────────────────────────────────────────
  if (payload.transferAmount < payment.amount_vnd) {
    console.warn(`Under-payment: expected ${payment.amount_vnd}, got ${payload.transferAmount}`);
    await supabase.from("payment_requests").update({
      status: "failed",
      sepay_transaction_id: String(payload.id),
    }).eq("id", payment.id);
    return new Response(
      JSON.stringify({ success: false, message: "under-payment" }),
      { headers: { ...corsHeaders, "Content-Type": "application/json" } }
    );
  }

  // ── Kiểm tra hết hạn ────────────────────────────────────────────────────
  const now = new Date();
  if (now > new Date(payment.expires_at)) {
    console.log("Payment expired:", code);
    await supabase.from("payment_requests").update({ status: "expired" }).eq("id", payment.id);
    return new Response(
      JSON.stringify({ success: false, message: "payment expired" }),
      { headers: { ...corsHeaders, "Content-Type": "application/json" } }
    );
  }

  // ── Kích hoạt subscription ───────────────────────────────────────────────
  const planName = payment.subscription_plans.name as string;
  const days = PLAN_DAYS[planName] ?? 30;
  const expiresAt = addDays(now, days).toISOString();

  // Hủy gói active cũ
  await supabase.from("user_subscriptions")
    .update({ status: "cancelled" })
    .eq("user_id", payment.user_id)
    .eq("status", "active");

  const { error: subErr } = await supabase.from("user_subscriptions").insert({
    user_id:           payment.user_id,
    plan_id:           payment.plan_id,
    status:            "active",
    started_at:        now.toISOString(),
    expires_at:        expiresAt,
    paid_at:           now.toISOString(),
    payment_provider:  "sepay",
    payment_reference: code,
  });

  if (subErr) {
    console.error("Subscription insert error:", subErr.message);
    return new Response(
      JSON.stringify({ success: false, error: subErr.message }),
      { status: 500, headers: { ...corsHeaders, "Content-Type": "application/json" } }
    );
  }

  // ── Đánh dấu payment hoàn thành ─────────────────────────────────────────
  await supabase.from("payment_requests").update({
    status:               "completed",
    sepay_transaction_id: String(payload.id),
    sepay_reference:      payload.referenceCode ?? "",
    completed_at:         now.toISOString(),
  }).eq("id", payment.id);

  console.log(`✅ Plan '${planName}' activated for user ${payment.user_id}`);

  return new Response(
    JSON.stringify({
      success: true,
      message: `${planName} activated for ${payment.user_id}`,
    }),
    { headers: { ...corsHeaders, "Content-Type": "application/json" } }
  );
});
