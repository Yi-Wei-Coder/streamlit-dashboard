import pandas as pd

from data.providers.base import BaseProvider
from data.providers.mock import MockProvider
from data.providers.coingecko import CoinGeckoProvider
from data.providers.defillama import DefiLlamaProvider

class HybridProvider(BaseProvider):
    name = "hybrid"

    def __init__(self):
        self.mock = MockProvider()
        self.cg = CoinGeckoProvider()
        self.llama = DefiLlamaProvider()

    def token_summary_table(self, tokens: list[str], seed: int = 42):
        base = self.mock.token_summary_table(tokens, seed=seed)
        cg = self.cg.token_summary_table(tokens, seed=seed)

        cg_map = cg.set_index("Token").to_dict(orient="index")
        overlay_cols = [
            "Price", "Price (30D %)",
            "FDV", "FDV (30D %)",
            "Volume 24H", "Volume 24H (30D %)",
        ]

        for col in overlay_cols:
            if col not in base.columns:
                base[col] = float("nan")
            base[col] = base["Token"].map(lambda t: cg_map.get(t, {}).get(col)).fillna(base[col])

        if "Next Unlock (>2%)" not in base.columns:
            base["Next Unlock (>2%)"] = "-"
        if "_next_unlock_flag" not in base.columns:
            base["_next_unlock_flag"] = False

        return base

    def token_detail(self, token: str, seed: int = 42):
        d = self.mock.token_detail(token, seed=seed)

        cg = self.cg.token_detail(token, seed=seed)
        for k in ["price", "volume", "market_cap"]:
            if k in cg and isinstance(cg[k], pd.DataFrame) and len(cg[k]) > 0:
                d[k] = cg[k]

        ll = self.llama.token_detail(token, seed=seed)
        for k in ["tvl", "fees", "revenue"]:
            if k in ll and isinstance(ll[k], pd.DataFrame) and len(ll[k]) > 0:
                d[k] = ll[k]

        return d
