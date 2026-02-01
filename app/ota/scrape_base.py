from contextlib import contextmanager
from pathlib import Path
from typing import Optional
from playwright.sync_api import sync_playwright
from app.config import settings
from app.ota.cookies import load_cookies

@contextmanager
def browser_page():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=settings.scrape_headless)
        context = browser.new_context(storage_state=settings.scrape_storage_state)
        if settings.scrape_cookies_txt:
            cookies = load_cookies(Path(settings.scrape_cookies_txt))
            if cookies:
                context.add_cookies(cookies)
        page = context.new_page()
        try:
            yield page
        finally:
            browser.close()


def fetch_text_from_url(url: str) -> str:
    if not settings.allow_scraping:
        raise NotImplementedError("Scraping disabled. Set ALLOW_SCRAPING=1.")

    if settings.use_cloudscraper:
        import cloudscraper
        scraper = cloudscraper.create_scraper()
        resp = scraper.get(url, timeout=settings.scrape_timeout_ms / 1000)
        resp.raise_for_status()
        return resp.text

    with browser_page() as page:
        page.goto(url, timeout=settings.scrape_timeout_ms, wait_until="networkidle")
        return page.content()


def extract_text_by_selector(url: str, selector: str) -> Optional[str]:
    if not settings.allow_scraping:
        raise NotImplementedError("Scraping disabled. Set ALLOW_SCRAPING=1.")

    with browser_page() as page:
        page.goto(url, timeout=settings.scrape_timeout_ms, wait_until="networkidle")
        el = page.query_selector(selector)
        if el is None:
            return None
        return el.inner_text().strip()
