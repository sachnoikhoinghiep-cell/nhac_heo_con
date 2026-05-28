"""
sepay.py — SePay payment integration helper.

Yêu cầu thêm vào secrets.toml:
    SEPAY_BANK_BIN       = "970422"            # BIN ngân hàng (MB: 970422, VCB: 970436...)
    SEPAY_ACCOUNT_NO     = "0123456789"        # Số tài khoản nhận tiền
    SEPAY_ACCOUNT_NAME   = "NGUYEN VAN A"      # Tên chủ tài khoản (UPPERCASE)
    SEPAY_WEBHOOK_SECRET = "your-secret-token" # Token xác thực webhook
"""

import os
import random
import string
from datetime import datetime, timezone, timedelta
from urllib.parse import quote

from supabase_config import get_supabase

# ---------------------------------------------------------------------------
# Bảng giá VNĐ — đồng bộ với subscription_plans.price_vnd
# ---------------------------------------------------------------------------
PLANS_VND = {
    "Ngày":  {
        "price_vnd": 19_000,
        "desc":      "Thử nghiệm hệ thống, xem luồng tự động hóa",
        "badge":     "Thử nghiệm",
        "color":     "#3b82f6",
    },
    "Tuần":  {
        "price_vnd": 69_000,
        "desc":      "Đẩy nhanh tiến độ 1–2 kênh YouTube trong tuần",
        "badge":     "Dự án ngắn",
        "color":     "#8b5cf6",
    },
    "Tháng": {
        "price_vnd": 199_000,
        "desc":      "Công cụ làm việc chính cho content creator",
        "badge":     "Phổ biến nhất ⭐",
        "color":     "#f59e0b",
    },
    "Năm":   {
        "price_vnd": 1_490_000,
        "desc":      "Ưu tiên cập nhật dòng nhạc & kịch bản video 2 mới",
        "badge":     "Chuyên gia",
        "color":     "#10b981",
    },
}


# ---------------------------------------------------------------------------
# Secrets helpers
# ---------------------------------------------------------------------------
def _secret(key: str, default: str = "") -> str:
    try:
        import streamlit as st
        return st.secrets.get(key, "") or os.environ.get(key, default)
    except Exception:
        return os.environ.get(key, default)


def bank_config() -> dict:
    return {
        "bank_bin":      _secret("SEPAY_BANK_BIN"),
        "account_no":    _secret("SEPAY_ACCOUNT_NO"),
        "account_name":  _secret("SEPAY_ACCOUNT_NAME"),
    }


# ---------------------------------------------------------------------------
# Payment code generation
# ---------------------------------------------------------------------------
def generate_payment_code() -> str:
    """Tạo mã chuyển khoản duy nhất: SONIC + 8 ký tự chữ hoa/số."""
    suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=8))
    return f"SONIC{suffix}"


# ---------------------------------------------------------------------------
# VietQR URL builder
# ---------------------------------------------------------------------------
def build_qr_url(amount_vnd: int, payment_code: str) -> str:
    """
    Tạo URL ảnh QR chuẩn VietQR để user quét.
    Format: https://img.vietqr.io/image/{bin}-{account}-compact2.jpg
    """
    cfg = bank_config()
    bin_ = cfg.get("bank_bin", "")
    acc  = cfg.get("account_no", "")
    name = cfg.get("account_name", "")
    if not bin_ or not acc:
        return ""
    return (
        f"https://img.vietqr.io/image/{bin_}-{acc}-compact2.jpg"
        f"?amount={amount_vnd}"
        f"&addInfo={quote(payment_code)}"
        f"&accountName={quote(name)}"
    )


# ---------------------------------------------------------------------------
# Supabase CRUD
# ---------------------------------------------------------------------------
def create_payment_request(uid: str, plan_name: str) -> dict:
    """
    Tạo payment request mới trong Supabase.
    Trả về dict: payment_code, amount_vnd, qr_url, expires_at, bank info.
    """
    db = get_supabase()
    plan_info = PLANS_VND.get(plan_name)
    if not plan_info:
        raise ValueError(f"Gói không hợp lệ: {plan_name}")

    # Lấy plan_id từ DB (fallback về giá local nếu cột price_vnd chưa tồn tại)
    try:
        res = (
            db.table("subscription_plans")
            .select("id, price_vnd")
            .eq("name", plan_name)
            .single()
            .execute()
        )
    except Exception:
        res = (
            db.table("subscription_plans")
            .select("id")
            .eq("name", plan_name)
            .single()
            .execute()
        )
    if not res.data:
        raise ValueError(f"Không tìm thấy gói '{plan_name}' trong DB")
    plan_id    = res.data["id"]
    amount_vnd = res.data.get("price_vnd") or plan_info["price_vnd"]

    # Hủy pending requests cũ của user này
    db.table("payment_requests").update({"status": "expired"}).eq(
        "user_id", uid
    ).eq("status", "pending").execute()

    # Tạo mã mới
    code       = generate_payment_code()
    expires_at = (datetime.now(timezone.utc) + timedelta(minutes=30)).isoformat()

    db.table("payment_requests").insert({
        "user_id":      uid,
        "plan_id":      plan_id,
        "payment_code": code,
        "amount_vnd":   amount_vnd,
        "status":       "pending",
        "expires_at":   expires_at,
    }).execute()

    cfg = bank_config()
    return {
        "payment_code": code,
        "amount_vnd":   amount_vnd,
        "qr_url":       build_qr_url(amount_vnd, code),
        "expires_at":   expires_at,
        "bank_bin":     cfg.get("bank_bin", ""),
        "account_no":   cfg.get("account_no", ""),
        "account_name": cfg.get("account_name", ""),
    }


def check_payment_status(payment_code: str) -> str:
    """
    Kiểm tra trạng thái: 'pending' | 'completed' | 'expired' | 'failed' | 'not_found'
    Tự động đánh dấu expired nếu quá thời hạn.
    """
    db  = get_supabase()
    res = (
        db.table("payment_requests")
        .select("status, expires_at")
        .eq("payment_code", payment_code)
        .maybe_single()
        .execute()
    )
    if not res.data:
        return "not_found"

    status = res.data["status"]

    if status == "pending":
        exp_str = res.data.get("expires_at")
        if exp_str:
            try:
                exp = datetime.fromisoformat(exp_str.replace("Z", "+00:00"))
                if exp < datetime.now(timezone.utc):
                    db.table("payment_requests").update({"status": "expired"}).eq(
                        "payment_code", payment_code
                    ).execute()
                    return "expired"
            except Exception:
                pass
    return status


def fmt_vnd(amount: int) -> str:
    """Format số tiền VNĐ có dấu chấm phân cách nghìn."""
    return f"{amount:,}".replace(",", ".")
