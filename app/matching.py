from app.models import DisputeRequest, OtaQuote, MatchResult

# Strict match: all key fields must match, price must be <= claimed price to validate lower/equal.
# Adjust comparison if you want to accept lower-only or equal-only.

def match_dispute(req: DisputeRequest, quote: OtaQuote) -> MatchResult:
    if req.property_name.strip().lower() != quote.property_name.strip().lower():
        return MatchResult(match=False, reason="property_name_mismatch")
    if req.room_name.strip().lower() != quote.room_name.strip().lower():
        return MatchResult(match=False, reason="room_name_mismatch")
    if req.meal_plan.strip().lower() != quote.meal_plan.strip().lower():
        return MatchResult(match=False, reason="meal_plan_mismatch")
    if req.occupancy != quote.occupancy:
        return MatchResult(match=False, reason="occupancy_mismatch")
    if req.currency.upper() != quote.currency.upper():
        return MatchResult(match=False, reason="currency_mismatch")
    compare_price = quote.total_price if quote.total_price is not None else quote.price
    if compare_price > req.claimed_price:
        return MatchResult(match=False, reason="price_not_lower_or_equal")
    return MatchResult(match=True)
