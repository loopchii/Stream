from __future__ import annotations

import hashlib
import json
from typing import Any


def stable_dumps(payload: Any) -> str:
    return json.dumps(payload, sort_keys=True, ensure_ascii=False, separators=(",", ":"))


def stable_hash(payload: Any) -> str:
    return hashlib.sha256(stable_dumps(payload).encode("utf-8")).hexdigest()
