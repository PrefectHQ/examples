# /// script
# dependencies ["prefect"]
# ///

"""
This example shows how to bind specific parameters to a schedule.

We check the price of BTC and ETH at an interval of 10 seconds, and the price of SOL and
DOGE according to a cron schedule.
"""

from datetime import timedelta
from typing import Any

import httpx
from prefect import flow, task
from prefect.schedules import Cron, Interval


@task
def fetch_crypto_price(crypto_id: str) -> dict[str, Any]:
    """Fetch current price for a cryptocurrency."""
    with httpx.Client() as client:
        response = client.get(
            "https://api.coingecko.com/api/v3/simple/price",
            params={"ids": crypto_id, "vs_currencies": "usd"},
        )
        return response.json()


@flow(log_prints=True, flow_run_name="check prices: {currencies_to_check}")
def get_crypto_prices(currencies_to_check: list[str]):
    """Display current prices for provided cryptocurrencies."""

    for price in fetch_crypto_price.map(currencies_to_check).result():
        _id = list(price.keys())[0]
        print(f"{_id}: ${price[_id]['usd']:,.2f}")


if __name__ == "__main__":
    get_crypto_prices.serve(
        schedules=[
            Interval(
                timedelta(seconds=10),
                timezone="America/New_York",
                parameters={"currencies_to_check": ["bitcoin", "ethereum"]},
            ),
            Cron(
                "42 0 6 9 *",
                timezone="America/New_York",
                parameters={"currencies_to_check": ["solana", "dogecoin"]},
            ),
        ]
    )
