from urllib.parse import urljoin
from playwright.sync_api import sync_playwright
from app.ota.base import OtaProvider
from app.models import DisputeRequest, OtaQuote
from app.parsing import parse_price_from_text, parse_first_price
from app.config import settings
from app.matching_rules import pick_best_room

class BookingProvider(OtaProvider):
    def get_quote(self, req: DisputeRequest) -> OtaQuote:
        if not settings.allow_scraping:
            raise NotImplementedError("Scraping disabled. Set ALLOW_SCRAPING=1.")

        search_url = (
            "https://www.booking.com/searchresults.en-gb.html"
            f"?ss={req.property_name.replace(' ', '+')}"
            f"&checkin={req.check_in}"
            f"&checkout={req.check_out}"
            f"&group_adults={req.occupancy}"
            f"&group_children={req.children}"
            f"&no_rooms=1"
        )

        target_url = req.evidence_url

        def accept_cookies(page):
            for selector in [
                "#onetrust-accept-btn-handler",
                "button#onetrust-accept-btn-handler",
                "button[data-testid='cookie-notification-accept-button']",
            ]:
                try:
                    if page.locator(selector).first.is_visible():
                        page.locator(selector).first.click()
                        break
                except Exception:
                    pass

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
                page.wait_for_timeout(4000)
                accept_cookies(page)
                page.wait_for_timeout(2000)

                link = page.locator("a[data-testid='title-link']").first
                href = link.get_attribute("href")
                if not href:
                    browser.close()
                    raise RuntimeError("Booking search returned no property link.")
                if href.startswith("https//"):
                    href = "https://" + href[len("https//"):]
                target_url = urljoin("https://www.booking.com", href)

            page.goto(target_url, wait_until="domcontentloaded", timeout=settings.scrape_timeout_ms)
            page.wait_for_timeout(6000)
            accept_cookies(page)

            # Locate room rows
            rows = page.query_selector_all("tr[data-block-id]")
            if not rows:
                browser.close()
                raise RuntimeError("Booking room table not found.")

            candidates = []
            for row in rows:
                room_name = ""
                rn = row.query_selector(".hprt-roomtype-link span") or row.query_selector(".hprt-roomtype-link")
                if rn:
                    room_name = (rn.inner_text() or "").strip()
                row_text = (row.inner_text() or "").strip()
                candidates.append({"row": row, "room_name": room_name, "meal": row_text})

            scored = pick_best_room(candidates, req.room_name, req.meal_plan)
            if not scored:
                browser.close()
                raise RuntimeError("Booking room candidates empty.")

            top_score = scored[0][0]
            top_candidates = [c for s, c in scored if s == top_score]
            chosen = top_candidates[0]["row"]
            if len(top_candidates) > 1 and top_score > 0:
                names = [c.get("room_name") for c in top_candidates if c.get("room_name")]
                if names:
                    browser.close()
                    raise RuntimeError("ambiguous_rooms: " + ", ".join(names[:5]))

            price_text = None
            price_el = chosen.query_selector(".bui-price-display__value")
            if price_el:
                price_text = price_el.inner_text()

            base_price = None
            rounded = chosen.get_attribute("data-hotel-rounded-price")
            if rounded and rounded.isdigit():
                base_price = float(rounded)

            taxes = None
            taxes_el = chosen.query_selector(".prd-taxes-and-fees-under-price")
            if taxes_el:
                raw = taxes_el.get_attribute("data-excl-charges-raw")
                if raw:
                    try:
                        taxes = float(raw)
                    except ValueError:
                        taxes = parse_first_price(raw)
                if taxes is None:
                    taxes = parse_first_price(taxes_el.inner_text() or "")

            price = parse_price_from_text(price_text or "") if price_text else None
            if price is None and base_price is not None:
                price = base_price

            total_price = None
            if base_price is not None and taxes is not None:
                total_price = base_price + taxes
            elif price is not None:
                total_price = price

            browser.close()

        if price is None:
            raise RuntimeError("Booking price not found on page.")
        fees = None

        return OtaQuote(
            ota="booking",
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
