from __future__ import annotations

import re


def slugify(value: str) -> str:
    cleaned = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return cleaned or "item"


def sentence_case(value: str) -> str:
    value = (value or "").strip()
    if not value:
        return ""
    return value[0].upper() + value[1:]
