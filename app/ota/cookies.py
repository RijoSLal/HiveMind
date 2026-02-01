from __future__ import annotations
from pathlib import Path
from typing import List, Dict


def _parse_netscape_cookies(text: str) -> List[Dict]:
    cookies: List[Dict] = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) < 7:
            continue
        domain, flag, path, secure, expiry, name, value = parts[:7]
        cookies.append(
            {
                "name": name,
                "value": value,
                "domain": domain,
                "path": path,
                "expires": int(expiry) if expiry.isdigit() else -1,
                "httpOnly": False,
                "secure": secure.lower() == "true",
                "sameSite": "Lax",
            }
        )
    return cookies


def load_cookies(path: Path) -> List[Dict]:
    text = path.read_text(encoding="utf-8", errors="ignore")
    return _parse_netscape_cookies(text)
