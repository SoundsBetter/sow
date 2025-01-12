import asyncio
import logging

from solders.signature import Signature
from solders.transaction_status import UiConfirmedBlock

from src.settings import settings
from src.providers.api import SolanaAPI
from src.utils import get_timestamp_from_datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_first_signature_in_block(block: UiConfirmedBlock) -> Signature:
    return block.transactions[0].transaction.signatures[0]

async def fetch_pumpfun_tokens_via_timerange():
    solana_api = SolanaAPI(settings.RPC_URL)
    async with solana_api:
        start_block = await solana_api.get_blok_by_timestamp(get_timestamp_from_datetime(settings.START_DATETIME))
        end_block = await solana_api.get_blok_by_timestamp(get_timestamp_from_datetime(settings.END_DATETIME))
        signatures = await solana_api.fetch_finalized_signatures_by_account(
            settings.PUMP_FUN_PROGRAM_ID,
            until=get_first_signature_in_block(start_block.value),
            before=get_first_signature_in_block(end_block.value),
        )

    logger.info(f'{signatures=}')
    logger.info(f'{len(signatures)=}')


if __name__ == "__main__":
    asyncio.run(fetch_pumpfun_tokens_via_timerange())
