from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class RuntimeConfig:
    """Filesystem and runtime settings for the public Stream backend."""

    base_dir: Path
    sample_sizes: tuple[int, ...] = (1000, 5000, 10000, 25000)
    default_sample_size: int = 5000
    sqlite_filename: str = "stream_runtime.sqlite3"
    static_dirname: str = "data"
    system_dirname: str = "system"
    db_subdir: str = "runtime"
    report_filename: str = "runtime_surface.md"
    timezone_label: str = "UTC"
    owner_label: str = "Loopchii Stream"
    dataset_family: str = "public_research_surface"
    music_lane_label: str = "public_music_lane"
    synthetic_lane_label: str = "synthetic_representation_lane"
    tags: tuple[str, ...] = ("python", "sqlite", "analytics", "music", "governance")
    build_targets: tuple[str, ...] = ("api", "static", "sqlite")
    cache_enabled: bool = True
    notes: tuple[str, ...] = field(
        default_factory=lambda: (
            "Synthetic and public lanes stay separated.",
            "Static exports and API responses should originate from the same runtime package.",
            "SQLite snapshots are for inspectable persistence, not for hiding logic.",
        )
    )

    @property
    def data_dir(self) -> Path:
        return self.base_dir / self.static_dirname

    @property
    def system_dir(self) -> Path:
        return self.data_dir / self.system_dirname

    @property
    def db_dir(self) -> Path:
        return self.system_dir / self.db_subdir

    @property
    def sqlite_path(self) -> Path:
        return self.db_dir / self.sqlite_filename

    @property
    def report_path(self) -> Path:
        return self.system_dir / self.report_filename

    @classmethod
    def from_base_dir(cls, base_dir: Path) -> "RuntimeConfig":
        return cls(base_dir=Path(base_dir).resolve())
