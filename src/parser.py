import asyncio
import logging

from datetime import datetime, timezone

from .api import HeliusAPI
from .models import SwapEvent
from .utils import find_native_balance_change

logger = logging.getLogger(__name__)

class TransactionParser:
    def __init__(self, helius_api: HeliusAPI, tx_source: str, tx_types: str, max_concurrent_tasks: int):
        self.helius_api = helius_api
        self.tx_source = tx_source
        self.tx_types = tx_types
        self.semaphore = asyncio.Semaphore(max_concurrent_tasks)

    async def parse_transactions(self, chunks: list[list[str]]) -> list[dict]:
        parsed_txs = []
        tasks = [
            asyncio.create_task(self.get_parsed_transactions_async(chunk))
            for chunk in chunks
        ]
        results = await asyncio.gather(*tasks)
        for parsed_transactions in results:
            filtered = [
                tx for tx in parsed_transactions
                if tx.get('source') == self.tx_source and tx.get('type') in self.tx_types and tx.get('tokenTransfers')
            ]
            parsed_txs.extend(filtered)
        return parsed_txs

    async def get_parsed_transactions_async(self, chunk: list[str]) -> list[dict]:
        async with self.semaphore:
            try:
                return await asyncio.to_thread(self.helius_api.get_parsed_transactions, chunk)
            except Exception as e:
                logger.error(f'Error parsing transactions: {e}')
                return []

    def convert_to_swap_events(self, transactions: list[dict]) -> list[SwapEvent]:
        return [self.create_swap_event(tx) for tx in transactions]

    def create_swap_event(self, tx: dict) -> SwapEvent:
        fee_payer = tx['feePayer']
        account_data = tx['accountData']
        from_user_account = tx['tokenTransfers'][0]['fromUserAccount']
        to_user_account = tx['tokenTransfers'][0]['toUserAccount']
        is_buy = fee_payer == to_user_account
        sol_amount = (
            find_native_balance_change(account_data, from_user_account)
            if is_buy else find_native_balance_change(account_data, to_user_account)
        )
        timestamp = datetime.fromtimestamp(tx['timestamp'], tz=timezone.utc).isoformat() + "Z"
        return SwapEvent(
            slot=tx['slot'],
            txn_hash=tx['signature'],
            token_mint_address=tx['tokenTransfers'][0]['mint'],
            user_address=fee_payer,
            sol_amount=sol_amount,
            token_amount=tx['tokenTransfers'][0]['tokenAmount'],
            is_buy=is_buy,
            timestamp=timestamp
        )
