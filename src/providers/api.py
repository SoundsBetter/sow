import asyncio
import logging
from typing import Optional

import httpx
from solana.exceptions import SolanaRpcException
from solana.rpc.async_api import AsyncClient
from solana.rpc.core import RPCException
from solders.pubkey import Pubkey
from solders.rpc.responses import GetBlockResp
from solders.signature import Signature
from solders.transaction_status import TransactionConfirmationStatus, UiConfirmedBlock

from src.utils import chunked_iterable
from src.settings import settings

logger = logging.getLogger(__name__)

class SolanaAPI:
    def __init__(self, rpc_url: str):
        self.rpc_url = rpc_url
        self.client = AsyncClient(self.rpc_url)
        self.delay_before_request = 1

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.close()

    async def fetch_finalized_signatures_by_account(
            self,
            account: str,
            before: Optional[Signature] = None,
            until: Optional[Signature] = None,
    ) -> list[str]:
        account = Pubkey.from_string(account)
        results = []
        while True:
            await asyncio.sleep(self.delay_before_request)
            try:
                signatures_response = await self.client.get_signatures_for_address(account, before=before, until=until)
            except Exception as e:
                logger.error(f'Error fetching transactions: {e}')
                self.delay_before_request += 1
                continue

            data = signatures_response.value
            if not data:
                break

            before = data[-1].signature
            results.extend(
                [str(s.signature) for s in data if s.confirmation_status == TransactionConfirmationStatus.Finalized]
            )
        if not results:
            logger.warning(f'No transactions found for: {account}')
        return results

    async def get_current_slot_timestamp(self) -> tuple[int, int]:
        current_slot = await self.client.get_slot()
        current_block = await self.client.get_block(current_slot.value, max_supported_transaction_version=0)
        return current_slot.value, current_block.value.block_time

    async def get_blok_by_timestamp(self, input_timestamp: int) -> GetBlockResp:
        try:
            cur_slot, cur_block_timestamp = await self.get_current_slot_timestamp()
        except SolanaRpcException as e:
            cur_slot, cur_block_timestamp = await self.get_current_slot_timestamp()
        while True:
            slot_delta = int((cur_block_timestamp - input_timestamp) // settings.SLOT_DURATION)
            proxy_slot = cur_slot - slot_delta
            await asyncio.sleep(self.delay_before_request)
            try:
                proxy_block = await self.client.get_block(proxy_slot, max_supported_transaction_version=0)
                if proxy_block.value.block_time == input_timestamp:
                    return proxy_block
                cur_slot = proxy_slot
                cur_block_timestamp = proxy_block.value.block_time
            except SolanaRpcException as e:
                logger.error(f'Error fetching block: {e}')
                self.delay_before_request += 1
                continue
            except RPCException as e:
                logger.error(f'Error fetching block: {e}')
                cur_slot += 1


class HeliusAPI:
    def __init__(self, api_key: str):
        self.api_key = api_key

    async def get_transactions_for_chunk(self, chunk: list[str]):
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

    async def get_detail_transactions_for_mint(self, signatures: list[str], mint: str) -> list[dict]:
        results = [
            await self.get_transactions_for_chunk(chunk)
            for chunk in chunked_iterable(signatures)
        ]
        # write_data_to_json_file(results)  # IF YOU NEED STORE RAW DATA TO FILE
        return [tx for parsed_transactions in results for tx in parsed_transactions if self.validate_tx(tx, mint)]

    def validate_tx(self, tx: dict, mint: str) -> bool:
        if tx.get("transactionError"):
            return False
        if not self.is_pumpfun_swap(tx):
            return False
        if not [
            tt for tt in tx['tokenTransfers']
            if tt.get('mint') == mint and tt.get('fromUserAccount') and tt.get('toUserAccount')
        ]:
            return False
        return True

    def is_pumpfun_swap(self, tx: dict) -> bool:
        for instruction in tx.get("instructions", []):
            if instruction.get("programId") == settings.PUMP_FUN_PROGRAM_ID:
                return True
            for inner in instruction.get("innerInstructions", []):
                if inner.get("programId") == settings.PUMP_FUN_PROGRAM_ID:
                    return True
        return False