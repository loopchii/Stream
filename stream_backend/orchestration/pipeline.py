from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Mapping

from data_engineering import build_data_engineering_snapshot
from stream_backend.analytics import (
    build_backend_contract_surface,
    build_comparative_surface,
    build_frontend_state,
)
from stream_backend.config import RuntimeConfig
from stream_backend.orchestration.runtime import build_orchestration_surface
from stream_backend.utils import dataframe_overview


@dataclass
class StreamPipeline:
    config: RuntimeConfig
    representation_results_fn: Callable[[int], Mapping[str, Any]]
    representation_df_fn: Callable[[], Any]
    music_report_fn: Callable[[], Mapping[str, Any]]
    music_df_fn: Callable[[], Any]
    music_index_fn: Callable[[], Mapping[str, Any]]

    def execute(self, sample_size: int, generated_at: str) -> dict[str, Any]:
        representation = dict(self.representation_results_fn(sample_size))
        df = self.representation_df_fn()
        representation["row_count"] = int(len(df))
        representation["frame_overview"] = dataframe_overview(df)
        music_report = dict(self.music_report_fn())
        music_index = dict(self.music_index_fn())
        music_df = self.music_df_fn()
        data_engineering = build_data_engineering_snapshot(
            synthetic_df=df,
            synthetic_results=representation,
            music_df=music_df,
            music_quality=music_report.get("quality", {}),
        )
        orchestration = build_orchestration_surface(self.config, generated_at, sample_size)
        frontend_state = build_frontend_state(
            generated_at=generated_at,
            sample_size=sample_size,
            representation=representation,
            music_report=music_report,
            music_index=music_index,
            data_engineering=data_engineering,
        )
        comparatives = build_comparative_surface(representation, music_report, music_index)
        contracts = build_backend_contract_surface(self.config)
        orchestration["contract_surface"] = contracts
        return {
            "representation": representation,
            "music": music_report,
            "music_index": music_index,
            "data_engineering": data_engineering,
            "frontend_state": frontend_state,
            "orchestration": orchestration,
            "comparatives": comparatives,
        }
