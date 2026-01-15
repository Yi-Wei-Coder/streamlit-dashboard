import numpy as np
import pandas as pd

def _date_index(years: int, freq: str) -> pd.DatetimeIndex:
    end = pd.Timestamp.today().normalize()
    start = end - pd.Timedelta(days=int(years * 365.25))
    return pd.date_range(start=start, end=end, freq=freq)

def make_series(
    name: str,
    years: int,
    freq: str,
    kind: str = "level",   # "level" | "volume" | "ratio" | "index"
    seed: int = 42,
) -> pd.DataFrame:
    rng = np.random.default_rng(abs(hash((name, seed))) % (2**32))
    idx = _date_index(years, freq)

    n = len(idx)
    noise = rng.normal(0, 1, n)

    if kind == "level":
        drift = rng.uniform(0.002, 0.01)
        values = 100 * np.exp(np.cumsum(drift + 0.02 * noise))
    elif kind == "volume":
        base = 50 + 5 * np.cumsum(rng.normal(0, 0.2, n))
        spikes = rng.exponential(scale=20, size=n) * (rng.random(n) < 0.12)
        values = np.maximum(1, base + spikes + 5 * noise)
    elif kind == "ratio":
        center = rng.uniform(1.2, 2.2)
        values = center + 0.4 * np.sin(np.linspace(0, 10, n)) + 0.15 * noise
        values = np.clip(values, 0.6, 4.5)
    elif kind == "index":
        values = 50 + 20 * np.sin(np.linspace(0, 18, n)) + 10 * noise
        values = np.clip(values, 0, 100)
    else:
        values = np.cumsum(noise)

    return pd.DataFrame({"date": idx, "value": values})
