import asyncio
import json
from dataclasses import dataclass
from datetime import datetime
from pprint import pprint

from solana.rpc.async_api import AsyncClient
from solders.pubkey import Pubkey
from solders.rpc.config import RpcTransactionConfig
from solders.rpc.requests import GetTransaction
from solders.transaction_status import UiTransactionEncoding

from transaction_parser import parse_full_deltas


@dataclass
class TransactionData:
    slot: int
    txn_hash: str
    token_mint_address: str
    user_address: str
    sol_amount: int
    token_amount: int
    is_buy: bool
    timestamp: str


async def fetch_transaction_history(mint_address: str):
    rpc_url = "https://api.mainnet-beta.solana.com"
    async with AsyncClient(rpc_url) as client:
        public_key = Pubkey.from_string(mint_address)

        signatures_response = await client.get_signatures_for_address(public_key)
        if not signatures_response.value:
            print(f"No transaction history found for {mint_address}")
            return

        print(f"Found {len(signatures_response.value)} transactions for {mint_address}")
        transactions = []

        # Limit to 2 transactions for this example
        for signature_info in signatures_response.value:
            signature = signature_info.signature

            req = GetTransaction(
                signature,
                RpcTransactionConfig(
                    encoding=UiTransactionEncoding.JsonParsed,
                    max_supported_transaction_version=0
                )
            )
            # Using "raw" make_request_unparsed call
            response_str = await client._provider.make_request_unparsed(req)
            raw_json = json.loads(response_str)

            if "result" not in raw_json or raw_json["result"] is None:
                print(f"No result for transaction {signature}")
                continue

            result = raw_json["result"]
            slot = result.get("slot", 0)
            txn_hash = signature
            block_time = result.get("blockTime", None)
            timestamp = datetime.fromtimestamp(block_time).isoformat() + "Z" if block_time else None

            tx_info = result.get("transaction", {})
            meta_info = result.get("meta", {})

            # ---------------------------
            # Existing "simplified" calculation (as in your code):
            pre_balances = meta_info.get("preBalances", [])
            post_balances = meta_info.get("postBalances", [])
            sol_amount = (pre_balances[0] - post_balances[0]) if pre_balances and post_balances else 0

            token_amount = 0
            pre_token_balances = meta_info.get("preTokenBalances", [])
            post_token_balances = meta_info.get("postTokenBalances", [])
            if pre_token_balances and post_token_balances:
                pre_amount_str = pre_token_balances[0]["uiTokenAmount"]["amount"]
                post_amount_str = post_token_balances[0]["uiTokenAmount"]["amount"]
                token_amount = int(post_amount_str) - int(pre_amount_str)

            message_dict = tx_info.get("message", {})
            account_keys = message_dict.get("accountKeys", [])
            user_address = account_keys[0]["pubkey"] if account_keys else "Unknown"

            is_buy = token_amount > 0

            # Create a simple "TransactionData" (your format)
            transactions.append(TransactionData(
                slot=slot,
                txn_hash=str(txn_hash),
                token_mint_address=mint_address,
                user_address=user_address,
                sol_amount=sol_amount,
                token_amount=token_amount,
                is_buy=is_buy,
                timestamp=timestamp,
            ))
            # ---------------------------

            # ---------------------------
            # Add "Full" calculation for debugging/review
            sol_deltas, token_deltas = parse_full_deltas(result)
            print("\n=== Full Deltas for transaction", signature, "===")
            if sol_deltas:
                print("SOL Changes (lamports):")
                for d in sol_deltas:
                    print(f"  {d.pubkey}: {d.delta_lamports}")
            else:
                print("No SOL changes")

            if token_deltas:
                print("SPL Token Changes:")
                for t in token_deltas:
                    print(f"  owner={t.owner} mint={t.mint} delta={t.delta_amount}")
            else:
                print("No SPL token changes")
            # ---------------------------

            await asyncio.sleep(0.5)

        # Output "simplified" results
        print("\nFinal collected simplified transactions:")
        for tx in transactions:
            pprint(tx)


async def main():
    mint_address = "KbCZjfexzrExJr7DmTcg8rqKCqrc5cxTPVvopoKJGwg"
    await fetch_transaction_history(mint_address)


if __name__ == "__main__":
    asyncio.run(main())
