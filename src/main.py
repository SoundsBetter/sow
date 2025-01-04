import asyncio
import json
import logging
from dataclasses import dataclass
from datetime import datetime

from helius import TransactionsAPI
from solana.rpc.async_api import AsyncClient
from solders.pubkey import Pubkey
from solders.transaction_status import TransactionConfirmationStatus

from .settings import (
    RPC_URL,
    API_KEY,
    TARGET_MINT,
    TX_SOURCE,
    TX_TYPE,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class SwapEvent:
    """
    Represents a single swap event for a specific SPL token.
    """
    slot: int
    txn_hash: str
    token_mint_address: str
    user_address: str
    sol_amount: float
    token_amount: float
    is_buy: bool
    timestamp: str

async def chunked_iterable(iterable: list[str], chunk_size: int = 100) -> list[list[str]]:
    """
    Splits a list into chunks of specified size.
    """
    return [iterable[i:i + chunk_size] for i in range(0, len(iterable), chunk_size)]


def find_native_balance_change(account_data: list[dict], target_account: str) -> int:
    for account in account_data:
        if account["account"].strip() == target_account:
            return abs(account["nativeBalanceChange"])/10**9


def get_swap_data(tx: dict) -> SwapEvent:
    fee_payer = tx['feePayer']
    account_data = tx['accountData']
    from_user_account = tx['tokenTransfers'][0]['fromUserAccount']
    to_user_account = tx['tokenTransfers'][0]['toUserAccount']
    is_buy = fee_payer == to_user_account
    sol_amount = (
        find_native_balance_change(account_data, from_user_account)
        if is_buy else find_native_balance_change(account_data, to_user_account)
    )
    timestamp = datetime.fromtimestamp(tx['timestamp']).isoformat() + "Z"
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


async def fetch_transaction_history(mint_address: str) -> list[str]:
    async with AsyncClient(RPC_URL) as client:
        public_key = Pubkey.from_string(mint_address)
        last_signature = None
        results = []
        while True:
            try:
                signatures_response = await client.get_signatures_for_address(public_key, before=last_signature)
            except Exception as e:
                logger.error(f'Error fetching transactions: {e}')

            if not (data := signatures_response.value):
                break

            last_signature = data[-1].signature
            results.extend(
                [str(tx.signature) for tx in data if tx.confirmation_status == TransactionConfirmationStatus.Finalized]
            )
            await asyncio.sleep(5)  # TODO: remove after brake limits
        if not results:
            logger.error(f'No transactions found for: {mint_address}')

        return results

async def get_parsed_transactions_async(tx_api, chunk):
    try:
        return await asyncio.to_thread(tx_api.get_parsed_transactions, chunk)
    except Exception as e:
        logger.error(f'Error parsing transactions: {e}')
        return []

async def main():
    signatures = await fetch_transaction_history(TARGET_MINT)
    chunks = await chunked_iterable(signatures)
    tx_api = TransactionsAPI(API_KEY)
    parsed_txs = []

    tasks = [
        asyncio.create_task(get_parsed_transactions_async(tx_api, chunk))
        for chunk in chunks
    ]
    results = await asyncio.gather(*tasks)

    for parsed_transactions in results:
        filtered = [
            tx for tx in parsed_transactions
            if tx['source'] == TX_SOURCE and tx['type'] == TX_TYPE and tx['tokenTransfers']
        ]
        parsed_txs.extend(filtered)

    results = [get_swap_data(tx) for tx in parsed_txs]

    for res in results:
        logger.info(json.dumps(res.__dict__, indent=2))


if __name__ == "__main__":
    asyncio.run(main())
