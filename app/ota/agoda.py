from urllib.parse import urljoin
from playwright.sync_api import sync_playwright
from app.ota.base import OtaProvider
from app.models import DisputeRequest, OtaQuote
from app.parsing import parse_price_from_text, parse_first_price
from app.config import settings
from app.matching_rules import pick_best_room

class AgodaProvider(OtaProvider):
    def get_quote(self, req: DisputeRequest) -> OtaQuote:
        if not settings.allow_scraping:
            raise NotImplementedError("Scraping disabled. Set ALLOW_SCRAPING=1.")

        search_url = (
            "https://www.agoda.com/search"
            f"?query={req.property_name.replace(' ', '+')}"
            f"&checkIn={req.check_in}"
            f"&checkOut={req.check_out}"
            f"&adults={req.occupancy}"
            f"&children={req.children}"
            f"&rooms=1"
        )

        target_url = req.evidence_url

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=settings.scrape_headless)
            context = browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
                locale="en-GB",
                timezone_id="Asia/Kolkata",
                viewport={"width": 1366, "height": 900},
            )
            page = context.new_page()

            if target_url is None:
                page.goto(search_url, wait_until="domcontentloaded", timeout=settings.scrape_timeout_ms)
                page.wait_for_timeout(5000)
                link = page.locator("a[data-selenium='hotel-name']").first
                href = link.get_attribute("href")
                if not href:
                    browser.close()
                    raise RuntimeError("Agoda search returned no property link.")
                target_url = urljoin("https://www.agoda.com", href)

            page.goto(target_url, wait_until="domcontentloaded", timeout=settings.scrape_timeout_ms)
            page.wait_for_timeout(7000)

            # Collect candidate blocks
            rows = page.query_selector_all("[data-selenium='room-grid-item']")
            candidates = []
            for row in rows:
                room_name = ""
                rn = row.query_selector("[data-selenium='room-name']")
                if rn:
                    room_name = (rn.inner_text() or "").strip()
                row_text = (row.inner_text() or "").strip()
                candidates.append({"row": row, "room_name": room_name, "meal": row_text})

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
            price_el = chosen.query_selector("[data-selenium='display-price']") or chosen.query_selector("[data-selenium='price']")
            if price_el:
                price_text = price_el.inner_text()

            taxes = None
            taxes_el = chosen.query_selector("[data-selenium='tax-and-fees']")
            if taxes_el:
                taxes = parse_first_price(taxes_el.inner_text() or "")

            price = parse_price_from_text(price_text or "") if price_text else None
            if price is None:
                browser.close()
                raise RuntimeError("Agoda price not found on page.")

            total_price = price
            base_price = None
            fees = None

            browser.close()

        return OtaQuote(
            ota="agoda",
            property_name=req.property_name,
            room_name=req.room_name,
            meal_plan=req.meal_plan,
            occupancy=req.occupancy,
            currency=req.currency,
            price=price,
            base_price=base_price,
            taxes=taxes,
            fees=fees,
            total_price=total_price,
        )
