from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone


@dataclass(frozen=True)
class EpochClock:
    generated_at: str

    @property
    def date_label(self) -> str:
        return self.generated_at.split("T", 1)[0]

    @classmethod
    def now(cls) -> "EpochClock":
        value = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
        return cls(generated_at=value)
