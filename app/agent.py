from app.models import DisputeRequest, DisputeResponse


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
