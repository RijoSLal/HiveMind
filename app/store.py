from typing import Dict
from app.models import DisputeResponse, ReviewDecision

# In-memory store for demo/dev usage only.
_store: Dict[str, DisputeResponse] = {}


def save_dispute(resp: DisputeResponse) -> None:
    _store[resp.dispute_id] = resp


def get_dispute(dispute_id: str) -> DisputeResponse | None:
    return _store.get(dispute_id)


def apply_review(dispute_id: str, decision: ReviewDecision) -> DisputeResponse | None:
    resp = _store.get(dispute_id)
    if resp is None:
        return None
    resp.status = "approved" if decision.status == "approved" else "rejected"
    return resp
