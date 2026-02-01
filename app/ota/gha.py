import requests
from app.ota.base import OtaProvider
from app.models import DisputeRequest, OtaQuote
from app.config import settings

SERPAPI_ENDPOINT = "https://serpapi.com/search.json"

OTA_SOURCE_MAP = {
    "mmt": "MakeMyTrip",
    "agoda": "Agoda",
    "booking": "Booking.com",
    "skyscanner": "Skyscanner",
}


def _pick_property(properties: list[dict], name: str) -> dict | None:
    target = name.lower().strip()
    best = None
    for p in properties:
        pname = (p.get("name") or "").lower()
        if target and target in pname:
            return p
        if best is None:
            best = p
    return best


def _pick_price(prices: list[dict], ota: str) -> dict | None:
    if not prices:
        return None
    target_source = OTA_SOURCE_MAP.get(ota)
    if target_source:
        for pr in prices:
            if (pr.get("source") or "").lower().find(target_source.lower()) >= 0:
                return pr
    # fallback to lowest total_rate
    best = None
    best_val = None
    for pr in prices:
        total = pr.get("total_rate") or {}
        val = total.get("extracted_lowest")
        if isinstance(val, (int, float)):
            if best_val is None or val < best_val:
                best_val = val
                best = pr
    return best or prices[0]


class GoogleHotelAdsProvider(OtaProvider):
    def get_quote(self, req: DisputeRequest) -> OtaQuote:
        if not settings.serpapi_api_key:
            raise NotImplementedError("SERPAPI_API_KEY not set for GHA provider.")

        params = {
            "engine": "google_hotels",
            "q": req.property_name,
            "check_in_date": req.check_in.isoformat(),
            "check_out_date": req.check_out.isoformat(),
            "adults": req.occupancy,
            "children": req.children,
            "currency": req.currency,
            "hl": "en",
            "gl": "in",
            "api_key": settings.serpapi_api_key,
        }
        resp = requests.get(SERPAPI_ENDPOINT, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        properties = data.get("properties") or []
        prop = _pick_property(properties, req.property_name)
        if not prop:
            raise RuntimeError("GHA property not found.")

        token = prop.get("property_token")
        if not token:
            raise RuntimeError("GHA property token missing.")

        detail_params = {
            "engine": "google_hotels_property_details",
            "property_token": token,
            "check_in_date": req.check_in.isoformat(),
            "check_out_date": req.check_out.isoformat(),
            "adults": req.occupancy,
            "children": req.children,
            "currency": req.currency,
            "hl": "en",
            "gl": "in",
            "api_key": settings.serpapi_api_key,
        }
        dresp = requests.get(SERPAPI_ENDPOINT, params=detail_params, timeout=30)
        dresp.raise_for_status()
        details = dresp.json()

        prices = details.get("prices") or []
        chosen = _pick_price(prices, req.ota)

        base_price = None
        taxes = None
        total_price = None
        price = None

        if chosen:
            total = chosen.get("total_rate") or {}
            total_price = total.get("extracted_lowest")
            base_price = total.get("extracted_before_taxes_fees")
            if isinstance(total_price, (int, float)) and isinstance(base_price, (int, float)):
                taxes = total_price - base_price
            price = total_price

        if price is None:
            # fallback to search result rate_per_night if details missing
            rate = prop.get("rate_per_night") or {}
            price = rate.get("extracted_lowest")
            base_price = rate.get("extracted_before_taxes_fees")
            total_price = price

        if price is None:
            raise RuntimeError("GHA price not found.")

        return OtaQuote(
            ota="gha",
            property_name=prop.get("name") or req.property_name,
            room_name=req.room_name,
            meal_plan=req.meal_plan,
            occupancy=req.occupancy,
            currency=req.currency,
            price=price,
            base_price=base_price,
            taxes=taxes,
            fees=None,
            total_price=total_price or price,
            rate_plan=(chosen or {}).get("source"),
        )
