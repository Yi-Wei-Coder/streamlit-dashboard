from dataclasses import dataclass
from typing import Optional, Literal
import pandas as pd

Frequency = Literal["D", "W"]

@dataclass
class Series:
    """Generic time series with a fixed schema."""
    df: pd.DataFrame  # columns: date, value
    freq: Frequency
    unit: Optional[str] = None
    source: Optional[str] = None

@dataclass
class Snapshot:
    """Single metric point with change info."""
    value: float
    change_30d_pct: float = 0.0
    unit: Optional[str] = None
    source: Optional[str] = None
