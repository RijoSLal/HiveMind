from pathlib import Path
from uuid import uuid4


def save_upload(upload_dir: Path, filename: str, content: bytes) -> Path:
    upload_dir.mkdir(parents=True, exist_ok=True)
    safe_name = f"{uuid4().hex}_{Path(filename).name}"
    path = upload_dir / safe_name
    path.write_bytes(content)
    return path
