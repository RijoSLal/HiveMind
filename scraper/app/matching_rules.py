import re
from typing import Iterable

MEAL_MAP = {
    "room only": ["room only", "no meals"],
    "breakfast": ["breakfast", "breakfast included", "breakfast buffet", "bf"],
    "half board": ["half board", "hb"],
    "full board": ["full board", "fb"],
    "all inclusive": ["all inclusive", "ai"],
}


def _clean(text: str) -> str:
    text = text.lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def normalize_room(text: str) -> str:
    if not text:
        return ""
    t = _clean(text)
    for drop in ["room", "bed", "suite", "view", "non refundable", "refundable", "free cancellation", "pay at property"]:
        t = t.replace(drop, " ")
    t = re.sub(r"\s+", " ", t).strip()
    return t


def normalize_meal(text: str) -> str:
    t = _clean(text)
    for canon, variants in MEAL_MAP.items():
        for v in variants:
            if v in t:
                return canon
    return ""


def score_match(room_text: str, meal_text: str, target_room: str, target_meal: str) -> int:
    room_norm = normalize_room(room_text)
    target_room_norm = normalize_room(target_room)
    meal_norm = normalize_meal(meal_text or room_text)
    target_meal_norm = normalize_meal(target_meal)

    score = 0
    if target_room_norm and target_room_norm in room_norm:
        score += 2
    if meal_norm and target_meal_norm and meal_norm == target_meal_norm:
        score += 2
    if target_room_norm and room_norm == target_room_norm:
        score += 1
    return score


def pick_best_room(candidates: Iterable[dict], target_room: str, target_meal: str):
    scored = []
    for c in candidates:
        score = score_match(c.get("room_name", ""), c.get("meal", ""), target_room, target_meal)
        scored.append((score, c))
    scored.sort(key=lambda x: x[0], reverse=True)
    return scored
