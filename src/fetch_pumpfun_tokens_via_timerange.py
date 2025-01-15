import asyncio
import json
import logging
from datetime import datetime

from src.providers.parser import TransactionParser
from src.settings import settings
from src.providers.api import SolanaAPI, HeliusAPI
from src.utils import get_timestamp_from_datetime, write_data_to_json_file, get_first_signature_in_block

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def fetch_pumpfun_tokens_via_timerange():
    start = datetime.now()
    solana_api = SolanaAPI(settings.RPC_URL)
    helius_api = HeliusAPI(settings.HELIUS_API_KEY)
    parser = TransactionParser()

    async with solana_api:
        start_block = await solana_api.get_blok_by_timestamp(get_timestamp_from_datetime(settings.START_DATETIME))
        end_block = await solana_api.get_blok_by_timestamp(get_timestamp_from_datetime(settings.END_DATETIME))
        logger.info(f'Start block: {start_block.value.blockhash}, End block: {end_block.value.blockhash}')

    async with helius_api:
        signatures = await helius_api.fetch_finalized_signatures_by_account(
            settings.PUMP_FUN_PROGRAM_ID,
            before=await get_first_signature_in_block(end_block.value),
            until=await get_first_signature_in_block(start_block.value)
        )
        logger.info(f'Find {len(signatures)} signatures')
        created_txs = await helius_api.get_detail_transactions_created_token_pumpfun(signatures)

    minted_tokens = await parser.convert_to_minted_token(created_txs)
    await write_data_to_json_file([token.__dict__ for token in minted_tokens], 'created_tx.json')

    for token in minted_tokens:
        logger.info(json.dumps(token.__dict__, indent=2))
    finish = datetime.now()
    logger.info(f'Count of swaps: {len(minted_tokens)}')
    logger.info(f'Time: {finish - start}')

if __name__ == "__main__":
    asyncio.run(fetch_pumpfun_tokens_via_timerange())
