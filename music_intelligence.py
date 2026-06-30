#!/usr/bin/env python3
"""
Stream music intelligence harvest.

Builds a score-aware index that keeps two layers distinct:

1. The public song catalog already used by the music virality module.
2. Any local score / notation / MIDI / chord artifacts that can support
   deeper note-level analysis.

The pipeline stays honest about what exists. If the repo has no linked score
material, the package reports that clearly instead of inventing note-level
claims.
"""

from __future__ import annotations

import argparse
import json
import re
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
import zipfile
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

import pandas as pd

import music_pipeline

BASE_DIR = Path(__file__).resolve().parent
DEFAULT_ROOT = BASE_DIR
DEFAULT_JSON = BASE_DIR / "music_index.json"
DEFAULT_CSV = BASE_DIR / "music_index.csv"
DEFAULT_REPORT = BASE_DIR / "music_analysis_report.md"

USER_AGENT = "LoopchiiStreamMusicIntelligence/1.0 (https://github.com/loopchii/Stream)"
SKIP_DIRS = {
    ".git",
    ".github",
    ".venv",
    "venv",
    "node_modules",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    "dist",
    "build",
}
MUSIC_DIR_HINTS = {"scores", "sheets", "music", "midi", "tabs", "notation"}
TEXT_SCAN_EXTS = {".txt", ".md"}
SUPPORTED_EXTENSIONS = {
    ".pdf": "pdf",
    ".musicxml": "musicxml",
    ".mxl": "musicxml",
    ".mscx": "musescore_xml",
    ".mscz": "musescore",
    ".ly": "lilypond",
    ".abc": "abc",
    ".mid": "midi",
    ".midi": "midi",
    ".kar": "midi",
    ".sib": "sibelius",
    ".gp": "guitar_pro",
    ".gp3": "guitar_pro",
    ".gp4": "guitar_pro",
    ".gp5": "guitar_pro",
}
PITCH_CLASSES = ["C", "C#", "D", "Eb", "E", "F", "F#", "G", "Ab", "A", "Bb", "B"]
FIFTHS_TO_MAJOR = {
    -7: "Cb Major",
    -6: "Gb Major",
    -5: "Db Major",
    -4: "Ab Major",
    -3: "Eb Major",
    -2: "Bb Major",
    -1: "F Major",
    0: "C Major",
    1: "G Major",
    2: "D Major",
    3: "A Major",
    4: "E Major",
    5: "B Major",
    6: "F# Major",
    7: "C# Major",
}
FIFTHS_TO_MINOR = {
    -7: "Ab Minor",
    -6: "Eb Minor",
    -5: "Bb Minor",
    -4: "F Minor",
    -3: "C Minor",
    -2: "G Minor",
    -1: "D Minor",
    0: "A Minor",
    1: "E Minor",
    2: "B Minor",
    3: "F# Minor",
    4: "C# Minor",
    5: "G# Minor",
    6: "D# Minor",
    7: "A# Minor",
}

CHORD_TOKEN_RE = re.compile(
    r"\b([A-G](?:#|b)?(?:maj7|maj9|maj|min7|min9|m7|m9|m|sus2|sus4|dim|aug|add9|7|9|11|13)?(?:/[A-G](?:#|b)?)?)\b"
)
TAB_LINE_RE = re.compile(r"^[eBGDAE]\|[-0-9hpbrx~/\\\s]+$", re.M)
SECTION_RE = re.compile(r"\b(intro|verse|chorus|bridge|pre-chorus|hook|outro|refrain|solo)\b", re.I)
NOTE_RE_ABC = re.compile(r"([=_^]*[A-Ga-g][,']*)")
NOTE_RE_LILYPOND = re.compile(r"(?<!\\)\b([a-g](?:is|es|isis|eses)?[,']*)\d*\b")
INSTRUMENT_RE_LILYPOND = re.compile(r'instrumentName\s*=\s*"([^"]+)"')
TEMPO_RE_LILYPOND = re.compile(r"\\tempo(?:\s+\d+)?\s*=?\s*(\d+)")
TIME_RE_LILYPOND = re.compile(r"\\time\s+(\d+/\d+)")
KEY_RE_LILYPOND = re.compile(r"\\key\s+([a-g](?:is|es)?)\s+\\(major|minor)")


@dataclass
class DiscoveredAsset:
    path: Path
    relpath: str
    format: str
    category: str
    matched_by: str


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def path_allowed(path: Path) -> bool:
    return not any(part in SKIP_DIRS for part in path.parts)


def safe_read_text(path: Path, max_chars: int = 120000) -> str:
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""
    return text[:max_chars]


def coerce_float(value: object, default: float = 0.0) -> float:
    try:
        if pd.isna(value):
            return default
    except Exception:
        pass
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def coerce_int(value: object, default: int = 0) -> int:
    try:
        if pd.isna(value):
            return default
    except Exception:
        pass
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def title_variants(title: str, artist: Optional[str] = None) -> List[str]:
    variants = set()
    raw = title or ""
    candidates = [raw]
    if " - " in raw:
        left, right = raw.split(" - ", 1)
        candidates.extend([left, right])
    if " – " in raw:
        left, right = raw.split(" – ", 1)
        candidates.extend([left, right])
    if artist:
        artist_l = artist.lower().strip()
        for candidate in list(candidates):
            if candidate.lower().startswith(artist_l + " - "):
                candidates.append(candidate[len(artist) + 3 :])
            if candidate.lower().startswith(artist_l + " – "):
                candidates.append(candidate[len(artist) + 3 :])
    for candidate in candidates:
        clean = re.sub(r"\([^)]*\)|\[[^\]]*\]", "", candidate)
        clean = re.sub(r"\b(feat|ft)\.?\b.*$", "", clean, flags=re.I)
        clean = re.sub(r"\bofficial\b|\bvideo\b|\baudio\b|\blyric\b", "", clean, flags=re.I)
        clean = re.sub(r"[^a-z0-9]+", " ", clean.lower()).strip()
        if clean:
            variants.add(clean)
    return sorted(variants)


def infer_title(path: Path, text: str = "") -> str:
    if text:
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            if line.startswith("#"):
                return line.lstrip("#").strip()
            if len(line) < 120:
                return line
    return path.stem.replace("_", " ").replace("-", " ").strip()


def note_name_from_abc(token: str) -> Optional[str]:
    token = token.strip()
    if not token:
        return None
    accidental = ""
    while token and token[0] in "^_=":
        accidental += token[0]
        token = token[1:]
    if not token or token[0].upper() not in "ABCDEFG":
        return None
    base = token[0].upper()
    if accidental.startswith("^"):
        return base + "#"
    if accidental.startswith("_"):
        flats = {"A": "Ab", "B": "Bb", "D": "Db", "E": "Eb", "G": "Gb", "C": "Cb", "F": "Fb"}
        return flats.get(base, base + "b")
    return base


def note_name_from_lily(token: str) -> Optional[str]:
    token = token.strip().lower()
    if not token:
        return None
    m = re.match(r"([a-g])(is|es|isis|eses)?", token)
    if not m:
        return None
    base = m.group(1).upper()
    accidental = m.group(2) or ""
    if accidental.startswith("is"):
        return base + "#"
    if accidental.startswith("es"):
        flats = {"A": "Ab", "B": "Bb", "D": "Db", "E": "Eb", "G": "Gb", "C": "Cb", "F": "Fb"}
        return flats.get(base, base + "b")
    return base


def note_name_from_midi(value: int) -> str:
    return PITCH_CLASSES[int(value) % 12]


def key_name_from_fifths(fifths: Optional[int], mode: Optional[str]) -> Optional[str]:
    if fifths is None:
        return None
    if (mode or "").lower().startswith("min"):
        return FIFTHS_TO_MINOR.get(fifths, f"{fifths} fifths minor")
    return FIFTHS_TO_MAJOR.get(fifths, f"{fifths} fifths major")


def summarize_counter(counter: Counter, limit: int = 10, total: Optional[int] = None) -> List[Dict[str, object]]:
    total = total if total is not None else sum(counter.values())
    if total <= 0:
        return []
    return [
        {"item": item, "count": int(count), "share": round(count / total, 4)}
        for item, count in counter.most_common(limit)
    ]


def summarize_pairs(sequence: Sequence[str], limit: int = 10) -> List[Dict[str, object]]:
    if len(sequence) < 2:
        return []
    pairs = Counter(f"{left} → {right}" for left, right in zip(sequence, sequence[1:]))
    total = sum(pairs.values())
    return summarize_counter(pairs, limit=limit, total=total)


def parse_chord_lines(text: str) -> List[str]:
    chords: List[str] = []
    for line in text.splitlines():
        tokens = CHORD_TOKEN_RE.findall(line)
        if len(tokens) >= 3:
            chords.extend(tokens)
    return chords


def detect_text_music_format(path: Path, text: str) -> Optional[str]:
    if not text:
        return None
    if path.suffix.lower() == ".abc" or re.search(r"^T:|^K:|^M:", text, flags=re.M):
        return "abc"
    if path.suffix.lower() == ".ly" or "\\relative" in text or "\\score" in text:
        return "lilypond"
    if TAB_LINE_RE.search(text):
        return "tablature"
    if len(parse_chord_lines(text)) >= 3:
        return "chord_chart"
    return None


def discover_music_assets(root: Path) -> List[DiscoveredAsset]:
    assets: List[DiscoveredAsset] = []
    for path in root.rglob("*"):
        if not path.is_file() or not path_allowed(path):
            continue
        ext = path.suffix.lower()
        relpath = str(path.relative_to(root))
        if ext in SUPPORTED_EXTENSIONS:
            fmt = SUPPORTED_EXTENSIONS[ext]
            category = "notation" if fmt in {"musicxml", "abc", "lilypond", "musescore_xml"} else "performance"
            assets.append(DiscoveredAsset(path=path, relpath=relpath, format=fmt, category=category, matched_by="extension"))
            continue
        if ext in TEXT_SCAN_EXTS and path.stat().st_size <= 512000:
            text = safe_read_text(path, max_chars=50000)
            fmt = detect_text_music_format(path, text)
            if fmt:
                category = "notation" if fmt in {"abc", "lilypond"} else "text_notation"
                assets.append(DiscoveredAsset(path=path, relpath=relpath, format=fmt, category=category, matched_by="text_scan"))
                continue
        if ext in TEXT_SCAN_EXTS and any(part.lower() in MUSIC_DIR_HINTS for part in path.parts):
            text = safe_read_text(path, max_chars=40000)
            fmt = detect_text_music_format(path, text)
            if fmt:
                category = "notation" if fmt in {"abc", "lilypond"} else "text_notation"
                assets.append(DiscoveredAsset(path=path, relpath=relpath, format=fmt, category=category, matched_by="directory_hint"))
    return sorted(assets, key=lambda item: item.relpath.lower())


def parse_musicxml_bytes(blob: bytes, relpath: str) -> Dict[str, object]:
    root = ET.fromstring(blob)

    def local(tag: str) -> str:
        return tag.rsplit("}", 1)[-1]

    def first_child_text(element: ET.Element, name: str) -> Optional[str]:
        for child in element:
            if local(child.tag) == name and child.text:
                return child.text.strip()
        return None

    def first_nested_child(element: ET.Element, name: str) -> Optional[ET.Element]:
        for child in element:
            if local(child.tag) == name:
                return child
        return None

    title = None
    composer = None
    key = None
    time_signature = None
    tempo = None
    instruments: List[str] = []
    sections: List[str] = []
    dynamics: List[str] = []
    articulations: List[str] = []
    notes: List[str] = []

    for element in root.iter():
        tag = local(element.tag)
        if tag == "movement-title" and element.text and not title:
            title = element.text.strip()
        elif tag == "work-title" and element.text and not title:
            title = element.text.strip()
        elif tag == "creator" and element.text and not composer:
            composer = element.text.strip()
        elif tag == "part-name" and element.text:
            instruments.append(element.text.strip())
        elif tag == "time" and time_signature is None:
            beats = first_child_text(element, "beats")
            beat_type = first_child_text(element, "beat-type")
            if beats and beat_type:
                time_signature = f"{beats}/{beat_type}"
        elif tag == "key" and key is None:
            fifths_text = first_child_text(element, "fifths")
            mode = first_child_text(element, "mode") or "major"
            fifths = int(fifths_text) if fifths_text else None
            key = key_name_from_fifths(fifths, mode)
        elif tag == "sound" and tempo is None and element.attrib.get("tempo"):
            try:
                tempo = int(round(float(element.attrib["tempo"])))
            except ValueError:
                pass
        elif tag == "per-minute" and tempo is None and element.text:
            try:
                tempo = int(round(float(element.text.strip())))
            except ValueError:
                pass
        elif tag == "words" and element.text:
            text = element.text.strip()
            for match in SECTION_RE.findall(text):
                sections.append(match.lower())
        elif tag in {"p", "pp", "ppp", "mp", "mf", "f", "ff", "fff", "sfz"}:
            dynamics.append(tag)
        elif tag in {"staccato", "tenuto", "accent", "strong-accent", "legato"}:
            articulations.append(tag)
        elif tag == "note":
            if any(local(child.tag) == "rest" for child in element):
                continue
            pitch_el = first_nested_child(element, "pitch")
            if pitch_el is None:
                continue
            step = first_child_text(pitch_el, "step")
            alter = first_child_text(pitch_el, "alter")
            if not step:
                continue
            name = step.upper()
            if alter:
                if alter == "1":
                    name += "#"
                elif alter == "-1":
                    flats = {"A": "Ab", "B": "Bb", "D": "Db", "E": "Eb", "G": "Gb", "C": "Cb", "F": "Fb"}
                    name = flats.get(name, name + "b")
            notes.append(name)

    return {
        "title": title or Path(relpath).stem.replace("_", " ").replace("-", " "),
        "composer": composer,
        "key": key,
        "time_signature": time_signature,
        "tempo": tempo,
        "instrumentation": sorted({item for item in instruments if item}),
        "structure": {"sections": sorted(set(sections), key=sections.index) if sections else []},
        "performance_notes": {
            "dynamics": sorted(set(dynamics), key=dynamics.index) if dynamics else [],
            "articulation": sorted(set(articulations), key=articulations.index) if articulations else [],
            "pedaling": False,
        },
        "_note_sequence": notes,
        "_chord_sequence": [],
    }


def parse_musicxml_asset(path: Path) -> Dict[str, object]:
    if path.suffix.lower() == ".mxl":
        with zipfile.ZipFile(path) as archive:
            xml_name = next((name for name in archive.namelist() if name.endswith(".xml")), "")
            if not xml_name:
                return {}
            return parse_musicxml_bytes(archive.read(xml_name), path.name)
    return parse_musicxml_bytes(path.read_bytes(), path.name)


def parse_abc_asset(path: Path) -> Dict[str, object]:
    text = safe_read_text(path)
    headers: Dict[str, List[str]] = defaultdict(list)
    body_lines: List[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        if re.match(r"^[A-Za-z]:", stripped):
            headers[stripped[0]].append(stripped[2:].strip())
        else:
            body_lines.append(stripped)
    body = "\n".join(body_lines)
    notes = [note_name_from_abc(token) for token in NOTE_RE_ABC.findall(body)]
    note_seq = [item for item in notes if item]
    chords = re.findall(r'"([^"]+)"', body)
    sections = []
    for line in body_lines:
        sections.extend(match.lower() for match in SECTION_RE.findall(line))
    tempo = None
    tempo_header = next(iter(headers.get("Q", [])), "")
    m = re.search(r"(\d+)", tempo_header)
    if m:
        tempo = int(m.group(1))
    return {
        "title": next(iter(headers.get("T", [])), infer_title(path, text)),
        "composer": next(iter(headers.get("C", [])), None),
        "key": next(iter(headers.get("K", [])), None),
        "time_signature": next(iter(headers.get("M", [])), None),
        "tempo": tempo,
        "instrumentation": [],
        "structure": {"sections": sorted(set(sections), key=sections.index) if sections else []},
        "performance_notes": {"dynamics": [], "articulation": [], "pedaling": False},
        "_note_sequence": note_seq,
        "_chord_sequence": chords,
    }


def parse_lilypond_asset(path: Path) -> Dict[str, object]:
    text = safe_read_text(path)
    notes = [note_name_from_lily(token) for token in NOTE_RE_LILYPOND.findall(text)]
    note_seq = [item for item in notes if item]
    chords = parse_chord_lines(text)
    sections = [match.lower() for match in SECTION_RE.findall(text)]
    tempo = None
    tm = TEMPO_RE_LILYPOND.search(text)
    if tm:
        tempo = int(tm.group(1))
    key_match = KEY_RE_LILYPOND.search(text)
    key = None
    if key_match:
        key_root = note_name_from_lily(key_match.group(1)) or key_match.group(1).upper()
        key = f"{key_root} {'Minor' if key_match.group(2) == 'minor' else 'Major'}"
    time_match = TIME_RE_LILYPOND.search(text)
    dynamics = re.findall(r"\\(ppp|pp|mp|mf|ff|fff|sfz)\b", text)
    articulation = re.findall(r"\\(staccato|tenuto|accent|marcato|legato)\b", text)
    return {
        "title": infer_title(path, text),
        "composer": None,
        "key": key,
        "time_signature": time_match.group(1) if time_match else None,
        "tempo": tempo,
        "instrumentation": INSTRUMENT_RE_LILYPOND.findall(text),
        "structure": {"sections": sorted(set(sections), key=sections.index) if sections else []},
        "performance_notes": {
            "dynamics": sorted(set(dynamics), key=dynamics.index) if dynamics else [],
            "articulation": sorted(set(articulation), key=articulation.index) if articulation else [],
            "pedaling": "\\sustainOn" in text or "\\sustainOff" in text,
        },
        "_note_sequence": note_seq,
        "_chord_sequence": chords,
    }


def read_vlq(data: bytes, pos: int) -> Tuple[int, int]:
    value = 0
    while pos < len(data):
        byte = data[pos]
        pos += 1
        value = (value << 7) | (byte & 0x7F)
        if not (byte & 0x80):
            break
    return value, pos


def parse_midi_asset(path: Path) -> Dict[str, object]:
    data = path.read_bytes()
    if not data.startswith(b"MThd") or len(data) < 14:
        return {"title": infer_title(path), "_note_sequence": [], "_chord_sequence": []}
    pos = 8
    header_len = int.from_bytes(data[4:8], "big")
    format_type = int.from_bytes(data[pos : pos + 2], "big")
    track_count = int.from_bytes(data[pos + 2 : pos + 4], "big")
    division = int.from_bytes(data[pos + 4 : pos + 6], "big")
    pos = 8 + header_len
    tempo = None
    time_signature = None
    key = None
    title = infer_title(path)
    instruments: List[str] = []
    notes: List[str] = []
    for _ in range(track_count):
        if data[pos : pos + 4] != b"MTrk":
            break
        length = int.from_bytes(data[pos + 4 : pos + 8], "big")
        track = data[pos + 8 : pos + 8 + length]
        pos += 8 + length
        tpos = 0
        running_status = None
        while tpos < len(track):
            _, tpos = read_vlq(track, tpos)
            if tpos >= len(track):
                break
            status = track[tpos]
            if status < 0x80:
                if running_status is None:
                    break
                status = running_status
            else:
                tpos += 1
                running_status = status
            if status == 0xFF:
                if tpos >= len(track):
                    break
                meta_type = track[tpos]
                tpos += 1
                length, tpos = read_vlq(track, tpos)
                payload = track[tpos : tpos + length]
                tpos += length
                if meta_type == 0x51 and len(payload) == 3 and tempo is None:
                    mpqn = int.from_bytes(payload, "big")
                    if mpqn:
                        tempo = int(round(60000000 / mpqn))
                elif meta_type == 0x58 and len(payload) >= 2 and time_signature is None:
                    numerator = payload[0]
                    denominator = 2 ** payload[1]
                    time_signature = f"{numerator}/{denominator}"
                elif meta_type == 0x59 and len(payload) >= 2 and key is None:
                    sf = int.from_bytes(payload[:1], "big", signed=True)
                    mode = "minor" if payload[1] else "major"
                    key = key_name_from_fifths(sf, mode)
                elif meta_type in {0x03, 0x04} and payload:
                    text = payload.decode("latin1", errors="ignore").strip()
                    if meta_type == 0x03 and title == infer_title(path):
                        title = text or title
                    elif meta_type == 0x04:
                        instruments.append(text)
                continue
            if status in {0xF0, 0xF7}:
                length, tpos = read_vlq(track, tpos)
                tpos += length
                continue
            event_type = status & 0xF0
            if event_type in {0x80, 0x90, 0xA0, 0xB0, 0xE0}:
                if tpos + 2 > len(track):
                    break
                data1, data2 = track[tpos], track[tpos + 1]
                tpos += 2
                if event_type == 0x90 and data2 > 0:
                    notes.append(note_name_from_midi(data1))
            elif event_type in {0xC0, 0xD0}:
                tpos += 1
            else:
                break
    return {
        "title": title,
        "composer": None,
        "key": key,
        "time_signature": time_signature,
        "tempo": tempo,
        "instrumentation": sorted({item for item in instruments if item}),
        "structure": {"sections": []},
        "performance_notes": {"dynamics": [], "articulation": [], "pedaling": False},
        "midi": {"format_type": format_type, "division": division},
        "_note_sequence": notes,
        "_chord_sequence": [],
    }


def parse_text_notation_asset(path: Path) -> Dict[str, object]:
    text = safe_read_text(path)
    sections = [match.lower() for match in SECTION_RE.findall(text)]
    chords = parse_chord_lines(text)
    performance = {
        "dynamics": [word.lower() for word in re.findall(r"\b(crescendo|diminuendo|forte|piano|mezzo-forte|mezzo-piano)\b", text, flags=re.I)],
        "articulation": [word.lower() for word in re.findall(r"\b(legato|staccato|tenuto|accent)\b", text, flags=re.I)],
        "pedaling": bool(re.search(r"\bpedal\b", text, flags=re.I)),
    }
    return {
        "title": infer_title(path, text),
        "composer": None,
        "key": None,
        "time_signature": None,
        "tempo": None,
        "instrumentation": ["guitar"] if TAB_LINE_RE.search(text) else [],
        "structure": {"sections": sorted(set(sections), key=sections.index) if sections else []},
        "performance_notes": performance,
        "_note_sequence": [],
        "_chord_sequence": chords,
    }


def parse_asset(asset: DiscoveredAsset) -> Dict[str, object]:
    try:
        if asset.format == "musicxml":
            parsed = parse_musicxml_asset(asset.path)
        elif asset.format == "abc":
            parsed = parse_abc_asset(asset.path)
        elif asset.format == "lilypond":
            parsed = parse_lilypond_asset(asset.path)
        elif asset.format == "midi":
            parsed = parse_midi_asset(asset.path)
        else:
            parsed = parse_text_notation_asset(asset.path)
    except Exception:
        parsed = {
            "title": infer_title(asset.path),
            "composer": None,
            "key": None,
            "time_signature": None,
            "tempo": None,
            "instrumentation": [],
            "structure": {"sections": []},
            "performance_notes": {"dynamics": [], "articulation": [], "pedaling": False},
            "_note_sequence": [],
            "_chord_sequence": [],
        }
    note_seq = [item for item in parsed.pop("_note_sequence", []) if item]
    chord_seq = [item for item in parsed.pop("_chord_sequence", []) if item]
    note_counts = Counter(note_seq)
    chord_counts = Counter(chord_seq)
    parsed["note_profile"] = {
        "note_events": int(len(note_seq)),
        "top_notes": summarize_counter(note_counts, limit=8, total=len(note_seq)),
        "top_note_combinations": summarize_pairs(note_seq, limit=8),
    }
    parsed["harmony_profile"] = {
        "chord_events": int(len(chord_seq)),
        "top_chords": summarize_counter(chord_counts, limit=8, total=len(chord_seq)),
        "top_chord_transitions": summarize_pairs(chord_seq, limit=8),
    }
    parsed["source_files"] = [
        {"path": asset.relpath, "format": asset.format, "category": asset.category, "matched_by": asset.matched_by}
    ]
    parsed["_internal_note_sequence"] = note_seq
    parsed["_internal_chord_sequence"] = chord_seq
    return parsed


def build_reference_queries(title: str, artist: Optional[str]) -> List[Dict[str, str]]:
    query = urllib.parse.quote_plus(" ".join(part for part in [title, artist] if part))
    return [
        {"source": "MusicBrainz", "kind": "search_url", "url": f"https://musicbrainz.org/search?query={query}&type=recording&method=indexed"},
        {"source": "Wikipedia", "kind": "search_url", "url": f"https://en.wikipedia.org/w/index.php?search={query}"},
        {"source": "IMSLP", "kind": "search_url", "url": f"https://imslp.org/index.php?search={query}"},
        {"source": "MuseScore", "kind": "search_url", "url": f"https://musescore.com/sheetmusic?text={query}"},
        {"source": "Ultimate Guitar", "kind": "search_url", "url": f"https://www.ultimate-guitar.com/search.php?search_type=title&value={query}"},
        {"source": "AllMusic", "kind": "search_url", "url": f"https://www.allmusic.com/search/all/{query}"},
    ]


def http_get_json(url: str) -> dict:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=20) as response:  # noqa: S310
        return json.loads(response.read().decode("utf-8"))


def enrich_with_musicbrainz(title: str, artist: Optional[str]) -> Optional[Dict[str, object]]:
    pieces = [f'recording:"{title}"']
    if artist:
        pieces.append(f'artist:"{artist}"')
    query = urllib.parse.quote_plus(" AND ".join(pieces))
    url = f"https://musicbrainz.org/ws/2/recording/?query={query}&fmt=json&limit=1"
    data = http_get_json(url)
    recordings = data.get("recordings") or []
    if not recordings:
        return None
    match = recordings[0]
    return {
        "source": "MusicBrainz",
        "kind": "resolved",
        "id": match.get("id"),
        "title": match.get("title"),
        "artist": ", ".join(item.get("name", "") for item in match.get("artist-credit", []) if item.get("name")),
        "first_release_date": match.get("first-release-date"),
        "score": match.get("score"),
        "url": f"https://musicbrainz.org/recording/{match.get('id')}" if match.get("id") else None,
    }


def enrich_with_wikipedia(title: str, artist: Optional[str]) -> Optional[Dict[str, object]]:
    query = " ".join(part for part in [title, artist] if part)
    search_url = (
        "https://en.wikipedia.org/w/api.php?action=opensearch"
        f"&search={urllib.parse.quote_plus(query)}&limit=1&namespace=0&format=json"
    )
    search = http_get_json(search_url)
    titles = search[1] if len(search) > 1 else []
    urls = search[3] if len(search) > 3 else []
    if not titles:
        return None
    page_title = titles[0]
    page_url = urls[0] if urls else None
    extract_url = (
        "https://en.wikipedia.org/w/api.php?action=query&prop=extracts&exintro=1&explaintext=1"
        f"&titles={urllib.parse.quote_plus(page_title)}&format=json"
    )
    summary = http_get_json(extract_url)
    pages = ((summary.get("query") or {}).get("pages") or {})
    page = next(iter(pages.values()), {})
    return {
        "source": "Wikipedia",
        "kind": "resolved",
        "title": page_title,
        "url": page_url,
        "summary": (page.get("extract") or "")[:280],
    }


def maybe_live_enrich(title: str, artist: Optional[str], enable_live: bool, last_call: List[float]) -> List[Dict[str, object]]:
    refs: List[Dict[str, object]] = []
    if not enable_live:
        return refs
    now = time.time()
    wait = 1.05 - (now - last_call[0])
    if wait > 0:
        time.sleep(wait)
    mb = enrich_with_musicbrainz(title, artist)
    last_call[0] = time.time()
    if mb:
        refs.append(mb)
    try:
        wiki = enrich_with_wikipedia(title, artist)
    except Exception:
        wiki = None
    if wiki:
        refs.append(wiki)
    return refs


def default_catalog_rows() -> List[Dict[str, object]]:
    df = music_pipeline.load_enriched_dataset().copy()
    keep = [
        "title",
        "channel",
        "view_count",
        "duration_min",
        "channel_follower_count",
        "virality_coefficient",
        "tag_count",
        "is_official",
        "source",
        "published_year",
        "detected_language",
        "country",
        "engagement_ratio",
    ]
    for column in keep:
        if column not in df.columns:
            df[column] = None
    return df[keep].to_dict("records")


def merge_asset_bundle(assets: List[Dict[str, object]]) -> Dict[str, object]:
    if not assets:
        return {
            "key": None,
            "time_signature": None,
            "tempo": None,
            "instrumentation": [],
            "structure": {"sections": []},
            "performance_notes": {"dynamics": [], "articulation": [], "pedaling": False},
            "note_profile": {"note_events": 0, "top_notes": [], "top_note_combinations": []},
            "harmony_profile": {"chord_events": 0, "top_chords": [], "top_chord_transitions": []},
            "source_files": [],
            "_internal_note_sequence": [],
            "_internal_chord_sequence": [],
        }
    note_seq: List[str] = []
    chord_seq: List[str] = []
    keys = Counter()
    times = Counter()
    tempos: List[int] = []
    instruments: List[str] = []
    sections: List[str] = []
    dynamics: List[str] = []
    articulation: List[str] = []
    source_files: List[Dict[str, object]] = []
    pedal = False
    for asset in assets:
        if asset.get("key"):
            keys[str(asset["key"])] += 1
        if asset.get("time_signature"):
            times[str(asset["time_signature"])] += 1
        if asset.get("tempo"):
            tempos.append(int(asset["tempo"]))
        instruments.extend(asset.get("instrumentation") or [])
        sections.extend((asset.get("structure") or {}).get("sections") or [])
        perf = asset.get("performance_notes") or {}
        dynamics.extend(perf.get("dynamics") or [])
        articulation.extend(perf.get("articulation") or [])
        pedal = pedal or bool(perf.get("pedaling"))
        source_files.extend(asset.get("source_files") or [])
        note_seq.extend(asset.get("_internal_note_sequence") or [])
        chord_seq.extend(asset.get("_internal_chord_sequence") or [])
    note_counts = Counter(note_seq)
    chord_counts = Counter(chord_seq)
    return {
        "key": keys.most_common(1)[0][0] if keys else None,
        "time_signature": times.most_common(1)[0][0] if times else None,
        "tempo": int(round(sum(tempos) / len(tempos))) if tempos else None,
        "instrumentation": sorted(set(filter(None, instruments))),
        "structure": {"sections": sorted(set(sections), key=sections.index) if sections else []},
        "performance_notes": {
            "dynamics": sorted(set(dynamics), key=dynamics.index) if dynamics else [],
            "articulation": sorted(set(articulation), key=articulation.index) if articulation else [],
            "pedaling": pedal,
        },
        "note_profile": {
            "note_events": len(note_seq),
            "top_notes": summarize_counter(note_counts, limit=8, total=len(note_seq)),
            "top_note_combinations": summarize_pairs(note_seq, limit=8),
        },
        "harmony_profile": {
            "chord_events": len(chord_seq),
            "top_chords": summarize_counter(chord_counts, limit=8, total=len(chord_seq)),
            "top_chord_transitions": summarize_pairs(chord_seq, limit=8),
        },
        "source_files": source_files,
        "_internal_note_sequence": note_seq,
        "_internal_chord_sequence": chord_seq,
    }


def base_piece_id(title: str, artist: Optional[str]) -> str:
    artist_part = (artist or "unknown").strip().lower()
    artist_part = re.sub(r"[^a-z0-9]+", "-", artist_part).strip("-")
    title_part = re.sub(r"[^a-z0-9]+", "-", (title or "untitled").strip().lower()).strip("-")
    return f"{title_part or 'untitled'}::{artist_part or 'unknown'}"


def build_music_data_package(
    repo_root: Path | str = DEFAULT_ROOT,
    catalog_rows: Optional[List[Dict[str, object]]] = None,
    enable_live_enrichment: bool = False,
) -> Dict[str, object]:
    root = Path(repo_root)
    assets = discover_music_assets(root)
    parsed_assets = [parse_asset(asset) for asset in assets]

    asset_lookup: Dict[str, List[Dict[str, object]]] = defaultdict(list)
    asset_variants: Dict[int, List[str]] = {}
    for index, parsed in enumerate(parsed_assets):
        source_path = ((parsed.get("source_files") or [{}])[0]).get("path", "")
        variants = title_variants(str(parsed.get("title") or ""), None)
        asset_variants[index] = variants
        for variant in variants:
            asset_lookup[variant].append(parsed)
        if not parsed.get("title") and source_path:
            for variant in title_variants(Path(source_path).stem, None):
                asset_lookup[variant].append(parsed)

    rows = catalog_rows if catalog_rows is not None else default_catalog_rows()
    pieces: List[Dict[str, object]] = []
    matched_asset_ids = set()
    live_clock = [0.0]

    for row in rows:
        title = str(row.get("title") or "").strip()
        artist = str(row.get("channel") or "").strip() or None
        variants = title_variants(title, artist)
        matched_assets: List[Dict[str, object]] = []
        for variant in variants:
            for parsed in asset_lookup.get(variant, []):
                if parsed not in matched_assets:
                    matched_assets.append(parsed)
        for idx, variants_for_asset in asset_variants.items():
            if idx in matched_asset_ids:
                continue
            if set(variants) & set(variants_for_asset):
                matched_asset_ids.add(idx)
        bundle = merge_asset_bundle(matched_assets)
        references = build_reference_queries(title, artist)
        references.extend(maybe_live_enrich(title, artist, enable_live_enrichment, live_clock))
        pieces.append(
            {
                "id": base_piece_id(title, artist),
                "title": title,
                "composer": None,
                "artist": artist,
                "key": bundle["key"],
                "time_signature": bundle["time_signature"],
                "tempo": bundle["tempo"],
                "instrumentation": bundle["instrumentation"],
                "difficulty": None,
                "genre": None,
                "structure": bundle["structure"],
                "performance_notes": bundle["performance_notes"],
                "note_profile": bundle["note_profile"],
                "harmony_profile": bundle["harmony_profile"],
                "notation_summary": {
                    "matched_file_count": len(bundle["source_files"]),
                    "has_notes": bool(bundle["note_profile"]["note_events"]),
                    "has_chords": bool(bundle["harmony_profile"]["chord_events"]),
                },
                "source_files": bundle["source_files"],
                "external_references": references,
                "catalog_metrics": {
                    "view_count": coerce_float(row.get("view_count")),
                    "duration_min": coerce_float(row.get("duration_min")),
                    "channel_follower_count": coerce_float(row.get("channel_follower_count")),
                    "virality_coefficient": coerce_float(row.get("virality_coefficient")),
                    "tag_count": coerce_int(row.get("tag_count")),
                    "is_official": coerce_int(row.get("is_official")),
                    "source": row.get("source"),
                    "published_year": coerce_int(row.get("published_year")),
                    "detected_language": row.get("detected_language"),
                    "country": row.get("country"),
                    "engagement_ratio": coerce_float(row.get("engagement_ratio")),
                },
                "_internal_note_sequence": bundle["_internal_note_sequence"],
                "_internal_chord_sequence": bundle["_internal_chord_sequence"],
            }
        )

    for idx, parsed in enumerate(parsed_assets):
        if idx in matched_asset_ids:
            continue
        title = str(parsed.get("title") or "")
        references = build_reference_queries(title, parsed.get("composer"))
        pieces.append(
            {
                "id": f"local::{base_piece_id(title, parsed.get('composer'))}",
                "title": title,
                "composer": parsed.get("composer"),
                "artist": None,
                "key": parsed.get("key"),
                "time_signature": parsed.get("time_signature"),
                "tempo": parsed.get("tempo"),
                "instrumentation": parsed.get("instrumentation") or [],
                "difficulty": None,
                "genre": None,
                "structure": parsed.get("structure") or {"sections": []},
                "performance_notes": parsed.get("performance_notes") or {"dynamics": [], "articulation": [], "pedaling": False},
                "note_profile": parsed.get("note_profile") or {"note_events": 0, "top_notes": [], "top_note_combinations": []},
                "harmony_profile": parsed.get("harmony_profile") or {"chord_events": 0, "top_chords": [], "top_chord_transitions": []},
                "notation_summary": {
                    "matched_file_count": len(parsed.get("source_files") or []),
                    "has_notes": bool((parsed.get("note_profile") or {}).get("note_events")),
                    "has_chords": bool((parsed.get("harmony_profile") or {}).get("chord_events")),
                },
                "source_files": parsed.get("source_files") or [],
                "external_references": references,
                "catalog_metrics": {},
                "_internal_note_sequence": parsed.get("_internal_note_sequence") or [],
                "_internal_chord_sequence": parsed.get("_internal_chord_sequence") or [],
            }
        )

    note_seq = [note for piece in pieces for note in piece.get("_internal_note_sequence", [])]
    chord_seq = [chord for piece in pieces for chord in piece.get("_internal_chord_sequence", [])]
    note_counter = Counter(note_seq)
    chord_counter = Counter(chord_seq)
    key_counter = Counter(piece["key"] for piece in pieces if piece.get("key"))
    time_counter = Counter(piece["time_signature"] for piece in pieces if piece.get("time_signature"))
    instrument_counter = Counter(
        instrument for piece in pieces for instrument in (piece.get("instrumentation") or []) if instrument
    )
    dynamics_counter = Counter(
        dynamic
        for piece in pieces
        for dynamic in ((piece.get("performance_notes") or {}).get("dynamics") or [])
    )
    articulation_counter = Counter(
        articulation
        for piece in pieces
        for articulation in ((piece.get("performance_notes") or {}).get("articulation") or [])
    )
    tempos = [int(piece["tempo"]) for piece in pieces if piece.get("tempo")]
    matched_catalog = sum(1 for piece in pieces if piece["id"][:7] != "local::" and piece["notation_summary"]["matched_file_count"] > 0)
    score_linked = [piece for piece in pieces if piece["notation_summary"]["matched_file_count"] > 0]
    priority_queue = sorted(
        [piece for piece in pieces if piece["id"][:7] != "local::" and piece["notation_summary"]["matched_file_count"] == 0],
        key=lambda piece: piece.get("catalog_metrics", {}).get("view_count", 0),
        reverse=True,
    )[:12]
    format_counts = Counter(
        source["format"] for piece in pieces for source in piece.get("source_files", [])
    )

    summary = {
        "generated_at": utc_now_iso(),
        "repo_root": str(root),
        "catalog_song_count": int(len(rows)),
        "discovered_music_files": int(len(assets)),
        "matched_catalog_songs": int(matched_catalog),
        "local_only_pieces": int(sum(1 for piece in pieces if piece["id"].startswith("local::"))),
        "notation_link_rate": round((matched_catalog / len(rows)) if rows else 0.0, 4),
        "pieces_with_notes": int(sum(1 for piece in pieces if piece["note_profile"]["note_events"] > 0)),
        "pieces_with_chords": int(sum(1 for piece in pieces if piece["harmony_profile"]["chord_events"] > 0)),
        "parsed_note_events": int(len(note_seq)),
        "parsed_chord_events": int(len(chord_seq)),
        "formats": [
            {"format": fmt, "count": int(count)}
            for fmt, count in sorted(format_counts.items(), key=lambda item: (-item[1], item[0]))
        ],
        "top_notes": summarize_counter(note_counter, limit=10, total=len(note_seq)),
        "top_note_combinations": summarize_pairs(note_seq, limit=10),
        "top_chords": summarize_counter(chord_counter, limit=10, total=len(chord_seq)),
        "top_chord_transitions": summarize_pairs(chord_seq, limit=10),
        "key_distribution": summarize_counter(key_counter, limit=10),
        "time_signature_distribution": summarize_counter(time_counter, limit=10),
        "instrumentation": summarize_counter(instrument_counter, limit=10),
        "performance_surface": {
            "dynamics": summarize_counter(dynamics_counter, limit=8),
            "articulation": summarize_counter(articulation_counter, limit=8),
            "pedaled_pieces": int(
                sum(1 for piece in pieces if (piece.get("performance_notes") or {}).get("pedaling"))
            ),
        },
        "tempo_summary": {
            "count": len(tempos),
            "median_bpm": int(pd.Series(tempos).median()) if tempos else None,
            "min_bpm": min(tempos) if tempos else None,
            "max_bpm": max(tempos) if tempos else None,
        },
        "priority_queue": [
            {
                "title": piece["title"],
                "artist": piece.get("artist"),
                "views": piece.get("catalog_metrics", {}).get("view_count", 0),
                "source": piece.get("catalog_metrics", {}).get("source"),
            }
            for piece in priority_queue
        ],
        "supported_formats": sorted(set(SUPPORTED_EXTENSIONS.values()) | {"chord_chart", "tablature"}),
        "invitation": (
            "The score-aware lane is live. If you add MusicXML, MIDI, ABC, LilyPond, tabs, or clean chord charts, "
            "the package will compare them against the public song catalog on the next run."
        ),
        "honesty_note": (
            "Note and chord claims appear only where the repository actually contains notation-bearing files. "
            "The public video catalog remains separate from the score layer on purpose."
        ),
        "live_enrichment_enabled": bool(enable_live_enrichment),
    }

    for piece in pieces:
        piece.pop("_internal_note_sequence", None)
        piece.pop("_internal_chord_sequence", None)

    return {
        "generated_at": summary["generated_at"],
        "summary": summary,
        "assets": [asset.__dict__ | {"path": str(asset.path)} for asset in assets],
        "pieces": pieces,
    }


def write_package(package: Dict[str, object], json_path: Path, csv_path: Path, report_path: Path) -> None:
    json_path.write_text(json.dumps(package, indent=2), encoding="utf-8")
    rows = []
    for piece in package["pieces"]:
        rows.append(
            {
                "id": piece["id"],
                "title": piece["title"],
                "composer": piece.get("composer"),
                "artist": piece.get("artist"),
                "key": piece.get("key"),
                "time_signature": piece.get("time_signature"),
                "tempo": piece.get("tempo"),
                "instrumentation": "; ".join(piece.get("instrumentation") or []),
                "sections": "; ".join((piece.get("structure") or {}).get("sections") or []),
                "dynamics": "; ".join(((piece.get("performance_notes") or {}).get("dynamics") or [])),
                "articulation": "; ".join(((piece.get("performance_notes") or {}).get("articulation") or [])),
                "pedaling": bool((piece.get("performance_notes") or {}).get("pedaling")),
                "matched_file_count": int((piece.get("notation_summary") or {}).get("matched_file_count") or 0),
                "note_events": int((piece.get("note_profile") or {}).get("note_events") or 0),
                "chord_events": int((piece.get("harmony_profile") or {}).get("chord_events") or 0),
                "view_count": piece.get("catalog_metrics", {}).get("view_count"),
                "duration_min": piece.get("catalog_metrics", {}).get("duration_min"),
                "channel_follower_count": piece.get("catalog_metrics", {}).get("channel_follower_count"),
                "virality_coefficient": piece.get("catalog_metrics", {}).get("virality_coefficient"),
                "source": piece.get("catalog_metrics", {}).get("source"),
                "published_year": piece.get("catalog_metrics", {}).get("published_year"),
                "detected_language": piece.get("catalog_metrics", {}).get("detected_language"),
                "country": piece.get("catalog_metrics", {}).get("country"),
                "source_paths": "; ".join(source["path"] for source in piece.get("source_files") or []),
                "reference_count": len(piece.get("external_references") or []),
            }
        )
    pd.DataFrame(rows).to_csv(csv_path, index=False)
    summary = package["summary"]
    report = [
        "# Music Analysis Report",
        "",
        f"- Generated: `{package['generated_at']}`",
        f"- Catalog songs: **{summary['catalog_song_count']}**",
        f"- Local music files discovered: **{summary['discovered_music_files']}**",
        f"- Catalog songs linked to notation: **{summary['matched_catalog_songs']}**",
        f"- Parsed note events: **{summary['parsed_note_events']}**",
        f"- Parsed chord events: **{summary['parsed_chord_events']}**",
        "",
        "## What This Surface Can Honestly Say",
        "",
        summary["honesty_note"],
        "",
        "## Coverage",
        "",
        f"- Notation link rate: **{summary['notation_link_rate'] * 100:.1f}%**",
        f"- Pieces with note sequences: **{summary['pieces_with_notes']}**",
        f"- Pieces with chord sequences: **{summary['pieces_with_chords']}**",
        "",
        "## Most Common Notes",
        "",
    ]
    top_notes = summary["top_notes"] or []
    if top_notes:
        for row in top_notes:
            report.append(f"- `{row['item']}` · {row['count']} events · {row['share'] * 100:.1f}%")
    else:
        report.append("- No note-bearing notation files are currently linked inside this repository.")
    report.extend(["", "## Most Common Note Combinations", ""])
    combos = summary["top_note_combinations"] or []
    if combos:
        for row in combos:
            report.append(f"- `{row['item']}` · {row['count']} transitions")
    else:
        report.append("- No note transition corpus is available yet.")
    report.extend(["", "## Most Common Chords", ""])
    chords = summary["top_chords"] or []
    if chords:
        for row in chords:
            report.append(f"- `{row['item']}` · {row['count']} hits · {row['share'] * 100:.1f}%")
    else:
        report.append("- No chord-chart or chord-bearing notation files are currently linked.")
    report.extend(["", "## Priority Queue", ""])
    for row in summary["priority_queue"][:8]:
        report.append(
            f"- **{row['title']}**"
            + (f" — {row['artist']}" if row.get("artist") else "")
            + f" · {int(row.get('views') or 0):,} views"
        )
    report.extend(
        [
            "",
            "## Collaboration Cue",
            "",
            summary["invitation"],
            "",
        ]
    )
    report_path.write_text("\n".join(report), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the Stream music intelligence package.")
    parser.add_argument("--root", default=str(DEFAULT_ROOT), help="Repository root to scan")
    parser.add_argument("--json-out", default=str(DEFAULT_JSON), help="JSON export path")
    parser.add_argument("--csv-out", default=str(DEFAULT_CSV), help="CSV export path")
    parser.add_argument("--report-out", default=str(DEFAULT_REPORT), help="Markdown report path")
    parser.add_argument("--live-enrich", action="store_true", help="Resolve MusicBrainz and Wikipedia metadata live")
    args = parser.parse_args()

    package = build_music_data_package(
        repo_root=Path(args.root),
        enable_live_enrichment=args.live_enrich,
    )
    write_package(package, Path(args.json_out), Path(args.csv_out), Path(args.report_out))
    print(f"Wrote {args.json_out}")
    print(f"Wrote {args.csv_out}")
    print(f"Wrote {args.report_out}")


if __name__ == "__main__":
    main()
