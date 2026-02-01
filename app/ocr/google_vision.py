from google.cloud import vision
from pathlib import Path
from typing import Optional

class GoogleVisionOCR:
    def __init__(self, credentials_path: Optional[str] = None):
        if credentials_path:
            self.client = vision.ImageAnnotatorClient.from_service_account_file(credentials_path)
        else:
            self.client = vision.ImageAnnotatorClient()

    def extract_text(self, image_path: Path) -> str:
        with image_path.open("rb") as f:
            content = f.read()
        image = vision.Image(content=content)
        response = self.client.text_detection(image=image)
        if response.error.message:
            raise RuntimeError(f"Google Vision error: {response.error.message}")
        texts = response.text_annotations
        if not texts:
            return ""
        # First annotation contains full text
        return texts[0].description.strip()
