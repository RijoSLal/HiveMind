import requests
from dataclasses import dataclass
from app.config import settings

@dataclass
class OfficialRate:
    property_name: str
    currency: str
    total_price: float
    base_price: float | None = None
    taxes: float | None = None
    fees: float | None = None
    room_name: str | None = None
    meal_plan: str | None = None


def fetch_official_rate(payload: dict) -> OfficialRate:
    if not settings.hotelzify_api_base:
        raise RuntimeError("HOTELZIFY_API_BASE not set")

    headers = {}
    if settings.hotelzify_api_key:
        headers["Authorization"] = f"Bearer {settings.hotelzify_api_key}"

    url = settings.hotelzify_api_base.rstrip("/") + "/rates"
    resp = requests.post(url, json=payload, headers=headers, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    return OfficialRate(
        property_name=data.get("property_name") or payload.get("property_name"),
        currency=data.get("currency"),
        total_price=float(data.get("total_price")),
        base_price=data.get("base_price"),
        taxes=data.get("taxes"),
        fees=data.get("fees"),
        room_name=data.get("room_name"),
        meal_plan=data.get("meal_plan"),
    )
