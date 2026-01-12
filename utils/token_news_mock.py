import pandas as pd
from datetime import datetime, timedelta
import random

def get_mock_governance(token: str) -> pd.DataFrame:
    today = datetime.today()

    data = [
        {
            "title": f"{token} Proposal #{i}",
            "type": random.choice(["Parameter Change", "Treasury", "Protocol Upgrade"]),
            "status": random.choice(["Active", "Passed", "Rejected"]),
            "start": today - timedelta(days=random.randint(10, 40)),
            "end": today + timedelta(days=random.randint(3, 14)),
            "impact": random.choice(["High", "Medium", "Low"]),
        }
        for i in range(1, 6)
    ]

    return pd.DataFrame(data)


def get_mock_news(token: str) -> pd.DataFrame:
    today = datetime.today()

    categories = [
        "Partnership",
        "Listing",
        "Product Update",
        "Security",
        "Regulation",
    ]

    data = [
        {
            "date": today - timedelta(days=random.randint(0, 30)),
            "headline": f"{token} announces {random.choice(categories)} update",
            "source": random.choice(["Twitter", "Blog", "CoinDesk", "The Block"]),
            "category": random.choice(categories),
        }
        for _ in range(8)
    ]

    return pd.DataFrame(data)
