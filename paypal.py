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


def create_order(client_id: str, secret: str, amount: str, plan: str,
                 return_url: str, cancel_url: str) -> tuple[str, str]:
    """Tạo PayPal order. Trả về (order_id, approval_url)."""
    token = _get_access_token(client_id, secret)
    resp = requests.post(
        f"{PAYPAL_API}/v2/checkout/orders",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json={
            "intent": "CAPTURE",
            "purchase_units": [{
                "amount": {"currency_code": "USD", "value": amount},
                "custom_id": plan,
                "description": f"nhacheocon - Gói {plan}",
            }],
            "application_context": {
                "return_url":   return_url,
                "cancel_url":   cancel_url,
                "brand_name":   "nhacheocon",
                "user_action":  "PAY_NOW",
                "landing_page": "BILLING",
            },
        },
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()
    order_id     = data["id"]
    approval_url = next(lnk["href"] for lnk in data["links"] if lnk["rel"] == "approve")
    return order_id, approval_url


def capture_order(client_id: str, secret: str, order_id: str) -> dict:
    """Capture PayPal order sau khi user approve. Trả về order details."""
    token = _get_access_token(client_id, secret)
    resp = requests.post(
        f"{PAYPAL_API}/v2/checkout/orders/{order_id}/capture",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()
