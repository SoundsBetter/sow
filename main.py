import asyncio
import json
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from helius import TransactionsAPI

@dataclass
class SwapEvent:
    """
    Represents a single swap event for a specific SPL token.

    Attributes:
        slot: The block number (slot).
        txn_hash: The transaction signature (hash).
        token_mint_address: The mint address of the SPL token.
        user_address: The account address that changed token balance.
        sol_amount: The SOL amount (in lamports) changed in this account.
        token_amount: The raw integer token amount changed in this account (with decimals considered).
        is_buy: Indicates whether the account received (+) or sent (-) token_amount.
        timestamp: ISO8601 string of the transaction's block time.
    """
    slot: int
    txn_hash: str
    token_mint_address: str
    user_address: str
    sol_amount: int
    token_amount: int
    is_buy: bool
    timestamp: str


async def fetch_token_swaps(
    mint_address: str,
    api_key: str,
    bonding_curve_address: Optional[str] = None
) -> List[SwapEvent]:
    """
    Fetches and parses token swaps for a specific SPL token using Helius parsed transaction history.
    Each accountData entry with a tokenBalanceChanges that matches the given mint_address
    generates a SwapEvent.

    Args:
        mint_address: The target SPL token mint address.
        api_key: The Helius API key.
        bonding_curve_address: An optional bonding curve program address (not used in filtering).

    Returns:
        A list of SwapEvent objects representing each balance change of the token mint_address.
    """
    tx_api = TransactionsAPI(api_key)
    transaction_history = tx_api.get_parsed_transaction_history(address=mint_address)
    if not transaction_history:
        return []

    results: List[SwapEvent] = []
    for tx in transaction_history:
        signature = tx.get("signature", "")
        slot = tx.get("slot", 0)
        ts_unix = tx.get("timestamp", 0)
        dt_str = ""
        if ts_unix:
            dt_str = datetime.fromtimestamp(ts_unix).isoformat() + "Z"

        if bonding_curve_address:
            account_data_list = tx.get("accountData", [])
            all_accounts = [d.get("account", "") for d in account_data_list]
            if bonding_curve_address not in all_accounts:
                continue

        account_data_list = tx.get("accountData", [])
        for acc_data in account_data_list:
            user_addr = acc_data.get("account", "")
            native_change = acc_data.get("nativeBalanceChange", 0)
            token_changes = acc_data.get("tokenBalanceChanges", [])

            for tchange in token_changes:
                mint = tchange.get("mint", "")
                if mint != mint_address:
                    continue
                raw_info = tchange.get("rawTokenAmount", {})
                raw_token_str = raw_info.get("tokenAmount", "0")
                try:
                    raw_token_int = int(raw_token_str)
                except ValueError:
                    raw_token_int = 0
                is_buy = (raw_token_int > 0)

                event = SwapEvent(
                    slot=slot,
                    txn_hash=signature,
                    token_mint_address=mint_address,
                    user_address=user_addr,
                    sol_amount=native_change,
                    token_amount=raw_token_int,
                    is_buy=is_buy,
                    timestamp=dt_str
                )
                results.append(event)
    return results


async def main():
    helius_api_key = "a5b5b179-92f9-42bc-8910-6cfb0f595d61"
    target_mint = "KbCZjfexzrExJr7DmTcg8rqKCqrc5cxTPVvopoKJGwg"
    bonding_curve_addr = None
    events = await fetch_token_swaps(
        mint_address=target_mint,
        api_key=helius_api_key,
        bonding_curve_address=bonding_curve_addr
    )
    for ev in events:
        print(json.dumps(ev.__dict__, indent=2))

    print(f'Find {len(events)} swaps')


if __name__ == "__main__":
    asyncio.run(main())
