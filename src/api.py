import asyncio
import logging

import httpx
from solana.rpc.async_api import AsyncClient
from solders.pubkey import Pubkey
from helius import TransactionsAPI

logger = logging.getLogger(__name__)

class SolanaAPI:
    def __init__(self, rpc_url: str):
        self.rpc_url = rpc_url
        self.client = AsyncClient(self.rpc_url)

    async def get_signatures(self, mint_address: str, before: str = None):
        public_key = Pubkey.from_string(mint_address)
        return await self.client.get_signatures_for_address(public_key, before=before)

    async def close(self):
        await self.client.close()

class HeliusAPI:
    def __init__(self, api_key: str):
        self.api_key = api_key

    async def get_parsed_transactions(self, chunk):
        payload = {
            "transactions": chunk
        }
        async with httpx.AsyncClient() as client:
            while True:
                try:
                    res = await client.post(f"https://api.helius.xyz/v0/transactions?api-key={self.api_key}", json=payload)
                except Exception as e:
                    logger.error(f'Error while parsing transactions: {e}')
                    await asyncio.sleep(3)
                    continue
                if res.status_code != 200:
                    logger.error(f'Error while parsing transactions: {res.status_code}: {res.text}')
                    await asyncio.sleep(3)
                    continue
                return res.json()
