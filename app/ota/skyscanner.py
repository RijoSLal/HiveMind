from app.ota.base import OtaProvider
from app.models import DisputeRequest, OtaQuote
from app.ota.scrape_base import fetch_text_from_url, extract_text_by_selector
from app.ota.selectors import SELECTORS
from app.parsing import parse_price_from_text, parse_first_price

class SkyscannerProvider(OtaProvider):
    def get_quote(self, req: DisputeRequest) -> OtaQuote:
        if not req.evidence_url:
            raise NotImplementedError("Skyscanner scraping requires evidence_url or custom URL builder.")

        selectors = SELECTORS["skyscanner"]
        base_text = extract_text_by_selector(req.evidence_url, selectors.base_price_selector) if selectors.base_price_selector else None
        taxes_text = extract_text_by_selector(req.evidence_url, selectors.taxes_selector) if selectors.taxes_selector else None
        fees_text = extract_text_by_selector(req.evidence_url, selectors.fees_selector) if selectors.fees_selector else None
        price_text = extract_text_by_selector(req.evidence_url, selectors.price_selector) if selectors.price_selector else None
        if price_text is None:
            price_text = fetch_text_from_url(req.evidence_url)

        price = parse_price_from_text(price_text or "")
        if price is None:
            raise RuntimeError("Skyscanner price not found on page.")
        base_price = parse_first_price(base_text or "") if base_text else None
        taxes = parse_first_price(taxes_text or "") if taxes_text else None
        fees = parse_first_price(fees_text or "") if fees_text else None

        return OtaQuote(
            ota="skyscanner",
            property_name=req.property_name,
            room_name=req.room_name,
            meal_plan=req.meal_plan,
            occupancy=req.occupancy,
            currency=req.currency,
            price=price,
            base_price=base_price,
            taxes=taxes,
            fees=fees,
            total_price=price,
        )
