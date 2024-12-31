import asyncio
import json
from pprint import pprint

from solana.rpc.async_api import AsyncClient
from solders.pubkey import Pubkey
from solders.rpc.config import RpcTransactionConfig
from solders.rpc.requests import GetTransaction
from solders.transaction_status import UiTransactionEncoding

from transaction_parser import (
    parse_sol_and_token_deltas,
    build_transaction_data,
)


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

        for signature_info in signatures_response.value:
            signature = signature_info.signature

            req = GetTransaction(
                signature,
                RpcTransactionConfig(
                    encoding=UiTransactionEncoding.JsonParsed,
                    max_supported_transaction_version=0,
                )
            )

            response_str = await client._provider.make_request_unparsed(req)
            raw_json = json.loads(response_str)

            if "result" not in raw_json or raw_json["result"] is None:
                print(f"No result for transaction {signature}")
                continue

            result = raw_json["result"]

            # 1. Build "simplified" TransactionData (old approach)
            tx_data = build_transaction_data(result, mint_address)
            if tx_data:
                transactions.append(tx_data)

            # 2. Simultaneously calculate all SOL and token deltas
            deltas = parse_sol_and_token_deltas(result)

            print("=== TX Signature:", signature, "===")
            print("Slot:", result.get("slot"), "BlockTime:", result.get("blockTime"))
            print("Simplified TransactionData:")
            pprint(tx_data)

            print("\nSOL deltas (lamports):")
            pprint(deltas.deltas_sol)
            print("\nToken deltas ( (owner, mint) -> amount ):")
            pprint(deltas.deltas_tokens)
            print("========================================\n")

            # Delay to avoid 429
            await asyncio.sleep(5)

        # After the loop, you can summarize your transactions
        print("======== Final transactions list ========")
        for tx in transactions:
            pprint(tx)


async def main():
    mint_address = "KbCZjfexzrExJr7DmTcg8rqKCqrc5cxTPVvopoKJGwg"
    await fetch_transaction_history(mint_address)


if __name__ == "__main__":
    asyncio.run(main())
