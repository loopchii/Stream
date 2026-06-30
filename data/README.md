# Data README

This folder contains the published artifacts that power the public Stream surfaces.

The repository uses more than one data posture. That distinction matters.

## Directory guide

| Path | What it holds | Posture |
|---|---|---|
| `data/n1000`, `data/n5000`, `data/n10000`, `data/n25000` | Synthetic representation exports | Fully reproducible synthetic data generated inside the repo |
| `data/music` | Derived music analysis exports used by the real-data music lane | Built from committed public-source CSVs and documented transforms |
| `data/system` | Runtime, governance, contract, and self-audit artifacts | Derived repository metadata and analysis surfaces |
| `data_sources` | Input CSVs for the public music lane | Public-source or contributor-supplied inputs that require provenance discipline |

## Current public music inputs

The music lane currently draws from these committed source files:

| File | Current role in the repo | Source posture |
|---|---|---|
| `data_sources/youtube-top-100-songs-2025.csv` | Primary top-100 cohort for the music lane | Public video metadata; may be refreshed through the YouTube Data API path in `music_ingest.py` |
| `data_sources/most-viewed-yt-videos-2026.csv` | Supplemental context for broader attention comparisons | Public metadata derivative committed to the repo |
| `data_sources/youtube-music-data.csv` | Supplemental music context | Public metadata derivative committed to the repo |
| `data_sources/youtube-top-channels-2026.csv` | Channel-level context | Public metadata derivative committed to the repo |

## Reference-link sources

Some repository surfaces generate search links or enrichment hints to public sources such as:

- MusicBrainz
- Wikipedia
- IMSLP
- MuseScore
- Ultimate Guitar
- AllMusic

Those references do not mean the repository mirrors or republishes those full datasets. They are public pointers that help contributors continue the work responsibly.

## Attribution rules

If you add or update a data source, document:

1. where it came from
2. whether the repo stores the raw data or a transformed derivative
3. what license or reuse terms apply, if known
4. which analysis surface depends on it

If you cannot document those four things, the dataset is not ready for merge.

## What should not be committed here

Do not commit:

- private exports
- personal data dumps
- credentials
- proprietary datasets without permission
- scraped content whose reuse posture is unclear

## Why this folder is documented this way

The goal is simple: anyone using or reviewing Stream should be able to tell which data is synthetic, which data is public, which data is derived, and which claims depend on each lane.
