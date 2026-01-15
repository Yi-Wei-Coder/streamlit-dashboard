import pandas as pd

def last_and_change(df: pd.DataFrame, days: int = 30) -> tuple[float, float]:
    if df is None or len(df) == 0:
        return 0.0, 0.0
    if len(df) < days + 1:
        v = float(df["value"].iloc[-1])
        return v, 0.0
    v = float(df["value"].iloc[-1])
    prev = float(df["value"].iloc[-(days+1)])
    chg = (v / prev - 1) * 100 if prev != 0 else 0.0
    return v, chg

def ma(df: pd.DataFrame, window: int = 30) -> pd.DataFrame:
    out = df.copy()
    out["ma"] = out["value"].rolling(window).mean()
    return out
