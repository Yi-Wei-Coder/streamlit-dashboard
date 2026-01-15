from data.providers.base import BaseProvider
from core.schemas import Series
from utils.tokens_mock import generate_token_dataset

class MockProvider(BaseProvider):
    name = "mock"

    def token_summary_table(self, tokens: list[str], seed: int = 42):
        summary, _ = generate_token_dataset(tokens=tokens, seed=seed)
        return summary

    def token_detail(self, token: str, seed: int = 42):
        _, details = generate_token_dataset(tokens=[token], seed=seed)
        return details[token]
