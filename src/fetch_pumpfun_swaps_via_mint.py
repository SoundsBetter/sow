import asyncio
import json
import logging

from src.settings import settings
from src.providers.api import SolanaAPI, HeliusAPI
from src.providers.parser import TransactionParser

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def fetch_pumpfun_swaps_via_mint():
    solana_api = SolanaAPI(settings.RPC_URL)
    helius_api = HeliusAPI(settings.HELIUS_API_KEY)
    parser = TransactionParser(settings.TARGET_MINT)

    async with solana_api:
        signatures = await solana_api.fetch_finalized_signatures_by_account(settings.TARGET_MINT)

    detail_transactions = await helius_api.get_detail_transactions_for_mint(signatures, settings.TARGET_MINT)
    swap_events = parser.convert_to_swap_events(detail_transactions)

    for event in swap_events:
        logger.info(json.dumps(event.__dict__, indent=2))
    logger.info(f'Count of swaps: {len(swap_events)}')


if __name__ == "__main__":
    asyncio.run(fetch_pumpfun_swaps_via_mint())
