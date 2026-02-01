from dataclasses import dataclass
from typing import Optional

@dataclass
class CompareResult:
    can_compare: bool
    lower: Optional[bool]
    message: str


def compare_prices(official_total: Optional[float], official_currency: Optional[str], user_total: Optional[float], user_currency: Optional[str]) -> CompareResult:
    if official_total is None or user_total is None:
        return CompareResult(False, None, "I need the official price and the OTA price to compare.")
    if official_currency and user_currency and official_currency.upper() != user_currency.upper():
        return CompareResult(False, None, "The prices are in different currencies, so I can't compare them yet.")

    if user_total < official_total:
        return CompareResult(True, True, f"The OTA price is lower than our official price.")
    if user_total == official_total:
        return CompareResult(True, False, f"The OTA price matches our official price.")
    return CompareResult(True, False, f"The OTA price is not lower than our official price.")
