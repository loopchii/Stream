# Stream Runtime Surface

- Generated at: `2026-06-30T19:22:15+00:00`
- Sample size: `5000`
- Synthetic rows: `5000`
- Public music songs: `100`

## Hero Signals

- **Representation parity**: `0.744` — Share balance in the active representation surface.
- **Representation breadth**: `71.3%` — Synthetic lane diversity index, computed in Python and exported for the UI.
- **Attention concentration**: `46.5%` — Top-3 channel control share in the public music lane.
- **Notation-linked coverage**: `0.0%` — Share of catalog songs with directly linked score or notation support.

## Runtime Notes

- The browser surface now has a generated backend state payload.
- SQLite persistence can store the latest runtime snapshot for inspection.
- Synthetic and public music lanes stay distinct all the way through export.
