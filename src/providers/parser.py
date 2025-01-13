import logging

from datetime import datetime, timezone
from typing import Optional

from src.settings import settings
from src.providers.models import SwapEvent, MintedToken
from src.utils import find_native_balance_change

logger = logging.getLogger(__name__)

class TransactionParser:
    def __init__(self, mint: str = settings.TARGET_MINT):
        self.mint = mint

    def convert_to_swap_events(self, transactions: list[dict]) -> list[SwapEvent]:
        return [
            swap for tx in transactions
            if (swap := self.create_swap_event_from_transaction(tx))
               and swap.sol_amount and swap.sol_amount > settings.MIN_SOL_AMOUNT
        ]

    def convert_to_minted_token(self, transactions: list[dict]) -> list[MintedToken]:
        return [self.create_minted_token_from_transaction(tx) for tx in transactions]

    def create_swap_event_from_transaction(self, tx: dict) -> Optional[SwapEvent]:
        fee_payer = tx['feePayer']
        account_data = tx['accountData']
        token_transfer = [
            tt for tt in tx['tokenTransfers']
            if tt['mint'] == self.mint and tt['fromUserAccount'] and tt['toUserAccount']
        ][0]
        from_user_account = token_transfer['fromUserAccount']
        to_user_account = token_transfer['toUserAccount']
        is_buy = fee_payer != from_user_account
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

    def create_minted_token_from_transaction(self, tx: dict) -> Optional[MintedToken]:
        mint = [
            tt['mint'] for tt in tx['tokenTransfers'] if not tt['fromUserAccount'] and not tt['fromTokenAccount']
        ][0]
        txh = tx['signature']
        return MintedToken(mint, txh)
