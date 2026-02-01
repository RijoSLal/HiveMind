from dataclasses import dataclass

@dataclass
class SelectorPack:
    price_selector: str | None = None
    base_price_selector: str | None = None
    taxes_selector: str | None = None
    fees_selector: str | None = None
    currency_selector: str | None = None

# Provide site-specific selectors here when you confirm layout.
# These are intentionally blank because OTA DOMs change frequently.
SELECTORS = {
    "mmt": SelectorPack(
        # Fill these once you confirm current DOM selectors for MMT
        price_selector=None,
        base_price_selector=None,
        taxes_selector=None,
        fees_selector=None,
        currency_selector=None,
    ),
    "agoda": SelectorPack(),
    "booking": SelectorPack(),
    "skyscanner": SelectorPack(),
}
