import logging

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
        self.api = TransactionsAPI(api_key)

    def get_parsed_transactions(self, chunk):
        return self.api.get_parsed_transactions(chunk)
