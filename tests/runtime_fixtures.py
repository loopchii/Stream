from __future__ import annotations

from pathlib import Path

import pandas as pd

from stream_backend.config import RuntimeConfig
from stream_backend.services.runtime import StreamRuntime


def synthetic_df() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "id": 1,
                "platform": "netflix",
                "genre": "drama",
                "media_type": "film",
                "year": 2024,
                "gender": "female",
                "race": "asian",
                "age_group": "adult",
                "role_type": "lead",
                "screen_time": 62.0,
                "dialogue_words": 1300,
                "sentiment_score": 0.21,
                "centrality": 0.77,
                "is_protagonist": True,
            },
            {
                "id": 2,
                "platform": "hulu",
                "genre": "comedy",
                "media_type": "series",
                "year": 2025,
                "gender": "male",
                "race": "white",
                "age_group": "adult",
                "role_type": "support",
                "screen_time": 48.0,
                "dialogue_words": 980,
                "sentiment_score": 0.14,
                "centrality": 0.61,
                "is_protagonist": False,
            },
        ]
    )


def music_df() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "title": "Moon Bloom",
                "channel": "Luna Vale",
                "view_count": 4_560_000,
                "duration_min": 3.4,
                "channel_follower_count": 1_200_000,
                "virality_coefficient": 3.8,
                "tag_count": 11,
                "description_len": 280,
                "genre": "pop",
                "is_official": 1,
                "collaboration_count": 1,
                "detected_language": "English",
                "published_at": "2025-02-01T00:00:00Z",
                "published_year": 2025,
                "likes": 225000,
                "engagement_ratio": 0.049,
                "source": "primary_top100",
                "country": "US",
            },
            {
                "title": "Glass Harbor",
                "channel": "North Field",
                "view_count": 8_900_000,
                "duration_min": 4.1,
                "channel_follower_count": 2_400_000,
                "virality_coefficient": 3.7,
                "tag_count": 14,
                "description_len": 310,
                "genre": "alternative",
                "is_official": 1,
                "collaboration_count": 2,
                "detected_language": "English",
                "published_at": "2025-04-12T00:00:00Z",
                "published_year": 2025,
                "likes": 410000,
                "engagement_ratio": 0.046,
                "source": "primary_top100",
                "country": "GB",
            },
        ]
    )


def representation_results(sample_size: int = 5000) -> dict:
    return {
        "overall_metrics": {
            "gender_parity": 0.68,
            "diversity_index": 0.77,
        },
        "advanced_metrics": {
            "equity_score": 0.74,
            "inequality": {
                "screen_time": {
                    "gini": 0.32,
                }
            },
        },
        "insights": [
            {"title": "Lead visibility narrows faster than the field looks at first pass."},
            {"title": "Dialogue pressure does not distribute evenly across role types."},
        ],
        "row_count": sample_size,
    }


def music_report() -> dict:
    return {
        "overview": {
            "n_songs": 2,
            "total_views": 13_460_000,
            "n_channels": 2,
        },
        "inequality": {
            "gini": 0.41,
            "top3_channel_share": 0.52,
        },
        "songs": [
            {"title": "Moon Bloom"},
            {"title": "Glass Harbor"},
        ],
        "bias": {
            "role_perspectives": {
                "artist": (
                    "Artists need to know whether the field is rewarding novelty "
                    "or just repeating scale."
                ),
                "consumer": "Consumers deserve to know when discovery has collapsed into a loop.",
                "business": (
                    "Business teams need an honest read on where reach is broad "
                    "and where it is over-concentrated."
                ),
                "research": "Researchers need claim boundaries and source cohort honesty before they cite a result.",
            }
        },
        "quality": {
            "coverage": {
                "publication_year_explicit_share": 0.80,
                "publication_year_inferred_share": 0.20,
            }
        },
    }


def music_index() -> dict:
    return {
        "summary": {
            "catalog_song_count": 2,
            "discovered_music_files": 1,
            "matched_catalog_songs": 1,
            "parsed_note_events": 12,
        },
        "pieces": [
            {
                "title": "Moon Bloom",
                "note_profile": {"note_events": 12},
            },
            {
                "title": "Glass Harbor",
                "note_profile": {"note_events": 0},
            },
        ],
    }


def build_runtime(base_dir: Path) -> StreamRuntime:
    config = RuntimeConfig.from_base_dir(base_dir)
    return StreamRuntime(
        config=config,
        representation_results_fn=representation_results,
        representation_df_fn=synthetic_df,
        music_report_fn=music_report,
        music_df_fn=music_df,
        music_index_fn=music_index,
    )
