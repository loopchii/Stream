"""Public backend spine for the Stream repository.

This package turns the repo's analysis surface into a real Python runtime:
analytics, orchestration, persistence, exports, and API-facing state all live
here instead of being scattered across the browser.
"""

from .config import RuntimeConfig
from .models import FrontendStateEnvelope, RuntimeArtifact, RuntimeSnapshot
from .services.runtime import StreamRuntime

__all__ = [
    "FrontendStateEnvelope",
    "RuntimeArtifact",
    "RuntimeConfig",
    "RuntimeSnapshot",
    "StreamRuntime",
]
