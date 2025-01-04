import asyncio
import json
import logging
from src.settings import settings
from src.api import SolanaAPI, HeliusAPI
from src.fetcher import TransactionFetcher
from src.parser import TransactionParser
from src.utils import chunked_iterable

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    solana_api = SolanaAPI(settings.RPC_URL)
    helius_api = HeliusAPI(settings.API_KEY)

    fetcher = TransactionFetcher(solana_api, settings.TARGET_MINT)
    parser = TransactionParser(helius_api, settings.TX_SOURCE, settings.TX_TYPE)

    signatures = await fetcher.fetch_transactions()

    parsed_transactions = await parser.parse_transactions(chunked_iterable(signatures))
    swap_events = parser.convert_to_swap_events(parsed_transactions)

    for event in swap_events:
        logger.info(json.dumps(event.__dict__, indent=2))

    await solana_api.close()

if __name__ == "__main__":
    asyncio.run(main())
