from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import date

OtaName = Literal["gha", "mmt", "agoda", "booking", "skyscanner"]

class DisputeRequest(BaseModel):
    property_name: str = Field(..., min_length=2)
    check_in: date
    check_out: date
    room_name: str = Field(..., min_length=2)
    meal_plan: str = Field(..., min_length=1)
    occupancy: int = Field(..., ge=1)
    children: int = Field(0, ge=0)
    currency: str = Field(..., min_length=3, max_length=3)
    claimed_price: float = Field(..., gt=0)
    ota: OtaName
    user_note: Optional[str] = None
    evidence_url: Optional[str] = None

class OtaQuote(BaseModel):
    ota: OtaName
    property_name: str
    room_name: str
    meal_plan: str
    occupancy: int
    currency: str
    price: float
    base_price: Optional[float] = None
    taxes: Optional[float] = None
    fees: Optional[float] = None
    total_price: Optional[float] = None
    rate_plan: Optional[str] = None
    cancellation_policy: Optional[str] = None

class MatchResult(BaseModel):
    match: bool
    reason: Optional[str] = None

class DisputeResponse(BaseModel):
    dispute_id: str
    status: str
    ota_quote: Optional[OtaQuote] = None
    sources: Optional[list[OtaQuote]] = None
    match: Optional[MatchResult] = None
    ocr_text: Optional[str] = None
    parsed_price: Optional[float] = None
    parsed_base_price: Optional[float] = None
    parsed_taxes: Optional[float] = None
    parsed_fees: Optional[float] = None
    parsed_total_price: Optional[float] = None
    errors: Optional[list[str]] = None

class ReviewDecision(BaseModel):
    status: Literal["approved", "rejected"]
    reviewer_note: Optional[str] = None

class AgentResponse(BaseModel):
    dispute_id: str
    decision: Literal["verified_lower_price", "mismatch", "unable_to_verify"]
    message: str
    data: DisputeResponse
