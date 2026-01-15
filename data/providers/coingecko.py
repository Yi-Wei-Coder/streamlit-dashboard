import requests
import pandas as pd

from data.providers.base import BaseProvider
from data.cache import cached
from core.coingecko_map import COINGECKO_ID

BASE_URL = "https://api.coingecko.com/api/v3"

def _arr_to_df(arr):
    df = pd.DataFrame(arr, columns=["ts", "value"])
    df["date"] = pd.to_datetime(df["ts"], unit="ms").dt.tz_localize(None)
    return df[["date", "value"]].sort_values("date").reset_index(drop=True)

def _pct_change_over_days(df: pd.DataFrame, days: int = 30) -> float:
    if df is None or len(df) < 2:
        return float("nan")
    df = df.dropna().sort_values("date").reset_index(drop=True)
    last_date = df["date"].iloc[-1]
    target = last_date - pd.Timedelta(days=days)
    before = df[df["date"] <= target]
    if len(before) == 0:
        return float("nan")
    prev = float(before["value"].iloc[-1])
    last = float(df["value"].iloc[-1])
    if prev == 0:
        return float("nan")
    return (last / prev - 1) * 100.0

@cached(ttl=3600)
def _cg_markets_cached(vs_currency: str, ids_csv: str):
    s = requests.Session()
    url = f"{BASE_URL}/coins/markets"
    params = {
        "vs_currency": vs_currency,
        "ids": ids_csv,
        "per_page": 250,
        "page": 1,
        "sparkline": "false",
        "price_change_percentage": "30d",
    }
    r = s.get(url, params=params, timeout=20)
    r.raise_for_status()
    return r.json()

@cached(ttl=21600)
def _cg_market_chart_cached(vs_currency: str, coin_id: str, days: int):
    s = requests.Session()
    url = f"{BASE_URL}/coins/{coin_id}/market_chart"
    params = {"vs_currency": vs_currency, "days": days, "interval": "daily"}
    r = s.get(url, params=params, timeout=20)
    if r.status_code >= 400:
        params = {"vs_currency": vs_currency, "days": days}
        r = s.get(url, params=params, timeout=20)
    r.raise_for_status()
    return r.json()

class CoinGeckoProvider(BaseProvider):
    name = "coingecko"

    def __init__(self, vs_currency: str = "usd"):
        self.vs_currency = vs_currency

    def _id(self, token: str):
        return COINGECKO_ID.get(token)

    def token_summary_table(self, tokens: list[str], seed: int = 42) -> pd.DataFrame:
        ids = [self._id(t) for t in tokens if self._id(t)]
        ids_csv = ",".join(sorted(set(ids))) if ids else ""
        by_id = {}
        if ids_csv:
            markets = _cg_markets_cached(self.vs_currency, ids_csv)
            by_id = {m.get("id"): m for m in markets}

        rows = []
        for t in tokens:
            cid = self._id(t)
            m = by_id.get(cid) if cid else None

            price = m.get("current_price") if m else None
            fdv = m.get("fully_diluted_valuation") if m else None
            vol24 = m.get("total_volume") if m else None
            price_30d = m.get("price_change_percentage_30d_in_currency") if m else None

            fdv_30d = float("nan")
            vol_30d = float("nan")

            if cid:
                try:
                    js = _cg_market_chart_cached(self.vs_currency, cid, 31)
                    if isinstance(js, dict) and "total_volumes" in js:
                        vol_df = _arr_to_df(js["total_volumes"])
                        vol_30d = _pct_change_over_days(vol_df, 30)
                    if isinstance(js, dict) and "market_caps" in js:
                        mc_df = _arr_to_df(js["market_caps"])
                        fdv_30d = _pct_change_over_days(mc_df, 30)
                except Exception:
                    pass

            rows.append({
                "Token": t,
                "Price": price,
                "Price (30D %)": float(price_30d) if price_30d is not None else float("nan"),
                "FDV": fdv,
                "FDV (30D %)": fdv_30d,                 # proxy via market cap 30D%
                "Volume 24H": vol24,
                "Volume 24H (30D %)": vol_30d,
                "Source": "coingecko" if m else "n/a",
            })

        return pd.DataFrame(rows)

    def token_detail(self, token: str, seed: int = 42) -> dict:
        cid = self._id(token)
        if not cid:
            return {}
        js = _cg_market_chart_cached(self.vs_currency, cid, 1095)  # 3Y
        out = {}
        try:
            if "prices" in js:
                out["price"] = _arr_to_df(js["prices"])
            if "market_caps" in js:
                out["market_cap"] = _arr_to_df(js["market_caps"])
            if "total_volumes" in js:
                out["volume"] = _arr_to_df(js["total_volumes"])
        except Exception:
            pass
        return out
