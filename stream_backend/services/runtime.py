from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping

from stream_backend.config import RuntimeConfig
from stream_backend.exporters import (
    persist_runtime_snapshot,
    write_runtime_json_exports,
    write_runtime_markdown,
)
from stream_backend.orchestration import EpochClock, StreamPipeline, build_runtime_snapshot
from stream_backend.services.catalog import build_runtime_catalog
from stream_backend.services.snapshots import load_latest_runtime_snapshot
from stream_backend.utils import slugify


@dataclass
class StreamRuntime:
    config: RuntimeConfig
    representation_results_fn: Callable[[int], Mapping[str, Any]]
    representation_df_fn: Callable[[], Any]
    music_report_fn: Callable[[], Mapping[str, Any]]
    music_df_fn: Callable[[], Any]
    music_index_fn: Callable[[], Mapping[str, Any]]

    def pipeline(self) -> StreamPipeline:
        return StreamPipeline(
            config=self.config,
            representation_results_fn=self.representation_results_fn,
            representation_df_fn=self.representation_df_fn,
            music_report_fn=self.music_report_fn,
            music_df_fn=self.music_df_fn,
            music_index_fn=self.music_index_fn,
        )

    def build_snapshot(self, sample_size: int | None = None) -> dict[str, Any]:
        size = int(sample_size or self.config.default_sample_size)
        clock = EpochClock.now()
        payloads = self.pipeline().execute(sample_size=size, generated_at=clock.generated_at)
        run_id = f"{slugify(self.config.owner_label)}-{clock.date_label}-n{size}"
        snapshot = build_runtime_snapshot(
            base_dir=self.config.base_dir,
            run_id=run_id,
            generated_at=clock.generated_at,
            sample_size=size,
            payloads=payloads,
        )
        payload = snapshot.to_dict()
        payload["catalog"] = build_runtime_catalog(self.config)
        return payload

    def materialize(
        self,
        sample_size: int | None = None,
        persist_sqlite: bool = True,
    ) -> dict[str, Any]:
        payload = self.build_snapshot(sample_size=sample_size)
        write_runtime_json_exports(self.config.base_dir, payload)
        write_runtime_markdown(self.config.report_path, payload)
        if persist_sqlite:
            snapshot = build_runtime_snapshot(
                base_dir=self.config.base_dir,
                run_id=payload["run_id"],
                generated_at=payload["created_at"],
                sample_size=payload["sample_size"],
                payloads=payload,
            )
            persist_runtime_snapshot(self.config.sqlite_path, snapshot)
        return payload

    def latest_snapshot(self) -> dict[str, Any] | None:
        return load_latest_runtime_snapshot(self.config.sqlite_path)
