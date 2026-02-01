from pydantic import BaseModel
from pathlib import Path
import os

class Settings(BaseModel):
    data_dir: Path = Path(os.getenv("DATA_DIR", "app/data"))
    upload_dir: Path = Path(os.getenv("UPLOAD_DIR", "app/data/uploads"))
    google_application_credentials: str | None = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    use_mock_ota: bool = os.getenv("USE_MOCK_OTA", "0") == "1"
    gha_feed_path: str | None = os.getenv("GHA_FEED_PATH")
    gha_api_base: str | None = os.getenv("GHA_API_BASE")
    allow_scraping: bool = os.getenv("ALLOW_SCRAPING", "0") == "1"
    scrape_timeout_ms: int = int(os.getenv("SCRAPE_TIMEOUT_MS", "30000"))
    scrape_headless: bool = os.getenv("SCRAPE_HEADLESS", "1") == "1"
    scrape_storage_state: str | None = os.getenv("SCRAPE_STORAGE_STATE")
    scrape_cookies_txt: str | None = os.getenv("SCRAPE_COOKIES_TXT")
    use_cloudscraper: bool = os.getenv("USE_CLOUDSCRAPER", "0") == "1"
    serpapi_api_key: str | None = os.getenv("SERPAPI_API_KEY")
    hotelzify_api_base: str | None = os.getenv("HOTELZIFY_API_BASE")
    hotelzify_api_key: str | None = os.getenv("HOTELZIFY_API_KEY")

settings = Settings()
