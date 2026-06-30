from __future__ import annotations

from typing import Any, Dict

import pandas as pd


def safe_row_count(df: pd.DataFrame | None) -> int:
    if df is None:
        return 0
    try:
        return int(len(df))
    except Exception:
        return 0


def dataframe_overview(df: pd.DataFrame) -> Dict[str, Any]:
    return {
        "rows": int(len(df)),
        "columns": int(len(df.columns)),
        "column_names": list(map(str, df.columns)),
    }
