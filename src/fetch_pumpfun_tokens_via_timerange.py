import asyncio
import json
import logging

from solders.signature import Signature
from solders.transaction_status import UiConfirmedBlock

from TMP2 import get_signatures_for_account
from src.settings import settings
from src.providers.api import SolanaAPI, HeliusAPI
from src.utils import get_timestamp_from_datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_first_signature_in_block(block: UiConfirmedBlock) -> Signature:
    return block.transactions[0].transaction.signatures[0]

async def fetch_pumpfun_tokens_via_timerange():
    solana_api = SolanaAPI(settings.RPC_URL)
    helius_api = HeliusAPI(settings.HELIUS_API_KEY)

    async with solana_api:
        start_block = await solana_api.get_blok_by_timestamp(get_timestamp_from_datetime(settings.START_DATETIME))
        end_block = await solana_api.get_blok_by_timestamp(get_timestamp_from_datetime(settings.END_DATETIME))

    signatures = await helius_api.fetch_finalized_signatures_by_account(
        settings.PUMP_FUN_PROGRAM_ID,
        settings.HELIUS_API_KEY,
        before=str(get_first_signature_in_block(end_block.value)),
        until=str(get_first_signature_in_block(start_block.value))
    )
    logger.info(f'{len(signatures)=}')

    created_tx = await helius_api.get_detail_transactions_created_token_pumpfun(signatures)
    for event in created_tx:
        logger.info(json.dumps(event, indent=2))

    logger.info(f'Count of swaps: {len(created_tx)}')


if __name__ == "__main__":
    asyncio.run(fetch_pumpfun_tokens_via_timerange())
