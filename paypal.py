import requests

PAYPAL_API = "https://api-m.paypal.com"


def _get_access_token(client_id: str, secret: str) -> str:
    resp = requests.post(
        f"{PAYPAL_API}/v1/oauth2/token",
        auth=(client_id, secret),
        data={"grant_type": "client_credentials"},
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def create_subscription(client_id: str, secret: str, plan_id: str,
                        return_url: str, cancel_url: str) -> tuple[str, str]:
    """Tạo PayPal subscription. Trả về (subscription_id, approval_url)."""
    token = _get_access_token(client_id, secret)
    resp = requests.post(
        f"{PAYPAL_API}/v1/billing/subscriptions",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json={
            "plan_id": plan_id,
            "application_context": {
                "return_url":  return_url,
                "cancel_url":  cancel_url,
                "brand_name":  "Sonicflowai",
                "user_action": "SUBSCRIBE_NOW",
            },
        },
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()
    sub_id       = data["id"]
    approval_url = next(lnk["href"] for lnk in data["links"] if lnk["rel"] == "approve")
    return sub_id, approval_url


def get_subscription(client_id: str, secret: str, subscription_id: str) -> dict:
    """Lấy chi tiết subscription để xác nhận status."""
    token = _get_access_token(client_id, secret)
    resp = requests.get(
        f"{PAYPAL_API}/v1/billing/subscriptions/{subscription_id}",
        headers={"Authorization": f"Bearer {token}"},
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()
