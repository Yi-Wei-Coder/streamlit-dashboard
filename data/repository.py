from core.config import TOKENS_DEFAULT
from data.providers.mock import MockProvider
from data.cache import cached

@cached(ttl=600)
def _get_token_summary_cached(provider_name: str, seed: int = 42):
    provider = MockProvider()
    return provider.token_summary_table(TOKENS_DEFAULT, seed=seed)

@cached(ttl=600)
def _get_token_detail_cached(provider_name: str, token: str, seed: int = 42):
    provider = MockProvider()
    return provider.token_detail(token, seed=seed)

class Repository:
    def __init__(self, provider=None):
        self.provider = provider or MockProvider()

    def get_token_summary(self, seed: int = 42):
        return _get_token_summary_cached(self.provider.name, seed)

    def get_token_detail(self, token: str, seed: int = 42):
        return _get_token_detail_cached(self.provider.name, token, seed)

repo = Repository()
