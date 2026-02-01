from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from uuid import uuid4
from datetime import date
from app.models import DisputeRequest, DisputeResponse, ReviewDecision, AgentResponse
from app.config import settings
from app.ocr.google_vision import GoogleVisionOCR
from app.storage import save_upload
from app.verify import verify_dispute
from app.parsing import parse_price_from_text, parse_breakdown_from_text
from app.store import save_dispute, get_dispute, apply_review
from app.agent import build_agent_message

app = FastAPI(title="Hotelzify Dispute Service", version="0.1.0")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/disputes", response_model=DisputeResponse)
async def create_dispute(
    property_name: str = Form(...),
    check_in: date = Form(...),
    check_out: date = Form(...),
    room_name: str = Form(...),
    meal_plan: str = Form(...),
    occupancy: int = Form(...),
    children: int = Form(0),
    currency: str = Form(...),
    claimed_price: float = Form(...),
    ota: str = Form(...),
    user_note: str | None = Form(None),
    evidence_url: str | None = Form(None),
    image: UploadFile | None = File(None),
):
    req = DisputeRequest(
        property_name=property_name,
        check_in=check_in,
        check_out=check_out,
        room_name=room_name,
        meal_plan=meal_plan,
        occupancy=occupancy,
        children=children,
        currency=currency,
        claimed_price=claimed_price,
        ota=ota,
        user_note=user_note,
        evidence_url=evidence_url,
    )

    dispute_id = uuid4().hex
    ocr_text = None

    if image is not None:
        content = await image.read()
        image_path = save_upload(settings.upload_dir, image.filename, content)
        if settings.google_application_credentials is None:
            raise HTTPException(status_code=500, detail="GOOGLE_APPLICATION_CREDENTIALS not set")
        ocr = GoogleVisionOCR(settings.google_application_credentials)
        ocr_text = ocr.extract_text(image_path)

    parsed_price = parse_price_from_text(ocr_text or "")
    parsed_breakdown = parse_breakdown_from_text(ocr_text or "")

    best_quote, quotes, match, errors = verify_dispute(req)
    if best_quote is None:
        resp = DisputeResponse(
            dispute_id=dispute_id,
            status="no_provider",
            ocr_text=ocr_text,
            parsed_price=parsed_price,
            parsed_base_price=parsed_breakdown.get("base_price"),
            parsed_taxes=parsed_breakdown.get("taxes"),
            parsed_fees=parsed_breakdown.get("fees"),
            parsed_total_price=parsed_breakdown.get("total_price"),
            errors=errors,
        )
        save_dispute(resp)
        return resp

    status = "verified" if match and match.match else "mismatch"

    resp = DisputeResponse(
        dispute_id=dispute_id,
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
    save_dispute(resp)
    return resp


@app.get("/disputes/{dispute_id}", response_model=DisputeResponse)
def get_dispute_status(dispute_id: str):
    resp = get_dispute(dispute_id)
    if resp is None:
        raise HTTPException(status_code=404, detail="Not found")
    return resp


@app.post("/disputes/{dispute_id}/review", response_model=DisputeResponse)
def review_dispute(dispute_id: str, decision: ReviewDecision):
    resp = apply_review(dispute_id, decision)
    if resp is None:
        raise HTTPException(status_code=404, detail="Not found")
    return resp


@app.post("/agent/price-check", response_model=AgentResponse)
async def agent_price_check(req: DisputeRequest):
    # Lightweight path for chatbot integration; no file upload.
    dispute_id = uuid4().hex
    best_quote, quotes, match, errors = verify_dispute(req)
    status = "no_provider" if best_quote is None else ("verified" if match and match.match else "mismatch")

    resp = DisputeResponse(
        dispute_id=dispute_id,
        status=status,
        ota_quote=best_quote,
        sources=quotes,
        match=match,
        errors=errors,
    )
    save_dispute(resp)

    decision, message = build_agent_message(resp, req)
    return AgentResponse(
        dispute_id=dispute_id,
        decision=decision,
        message=message,
        data=resp,
    )
