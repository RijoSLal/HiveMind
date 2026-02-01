from urllib.parse import urljoin
from playwright.sync_api import sync_playwright
from app.ota.base import OtaProvider
from app.models import DisputeRequest, OtaQuote
from app.parsing import parse_price_from_text, parse_first_price
from app.config import settings
from app.matching_rules import pick_best_room

class MakeMyTripProvider(OtaProvider):
    def get_quote(self, req: DisputeRequest) -> OtaQuote:
        if not settings.allow_scraping:
            raise NotImplementedError("Scraping disabled. Set ALLOW_SCRAPING=1.")

        target_url = req.evidence_url
        if target_url is None:
            search_text = req.property_name.replace(" ", "+")
            target_url = (
                "https://www.makemytrip.com/hotels/hotel-listing/?searchText="
                + search_text
                + "&checkin="
                + req.check_in.strftime("%m%d%Y")
                + "&checkout="
                + req.check_out.strftime("%m%d%Y")
                + "&adults="
                + str(req.occupancy)
                + "&children="
                + str(req.children)
            )

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=settings.scrape_headless)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
                locale="en-GB",
                timezone_id="Asia/Kolkata",
                viewport={"width": 1366, "height": 900},
            )
            page = context.new_page()
            page.goto(target_url, wait_until="domcontentloaded", timeout=settings.scrape_timeout_ms)
            page.wait_for_timeout(8000)

            # If landing on listing page, click first hotel card
            if "hotel-listing" in page.url:
                link = page.locator("a[href*='hotel-details']").first
                href = link.get_attribute("href")
                if href:
                    page.goto(urljoin("https://www.makemytrip.com", href), wait_until="domcontentloaded", timeout=settings.scrape_timeout_ms)
                    page.wait_for_timeout(8000)

            # Attempt to find room cards
            rooms = page.query_selector_all("[class*='room']")
            candidates = []
            for r in rooms:
                txt = (r.inner_text() or "").strip()
                if len(txt) < 10:
                    continue
                candidates.append({"row": r, "room_name": txt.split("\n")[0], "meal": txt})

            chosen = None
            if candidates:
                scored = pick_best_room(candidates, req.room_name, req.meal_plan)
                top_score = scored[0][0]
                top_candidates = [c for s, c in scored if s == top_score]
                chosen = top_candidates[0]["row"]
                if len(top_candidates) > 1 and top_score > 0:
                    names = [c.get("room_name") or "Unknown room" for c in top_candidates[:5]]
                    browser.close()
                    raise RuntimeError("ambiguous_rooms: " + ", ".join(names))

            if chosen is None:
                chosen = page

            price_text = None
            price_el = chosen.query_selector("[class*='price']")
            if price_el:
                price_text = price_el.inner_text()
            else:
                price_text = page.inner_text("body")

            price = parse_price_from_text(price_text or "")
            if price is None:
                browser.close()
                raise RuntimeError("MMT price not found on page.")

            taxes = None
            taxes_el = chosen.query_selector("[class*='tax']")
            if taxes_el:
                taxes = parse_first_price(taxes_el.inner_text() or "")

            browser.close()

        return OtaQuote(
            ota="mmt",
            property_name=req.property_name,
            room_name=req.room_name,
            meal_plan=req.meal_plan,
            occupancy=req.occupancy,
            currency=req.currency,
            price=price,
            base_price=None,
            taxes=taxes,
            fees=None,
            total_price=price,
        )
