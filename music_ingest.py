#!/usr/bin/env python3
"""
StreamLens Analytics - live music data extraction (YouTube Data API v3).

This module lets the app go *beyond* the bundled real CSV: when a
``YOUTUBE_API_KEY`` is available it pulls fresh, larger samples of top music
videos straight from YouTube and writes them in the exact same schema the
offline analysis already understands. With no key it is completely inert - the
rest of the app keeps running on the committed real dataset - so the code ships
and is testable without any credential.

Pipeline (key present):
    search.list   -> top music video IDs (category 10), ordered by view count
    videos.list   -> statistics, contentDetails(duration), snippet(tags, desc)
    channels.list -> subscriber counts

Only the Python standard library is used for HTTP, so there is no extra
dependency to install.

    # refresh the committed dataset in place (needs YOUTUBE_API_KEY)
    python music_ingest.py --max 100 --region US --out data_sources/youtube-top-100-songs-2025.csv

Author: Cazandra Aporbo, MS
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Dict, List, Optional

import pandas as pd

API_ROOT = "https://www.googleapis.com/youtube/v3"
BASE_DIR = Path(__file__).resolve().parent
DEFAULT_OUT = BASE_DIR / "data_sources" / "youtube-top-100-songs-2025.csv"

# Columns the offline pipeline (music_pipeline.engineer_features) expects.
SCHEMA = [
    "title", "fulltitle", "description", "view_count", "categories", "tags",
    "duration", "duration_string", "live_status", "thumbnail", "channel",
    "channel_url", "channel_follower_count",
]

_ISO_DURATION = re.compile(
    r"PT(?:(?P<h>\d+)H)?(?:(?P<m>\d+)M)?(?:(?P<s>\d+)S)?"
)


class MissingAPIKey(RuntimeError):
    """Raised when a live fetch is requested without a configured API key."""


def get_api_key(explicit: Optional[str] = None) -> Optional[str]:
    """Resolve the YouTube Data API key from an argument, env var or repo secret."""
    if explicit:
        return explicit
    key = os.environ.get("YOUTUBE_API_KEY")
    if key:
        return key
    # Repo-scoped secret file (Linux remotes): KEY=VALUE lines.
    secret_path = Path("/run/repo_secrets/StreamLens-Analytics/.env.secrets")
    if secret_path.exists():
        for line in secret_path.read_text().splitlines():
            if line.startswith("YOUTUBE_API_KEY="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    return None


def available() -> bool:
    """True if a live fetch could run right now (a key is configured)."""
    return get_api_key() is not None


def _get(endpoint: str, params: Dict[str, str]) -> dict:
    url = f"{API_ROOT}/{endpoint}?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url, timeout=30) as resp:  # noqa: S310 (trusted host)
        return json.loads(resp.read().decode("utf-8"))


def _iso_to_seconds(iso: str) -> int:
    m = _ISO_DURATION.fullmatch(iso or "")
    if not m:
        return 0
    h = int(m.group("h") or 0)
    mi = int(m.group("m") or 0)
    s = int(m.group("s") or 0)
    return h * 3600 + mi * 60 + s


def _seconds_to_string(total: int) -> str:
    mm, ss = divmod(total, 60)
    return f"{mm}:{ss:02d}"


def _chunked(seq: List[str], size: int) -> List[List[str]]:
    return [seq[i:i + size] for i in range(0, len(seq), size)]


def fetch_top_music(
    max_results: int = 100,
    region: str = "US",
    api_key: Optional[str] = None,
) -> pd.DataFrame:
    """Fetch the current top music videos as a DataFrame in the offline schema."""
    key = get_api_key(api_key)
    if not key:
        raise MissingAPIKey(
            "No YOUTUBE_API_KEY configured. Set the env var (or repo secret) to "
            "fetch live data, or use the bundled CSV."
        )

    # 1) Collect candidate video IDs ordered by view count.
    video_ids: List[str] = []
    page_token = ""
    while len(video_ids) < max_results:
        params = {
            "part": "id",
            "type": "video",
            "videoCategoryId": "10",  # Music
            "order": "viewCount",
            "regionCode": region,
            "maxResults": str(min(50, max_results - len(video_ids))),
            "q": "official music video",
            "key": key,
        }
        if page_token:
            params["pageToken"] = page_token
        data = _get("search", params)
        video_ids.extend(
            item["id"]["videoId"] for item in data.get("items", []) if item.get("id", {}).get("videoId")
        )
        page_token = data.get("nextPageToken", "")
        if not page_token:
            break

    video_ids = video_ids[:max_results]
    if not video_ids:
        raise RuntimeError("YouTube returned no videos for this query.")

    # 2) Video details (stats, duration, snippet).
    videos: List[dict] = []
    for chunk in _chunked(video_ids, 50):
        data = _get(
            "videos",
            {
                "part": "snippet,statistics,contentDetails",
                "id": ",".join(chunk),
                "key": key,
            },
        )
        videos.extend(data.get("items", []))

    # 3) Channel subscriber counts.
    channel_ids = sorted({v["snippet"]["channelId"] for v in videos})
    followers: Dict[str, int] = {}
    for chunk in _chunked(channel_ids, 50):
        data = _get(
            "channels",
            {"part": "statistics", "id": ",".join(chunk), "key": key},
        )
        for item in data.get("items", []):
            followers[item["id"]] = int(item["statistics"].get("subscriberCount", 0))

    rows = []
    for v in videos:
        snip = v["snippet"]
        stats = v.get("statistics", {})
        dur = _iso_to_seconds(v.get("contentDetails", {}).get("duration", ""))
        ch_id = snip["channelId"]
        rows.append(
            {
                "title": snip.get("title", ""),
                "fulltitle": snip.get("title", ""),
                "description": snip.get("description", ""),
                "view_count": int(stats.get("viewCount", 0)),
                "categories": "Music",
                "tags": ";".join(snip.get("tags", []) or []),
                "duration": dur,
                "duration_string": _seconds_to_string(dur),
                "live_status": snip.get("liveBroadcastContent", "none") != "none",
                "thumbnail": (snip.get("thumbnails", {}).get("high", {}) or {}).get("url", ""),
                "channel": snip.get("channelTitle", ""),
                "channel_url": f"https://www.youtube.com/channel/{ch_id}",
                "channel_follower_count": followers.get(ch_id, 0),
            }
        )

    df = pd.DataFrame(rows, columns=SCHEMA)
    df = df[df["view_count"] > 0].sort_values("view_count", ascending=False).reset_index(drop=True)
    return df


def refresh_dataset(
    out_path: Optional[Path] = None,
    max_results: int = 100,
    region: str = "US",
    api_key: Optional[str] = None,
) -> Path:
    """Fetch live data and overwrite the CSV the offline pipeline reads."""
    out = Path(out_path) if out_path else DEFAULT_OUT
    df = fetch_top_music(max_results=max_results, region=region, api_key=api_key)
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False)
    return out


def status() -> Dict[str, object]:
    """Lightweight status for the API/UI to report whether live data is wired."""
    return {
        "live_available": available(),
        "source": "youtube_data_api_v3" if available() else "bundled_csv",
        "note": (
            "Live YouTube Data API key detected - refresh enabled."
            if available()
            else "No API key set; serving the committed real dataset."
        ),
    }


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Refresh StreamLens music data from YouTube Data API v3")
    ap.add_argument("--max", type=int, default=100, help="Number of videos to fetch")
    ap.add_argument("--region", default="US", help="ISO region code (default US)")
    ap.add_argument("--out", default=str(DEFAULT_OUT), help="Output CSV path")
    ap.add_argument("--key", default=None, help="API key (else env YOUTUBE_API_KEY)")
    args = ap.parse_args()

    if not get_api_key(args.key):
        print(
            "No YOUTUBE_API_KEY set. Get one at "
            "https://console.cloud.google.com/apis/library/youtube.googleapis.com "
            "then re-run. The app still works on the bundled CSV without it.",
            file=sys.stderr,
        )
        sys.exit(2)

    path = refresh_dataset(out_path=Path(args.out), max_results=args.max, region=args.region, api_key=args.key)
    print(f"Wrote {path}")
