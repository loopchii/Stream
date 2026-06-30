from pathlib import Path

from fastapi.testclient import TestClient

from app import app
from music_intelligence import build_music_data_package, discover_music_assets


MUSICXML_SAMPLE = """<?xml version="1.0" encoding="UTF-8"?>
<score-partwise version="3.1">
  <work><work-title>Moon Bloom</work-title></work>
  <identification><creator type="composer">A. Rivera</creator></identification>
  <part-list>
    <score-part id="P1"><part-name>Piano</part-name></score-part>
  </part-list>
  <part id="P1">
    <measure number="1">
      <attributes>
        <divisions>1</divisions>
        <key><fifths>0</fifths><mode>major</mode></key>
        <time><beats>4</beats><beat-type>4</beat-type></time>
      </attributes>
      <direction placement="above">
        <direction-type><metronome><per-minute>120</per-minute></metronome></direction-type>
        <sound tempo="120"/>
      </direction>
      <direction>
        <direction-type><words>Verse</words></direction-type>
      </direction>
      <direction>
        <direction-type><dynamics><mf/></dynamics></direction-type>
      </direction>
      <note><pitch><step>C</step><octave>4</octave></pitch><duration>1</duration></note>
      <note><pitch><step>E</step><octave>4</octave></pitch><duration>1</duration></note>
      <note><pitch><step>G</step><octave>4</octave></pitch><duration>1</duration></note>
    </measure>
  </part>
</score-partwise>
"""


ABC_SAMPLE = """T:Moon Bloom
C:A. Rivera
M:3/4
Q:1/4=96
K:Dm
"Am"A2 c | "G"BA G |
"""


def test_discover_music_assets_detects_supported_formats(tmp_path: Path):
    (tmp_path / "scores").mkdir()
    (tmp_path / "scores" / "moon_bloom.musicxml").write_text(MUSICXML_SAMPLE, encoding="utf-8")
    (tmp_path / "notation").mkdir()
    (tmp_path / "notation" / "moon_bloom.abc").write_text(ABC_SAMPLE, encoding="utf-8")

    assets = discover_music_assets(tmp_path)

    formats = {asset.format for asset in assets}
    assert "musicxml" in formats
    assert "abc" in formats


def test_build_music_data_package_links_catalog_rows_to_notation(tmp_path: Path):
    (tmp_path / "scores").mkdir()
    (tmp_path / "scores" / "moon_bloom.musicxml").write_text(MUSICXML_SAMPLE, encoding="utf-8")
    catalog = [
        {
            "title": "Moon Bloom",
            "channel": "Luna Vale",
            "view_count": 4567890,
            "duration_min": 3.5,
            "channel_follower_count": 1200000,
            "virality_coefficient": 3.8,
            "tag_count": 12,
            "is_official": 1,
            "source": "primary_top100",
            "published_year": 2025,
            "detected_language": "English",
            "country": "US",
            "engagement_ratio": 0.04,
        }
    ]

    package = build_music_data_package(repo_root=tmp_path, catalog_rows=catalog, enable_live_enrichment=False)

    assert package["summary"]["catalog_song_count"] == 1
    assert package["summary"]["discovered_music_files"] == 1
    assert package["summary"]["matched_catalog_songs"] == 1
    assert package["summary"]["parsed_note_events"] == 3
    piece = package["pieces"][0]
    assert piece["title"] == "Moon Bloom"
    assert piece["key"] == "C Major"
    assert piece["time_signature"] == "4/4"
    assert piece["tempo"] == 120
    assert piece["notation_summary"]["matched_file_count"] == 1
    assert piece["note_profile"]["note_events"] == 3


def test_music_intelligence_api_surface():
    client = TestClient(app)

    res = client.get("/api/music/intelligence")
    assert res.status_code == 200
    body = res.json()
    assert "catalog_song_count" in body
    assert "discovered_music_files" in body
    assert "honesty_note" in body

    rows = client.get("/api/music/index", params={"limit": 5})
    assert rows.status_code == 200
    table = rows.json()
    assert table["limit"] == 5
    assert table["count"] <= 5
    assert "items" in table
