import re
from typing import Optional

CURRENCY_HINTS = ["INR", "USD", "EUR", "GBP"]


def parse_price_from_text(text: str) -> Optional[float]:
    if not text:
        return None
    # Find numbers with optional separators (e.g., 5,499 or 5499.00)
    matches = re.findall(r"\b\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?\b", text)
    if not matches:
        return None
    # Prefer largest value as likely total price
    values = []
    for m in matches:
        try:
            values.append(float(m.replace(",", "")))
        except ValueError:
            pass
    if not values:
        return None
    return max(values)


def parse_first_price(text: str) -> Optional[float]:
    if not text:
        return None
    match = re.search(r"\b\d{1,3}(?:,\d{3})*(?:\.\d{1,2})?\b", text)
    if not match:
        return None
    try:
        return float(match.group(0).replace(",", ""))
    except ValueError:
        return None


def parse_breakdown_from_text(text: str) -> dict:
    result = {
        "base_price": None,
        "taxes": None,
        "fees": None,
        "total_price": None,
    }
    if not text:
        return result

    lines = [l.strip() for l in text.splitlines() if l.strip()]
    for line in lines:
        low = line.lower()
        if result["total_price"] is None and any(k in low for k in ["total", "grand total", "payable", "amount to pay"]):
            result["total_price"] = parse_first_price(line)
        if result["base_price"] is None and any(k in low for k in ["base", "room price", "room rate"]):
            result["base_price"] = parse_first_price(line)
        if result["taxes"] is None and "tax" in low:
            result["taxes"] = parse_first_price(line)
        if result["fees"] is None and "fee" in low:
            result["fees"] = parse_first_price(line)

    return result
