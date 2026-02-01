# Hotelzify Dispute Service

FastAPI service to intake price-dispute requests (with optional images), run OCR via Google Vision, and validate against OTA quotes.

## Features
- Multipart intake with image upload
- Google Vision OCR for screenshots
- OTA provider interface (MMT/Agoda/Booking/Skyscanner)
- GHA-first provider chain with OTA fallbacks (MMT/Agoda/Booking/Skyscanner)
- Strict matching (no tolerance)
- Evidence-only flow with OCR parsing + review endpoint
- Docker-ready

## Quick start (local)
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
$env:GOOGLE_APPLICATION_CREDENTIALS="C:\path\to\service-account.json"
$env:USE_MOCK_OTA="1"
uvicorn app.main:app --reload
```

## Quick start (Docker)
```powershell
docker build -t hotelzify-disputes .
docker run -p 8000:8000 -e GOOGLE_APPLICATION_CREDENTIALS=/creds/sa.json -e USE_MOCK_OTA=1 -v C:\path\to\sa.json:/creds/sa.json hotelzify-disputes
```

## API
- `GET /health`
- `POST /disputes`
- `GET /disputes/{id}`
- `POST /disputes/{id}/review`
- `POST /agent/price-check`

Example request:
```powershell
curl -X POST http://localhost:8000/disputes `
  -F "property_name=Hotel Example" `
  -F "check_in=2026-02-10" `
  -F "check_out=2026-02-12" `
  -F "room_name=Deluxe Room" `
  -F "meal_plan=Breakfast" `
  -F "occupancy=2" `
  -F "children=0" `
  -F "currency=INR" `
  -F "claimed_price=5499" `
  -F "ota=mmt" `
  -F "user_note=Lower price seen on MMT" `
  -F "evidence_url=https://example.com/ota/room?query=..." `
  -F "image=@C:\path\to\screenshot.jpg"
```

Agent request (JSON):
```powershell
curl -X POST http://localhost:8000/agent/price-check `
  -H "Content-Type: application/json" `
  -d '{\"property_name\":\"Sterling Kodai Lake\",\"check_in\":\"2026-04-01\",\"check_out\":\"2026-04-03\",\"room_name\":\"Deluxe\",\"meal_plan\":\"Breakfast\",\"occupancy\":2,\"children\":0,\"currency\":\"INR\",\"claimed_price\":5499,\"ota\":\"mmt\",\"evidence_url\":\"https://www.makemytrip.com/...\"}'
```

## Python helper (scraper + OCR)
Use `run_verification()` to execute OCR (if image provided) and scraping in one call.

```python
from app.agent import run_verification
from app.models import DisputeRequest
from datetime import date

req = DisputeRequest(
    property_name="Sterling Varca Goa",
    check_in=date(2026, 4, 1),
    check_out=date(2026, 4, 3),
    room_name="Classic Room",
    meal_plan="Breakfast",
    occupancy=2,
    children=1,
    currency="INR",
    claimed_price=8500,
    ota="agoda",
)

# Optional: image_bytes from user screenshot
result = run_verification(req, image_bytes=None)
print(result.decision, result.message)
```

## Notes
- GHA and OTA providers are stubs; integrate official APIs/feeds or approved scraping inside `app/ota/*`.
- Provider chain is defined in `app/verify.py` (GHA first, then requested OTA).
- Strict matching is enforced in `app/matching.py`.
- Disputes are stored in-memory for now (`app/store.py`). Swap to a DB for production.
- Scrapers currently require `evidence_url` (deep link) until you provide site-specific URL builders/selectors in `app/ota/selectors.py`.
- For exact price breakdown, fill `base_price_selector`, `taxes_selector`, and `fees_selector` in `app/ota/selectors.py`.
- You can pass session cookies via `SCRAPE_COOKIES_TXT` (Netscape cookies.txt) or Playwright storage state via `SCRAPE_STORAGE_STATE`.
- Booking.com provider uses the search results page to resolve a property and then parses the room table for base price and taxes.
- Agoda and MMT providers use best-effort search -> property -> room matching; for highest accuracy pass `evidence_url` from the user.
- When multiple room matches are detected, responses include an `ambiguous_rooms:` error for the agent to request clarification.

## SerpAPI (Google Hotels)
If you want a more reliable price source, set `SERPAPI_API_KEY` and enable the GHA provider. The service uses the SerpAPI Google Hotels search and property details endpoints to fetch rates and sources.

Env vars:
- `SERPAPI_API_KEY` (required for GHA)

## Cloudscraper (optional)
Set `USE_CLOUDSCRAPER=1` to attempt Cloudflare-friendly HTTP fetches before falling back to Playwright.

## Hotelzify official pricing
Set `HOTELZIFY_API_BASE` (and optional `HOTELZIFY_API_KEY`) to fetch official Sterling prices for comparison.
The service calls `POST {HOTELZIFY_API_BASE}/rates` with:

```json
{
  "property_name": "...",
  "check_in": "YYYY-MM-DD",
  "check_out": "YYYY-MM-DD",
  "room_name": "...",
  "meal_plan": "...",
  "adults": 2,
  "children": 0,
  "currency": "INR"
}
```

Expected response:
```json
{
  "property_name": "...",
  "room_name": "...",
  "meal_plan": "...",
  "currency": "INR",
  "base_price": 12400,
  "taxes": 1786,
  "fees": 0,
  "total_price": 14186
}
```

## Comparison logic
If an official price is available, the agent compares:
- Official total vs OTA total (or OCR total if OTA missing)
- Same currency required

Agent response will explicitly state whether OTA is lower, equal, or higher than official.
