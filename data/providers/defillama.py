import time
import requests
import pandas as pd

from data.providers.base import BaseProvider
from data.cache import cached
from core.defillama_map import DEFILLAMA_SLUG

BASE_URL = "https://api.llama.fi"

@cached(ttl=21600)
def _llama_get(path: str):
    s = requests.Session()
    url = f"{BASE_URL}{path}"
    r = s.get(url, timeout=20)
    r.raise_for_status()
    return r.json()

def _normalize_llama_tvl(payload: dict) -> pd.DataFrame | None:
    tvl = payload.get("tvl")
    if not isinstance(tvl, list) or len(tvl) == 0:
        return None
    df = pd.DataFrame(tvl)
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], unit="s", errors="coerce").dt.tz_localize(None)
    if "totalLiquidityUSD" in df.columns:
        df = df.rename(columns={"totalLiquidityUSD": "value"})
    elif "tvl" in df.columns:
        df = df.rename(columns={"tvl": "value"})
    if "date" in df.columns and "value" in df.columns:
        return df[["date", "value"]].dropna().sort_values("date").reset_index(drop=True)
    return None

def _normalize_llama_chart(payload: dict) -> pd.DataFrame | None:
    chart = payload.get("totalDataChart") or payload.get("data") or payload.get("chart")
    if not isinstance(chart, list) or len(chart) == 0:
        return None
    if isinstance(chart[0], (list, tuple)) and len(chart[0]) >= 2:
        df = pd.DataFrame(chart, columns=["date", "value"])
        df["date"] = pd.to_datetime(df["date"], unit="s", errors="coerce").dt.tz_localize(None)
        return df.dropna().sort_values("date").reset_index(drop=True)
    return None

class DefiLlamaProvider(BaseProvider):
    name = "defillama"

    def _slug(self, token: str):
        return DEFILLAMA_SLUG.get(token)

    def token_summary_table(self, tokens: list[str], seed: int = 42) -> pd.DataFrame:
        return pd.DataFrame({"Token": tokens})

    def token_detail(self, token: str, seed: int = 42) -> dict:
        slug = self._slug(token)
        if not slug:
            return {}

        out = {}
        try:
            p = _llama_get(f"/protocol/{slug}")
            tvl_df = _normalize_llama_tvl(p if isinstance(p, dict) else {})
            if tvl_df is not None and len(tvl_df) > 0:
                out["tvl"] = tvl_df
        except Exception:
            pass

        try:
            fees = _llama_get(f"/summary/fees/{slug}")
            df = _normalize_llama_chart(fees if isinstance(fees, dict) else {})
            if df is not None and len(df) > 0:
                out["fees"] = df
        except Exception:
            pass

        try:
            rev = _llama_get(f"/summary/revenue/{slug}")
            df = _normalize_llama_chart(rev if isinstance(rev, dict) else {})
            if df is not None and len(df) > 0:
                out["revenue"] = df
        except Exception:
            pass

        return out
