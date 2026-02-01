from app.ota.base import OtaProvider
from app.models import DisputeRequest, OtaQuote

class MockProvider(OtaProvider):
    def get_quote(self, req: DisputeRequest) -> OtaQuote:
        return OtaQuote(
            ota=req.ota,
            property_name=req.property_name,
            room_name=req.room_name,
            meal_plan=req.meal_plan,
            occupancy=req.occupancy,
            currency=req.currency,
            price=req.claimed_price,
            rate_plan="mock",
            cancellation_policy="mock",
        )
