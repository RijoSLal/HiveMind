from app.models import DisputeRequest, DisputeResponse, AgentResponse
from app.config import settings
from app.ocr.google_vision import GoogleVisionOCR
from app.parsing import parse_price_from_text, parse_breakdown_from_text
from app.storage import save_upload
from app.verify import verify_dispute


def build_agent_message(resp: DisputeResponse, req: DisputeRequest) -> tuple[str, str]:
    if resp.errors:
        for err in resp.errors:
            if err.startswith("ambiguous_rooms:"):
                candidates = err.split(":", 1)[1].strip()
                message = (
                    "I found multiple possible room matches on the OTA. "
                    f"Please confirm the exact room name: {candidates}."
                )
                return "unable_to_verify", message

    if resp.status == "verified":
        price = resp.ota_quote.total_price if resp.ota_quote and resp.ota_quote.total_price else (resp.ota_quote.price if resp.ota_quote else None)
        message = f"I verified a lower price on {req.ota.upper()} for the same room and meal plan. Total is {price} {req.currency}."
        return "verified_lower_price", message

    if resp.status == "mismatch":
        price = resp.ota_quote.total_price if resp.ota_quote and resp.ota_quote.total_price else (resp.ota_quote.price if resp.ota_quote else None)
        message = f"I checked {req.ota.upper()} for your dates/room/meal. I see {price} {req.currency}, which does not match a lower price claim."
        return "mismatch", message

    hint = "I couldn't verify yet. Please share the exact OTA room link or a screenshot for OCR." \
        if req.evidence_url is None else "I couldn't verify yet. The OTA page needs manual review."
    return "unable_to_verify", hint


def run_verification(
    req: DisputeRequest,
    image_bytes: bytes | None = None,
    filename: str = "upload.jpg",
) -> AgentResponse:
    ocr_text = None
    parsed_price = None
    parsed_breakdown = {"base_price": None, "taxes": None, "fees": None, "total_price": None}

    if image_bytes is not None:
        if settings.google_application_credentials is None:
            raise RuntimeError("GOOGLE_APPLICATION_CREDENTIALS not set")
        image_path = save_upload(settings.upload_dir, filename, image_bytes)
        ocr = GoogleVisionOCR(settings.google_application_credentials)
        ocr_text = ocr.extract_text(image_path)
        parsed_price = parse_price_from_text(ocr_text or "")
        parsed_breakdown = parse_breakdown_from_text(ocr_text or "")

    best_quote, quotes, match, errors = verify_dispute(req)
    status = "no_provider" if best_quote is None else ("verified" if match and match.match else "mismatch")

    resp = DisputeResponse(
        dispute_id="inline",
        status=status,
        ota_quote=best_quote,
        sources=quotes,
        match=match,
        ocr_text=ocr_text,
        parsed_price=parsed_price,
        parsed_base_price=parsed_breakdown.get("base_price"),
        parsed_taxes=parsed_breakdown.get("taxes"),
        parsed_fees=parsed_breakdown.get("fees"),
        parsed_total_price=parsed_breakdown.get("total_price"),
        errors=errors,
    )

    decision, message = build_agent_message(resp, req)
    return AgentResponse(
        dispute_id=resp.dispute_id,
        decision=decision,
        message=message,
        data=resp,
    )
