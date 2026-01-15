from abc import ABC, abstractmethod
import pandas as pd
from core.schemas import Series

class BaseProvider(ABC):
    name: str = "base"

    @abstractmethod
    def token_summary_table(self, tokens: list[str], seed: int = 42) -> pd.DataFrame:
        raise NotImplementedError

    @abstractmethod
    def token_detail(self, token: str, seed: int = 42) -> dict:
        raise NotImplementedError
