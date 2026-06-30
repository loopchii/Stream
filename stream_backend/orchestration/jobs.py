from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RuntimeJob:
    name: str
    description: str
    output_name: str
    blocking: bool = True
