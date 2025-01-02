import asyncio
import json
from pprint import pprint
from datetime import datetime
from typing import List

import requests
from solana.rpc.async_api import AsyncClient
from solders.pubkey import Pubkey
from solders.rpc.config import RpcTransactionConfig
from solders.rpc.requests import GetTransaction
from solders.signature import Signature
from solders.transaction_status import UiTransactionEncoding
from dataclasses import dataclass


@dataclass
class SwapEvent:
    slot: int
    txn_hash: str
    token_mint_address: str
    user_address: str
    sol_amount: int
    token_amount: int
    is_buy: bool
    timestamp: str

def parse_with_helius_enriched(signatures: List[str], api_key: str) -> List[dict]:
    """
    Звертається до ендпоінту:
      POST https://api.helius.xyz/v0/transactions?api-key=<API_KEY>
    з body:
      {"transactions": [ ...signatures... ]}
    і повертає список розпарсених об'єктів (один на кожну сигнатуру).
    """
    url = f"https://api.helius.xyz/v0/transactions?api-key={api_key}"
    payload = {
        "transactions": signatures[:100]
    }
    headers = {
        "Content-Type": "application/json"
    }
    resp = requests.post(url, headers=headers, data=json.dumps(payload))
    if resp.status_code == 200:
        return resp.json()  # list of enriched transactions
    else:
        print("Helius Enhanced API Error:", resp.status_code, resp.text)
        return []


async def fetch_all_swaps_for_token(mint_address: str, limit: int = 5):
    """
    1) Отримуємо (limit) останніх сигнатур для mint_address (через звичайний Solana RPC).
    2) Викликаємо parse_all_swap_events_for_signature() для кожної сигнатури,
       щоб побачити "власну" логіку pre-/postBalances.
    3) Потім викликаємо parse_with_helius_enriched() і порівнюємо/виводимо дані Helius.
    """
    rpc_url = "https://api.mainnet-beta.solana.com"
    async with AsyncClient(rpc_url) as client:
        public_key = Pubkey.from_string(mint_address)

        signatures_response = await client.get_signatures_for_address(public_key)
        if not signatures_response.value:
            print(f"No transaction history found for {mint_address}")
            return

        sigs = [str(info.signature) for info in signatures_response.value]

        api_key = "a5b5b179-92f9-42bc-8910-6cfb0f595d61"
        helius_data = parse_with_helius_enriched(sigs, api_key=api_key)

        print("\n=== Helius Enriched Data ===")
        for enriched_tx in helius_data:
            # enriched_tx - це dict з полями "signature", "type", "tokenTransfers", "nativeTransfers" тощо.
            sig = enriched_tx.get("signature", "")
            print(f"Signature: {sig}, Type: {enriched_tx.get('type')}, Source: {enriched_tx.get('source')}")



async def main():
    mint_address = "KbCZjfexzrExJr7DmTcg8rqKCqrc5cxTPVvopoKJGwg"
    await fetch_all_swaps_for_token(mint_address, limit=2)


if __name__ == "__main__":
    asyncio.run(main())
