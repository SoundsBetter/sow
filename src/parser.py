import logging

from datetime import datetime, timezone

from .api import HeliusAPI
from .models import SwapEvent
from .utils import find_native_balance_change, write_data_to_json_file

logger = logging.getLogger(__name__)

class TransactionParser:
    def __init__(self, helius_api: HeliusAPI, tx_sources: list[str], mint: str):
        self.helius_api = helius_api
        self.tx_sources = tx_sources
        self.mint = mint

    async def parse_transactions(self, chunks: list[list[str]]) -> list[dict]:
        parsed_txs = []
        results = [
            await self.helius_api.get_parsed_transactions(chunk)
            for chunk in chunks
        ]
        write_data_to_json_file(results)
        for parsed_transactions in results:
            filtered = [
                tx for tx in parsed_transactions
                if tx.get("source") in self.tx_sources
                   and tx.get("tokenTransfers")
                   and not tx.get("transactionError")
            ]
            parsed_txs.extend(filtered)
        return parsed_txs

    def convert_to_swap_events(self, transactions: list[dict]) -> list[SwapEvent]:
        return [swap for tx in transactions if (swap := self.create_swap_event(tx)).sol_amount and swap.sol_amount >= 0.01]

    def create_swap_event(self, tx: dict) -> SwapEvent:
        fee_payer = tx['feePayer']
        account_data = tx['accountData']
        token_transfer = [tt for tt in tx['tokenTransfers'] if tt['mint'] == self.mint][0]
        from_user_account = token_transfer['fromUserAccount']
        to_user_account = token_transfer['toUserAccount']
        is_buy = fee_payer == to_user_account
        sol_amount = (
            find_native_balance_change(account_data, from_user_account)
            if is_buy else find_native_balance_change(account_data, to_user_account)
        )
        timestamp = datetime.fromtimestamp(tx['timestamp'], tz=timezone.utc).isoformat() + "Z"
        return SwapEvent(
            slot=tx['slot'],
            txn_hash=tx['signature'],
            token_mint_address=token_transfer['mint'],
            user_address=fee_payer,
            sol_amount=sol_amount,
            token_amount=token_transfer['tokenAmount'],
            is_buy=is_buy,
            timestamp=timestamp
        )
