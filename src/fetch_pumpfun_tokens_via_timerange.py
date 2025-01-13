import asyncio
import json
import logging
from dataclasses import asdict

from solders.signature import Signature
from solders.transaction_status import UiConfirmedBlock

from src.providers.parser import TransactionParser
from src.settings import settings
from src.providers.api import SolanaAPI, HeliusAPI
from src.utils import get_timestamp_from_datetime, write_data_to_json_file

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_first_signature_in_block(block: UiConfirmedBlock) -> Signature:
    return block.transactions[0].transaction.signatures[0]

async def fetch_pumpfun_tokens_via_timerange():
    solana_api = SolanaAPI(settings.RPC_URL)
    helius_api = HeliusAPI(settings.HELIUS_API_KEY)
    parser = TransactionParser()

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

    created_txs = await helius_api.get_detail_transactions_created_token_pumpfun(signatures)
    minted_tokens = parser.convert_to_minted_token(created_txs)
    write_data_to_json_file([asdict(token) for token in minted_tokens], 'created_tx.json')

    for event in minted_tokens:
        logger.info(json.dumps(event, indent=2))

    logger.info(f'Count of swaps: {len(minted_tokens)}')


if __name__ == "__main__":
    asyncio.run(fetch_pumpfun_tokens_via_timerange())
