import numpy as np
import pandas as pd

TOKENS_DEFAULT = [
    "AAVE","LDO","SQD","ENA","PENDLE","TON","SKY","HYPE","COMP","SNX","DYDX","PUMP","CANTON","POL","ARC"
]

def _rng(seed: int, salt: str):
    return np.random.default_rng(abs(hash((seed, salt))) % (2**32))

def _date_index(days: int, freq: str = "D"):
    end = pd.Timestamp.today().normalize()
    start = end - pd.Timedelta(days=days)
    return pd.date_range(start=start, end=end, freq=freq)

def _series_trend(seed: int, name: str, days: int, base: float, vol: float, drift: float):
    r = _rng(seed, name)
    idx = _date_index(days, "D")
    noise = r.normal(0, vol, len(idx))
    vals = base * np.exp(np.cumsum(drift + noise))
    return pd.DataFrame({"date": idx, "value": vals})

def _pct_change_30d(series_df: pd.DataFrame) -> float:
    df = series_df.dropna()
    if len(df) < 31:
        return 0.0
    latest = df["value"].iloc[-1]
    prev = df["value"].iloc[-31]
    if prev == 0:
        return 0.0
    return (latest / prev - 1) * 100

def generate_token_dataset(tokens=None, seed: int = 42):
    if tokens is None:
        tokens = TOKENS_DEFAULT

    # store per-token details
    details = {}
    summary_rows = []

    for t in tokens:
        r = _rng(seed, t)

        # Price (daily 1Y)
        price_base = r.uniform(0.2, 300)
        price = _series_trend(seed, f"{t}_price", days=365, base=price_base, vol=0.03, drift=r.uniform(-0.001, 0.003))

        # FDV (daily 1Y) – correlate with price
        fdv_base = r.uniform(200e6, 80e9)
        fdv = _series_trend(seed, f"{t}_fdv", days=365, base=fdv_base, vol=0.02, drift=r.uniform(-0.001, 0.002))

        # 24H Volume (daily 1Y) – spiky
        vol_base = r.uniform(5e6, 3e9)
        volume = _series_trend(seed, f"{t}_vol", days=365, base=vol_base, vol=0.06, drift=r.uniform(-0.002, 0.002))
        # add spikes
        spike_mask = r.random(len(volume)) < 0.08
        volume.loc[spike_mask, "value"] *= r.uniform(1.5, 5.0, spike_mask.sum())

        # Circulating supply (daily 1Y) – slow increase
        circ_base = r.uniform(20e6, 3e9)
        circ = _series_trend(seed, f"{t}_circ", days=365, base=circ_base, vol=0.005, drift=r.uniform(0.0001, 0.001))

        # Burning (daily 1Y) – can be 0 for some tokens
        burn_base = r.uniform(0, 2e6)
        burn = _series_trend(seed, f"{t}_burn", days=365, base=max(1.0, burn_base + 1.0), vol=0.08, drift=r.uniform(-0.003, 0.002))
        if burn_base < 2e5:
            burn["value"] *= 0.0  # show “no burn” behavior for some

        # PnL inputs (mock)
        cost_basis = float(price["value"].iloc[-1] * r.uniform(0.6, 1.4))
        position_qty = float(r.uniform(100, 20000))
        position_value = float(price["value"].iloc[-1] * position_qty)
        cost_value = float(cost_basis * position_qty)
        pnl_abs = position_value - cost_value
        pnl_pct = (pnl_abs / cost_value * 100) if cost_value != 0 else 0.0

        # Unlock schedule (monthly next 12 months)
        today = pd.Timestamp.today().normalize()
        unlock_months = pd.date_range(today + pd.offsets.MonthBegin(1), periods=12, freq="MS")
        # unlock % of circulating (0%~6%)
        unlock_pct = np.clip(r.normal(1.2, 1.0, len(unlock_months)), 0, 6)
        unlock_df = pd.DataFrame({"date": unlock_months, "unlock_pct_of_circ": unlock_pct})

        # Fundamentals (daily 1Y)
        fees = _series_trend(seed, f"{t}_fees", days=365, base=r.uniform(1e4, 2e7), vol=0.07, drift=r.uniform(-0.001, 0.004))
        tvl = _series_trend(seed, f"{t}_tvl", days=365, base=r.uniform(1e7, 3e10), vol=0.04, drift=r.uniform(-0.002, 0.003))
        platform_vol = _series_trend(seed, f"{t}_platvol", days=365, base=r.uniform(1e6, 2e10), vol=0.06, drift=r.uniform(-0.002, 0.004))
        mau = _series_trend(seed, f"{t}_mau", days=365, base=r.uniform(2e4, 2e7), vol=0.03, drift=r.uniform(-0.001, 0.002))
        dau = _series_trend(seed, f"{t}_dau", days=365, base=r.uniform(5e3, 5e6), vol=0.03, drift=r.uniform(-0.001, 0.002))

        # Market share (daily 1Y, 0~1)
        share = _series_trend(seed, f"{t}_share", days=365, base=r.uniform(0.01, 0.35), vol=0.02, drift=r.uniform(-0.001, 0.001))
        share["value"] = np.clip(share["value"], 0, 0.9)

        # Derived metrics / deltas
        price_30d = _pct_change_30d(price)
        fdv_30d = _pct_change_30d(fdv)
        vol_30d = _pct_change_30d(volume)

        # Next unlock > 2% ?
        next_big = unlock_df[unlock_df["unlock_pct_of_circ"] > 2.0].head(1)
        next_unlock_flag = False
        next_unlock_text = "-"
        if len(next_big) > 0:
            d = next_big["date"].iloc[0].date().isoformat()
            p = next_big["unlock_pct_of_circ"].iloc[0]
            next_unlock_flag = True
            next_unlock_text = f"{d} ({p:.1f}%)"

        summary_rows.append({
            "Token": t,
            "Price (30D %)": price_30d,
            "FDV (30D %)": fdv_30d,
            "Volume 24H (30D %)": vol_30d,
            "Next Unlock (>2%)": next_unlock_text,
            "_next_unlock_flag": next_unlock_flag,
        })

        details[t] = {
            "price": price,
            "fdv": fdv,
            "volume": volume,
            "circ": circ,
            "burn": burn,
            "unlock": unlock_df,
            "fund_fees": fees,
            "fund_tvl": tvl,
            "fund_platform_vol": platform_vol,
            "fund_mau": mau,
            "fund_dau": dau,
            "fund_share": share,
            "position": {
                "qty": position_qty,
                "cost_basis": cost_basis,
                "cost_value": cost_value,
                "value": position_value,
                "pnl_abs": pnl_abs,
                "pnl_pct": pnl_pct,
            }
        }

    summary = pd.DataFrame(summary_rows)

    # sort: put tokens with big unlock soon on top, then by volume change abs
    summary = summary.sort_values(
        by=["_next_unlock_flag", "Volume 24H (30D %)"],
        ascending=[False, False]
    ).reset_index(drop=True)

    return summary, details

def ma_30(series_df: pd.DataFrame) -> pd.DataFrame:
    df = series_df.copy()
    df["ma30"] = df["value"].rolling(30).mean()
    return df
