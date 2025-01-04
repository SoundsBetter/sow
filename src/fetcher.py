import asyncio
import logging

from solders.transaction_status import TransactionConfirmationStatus

from .api import SolanaAPI

logger = logging.getLogger(__name__)

class TransactionFetcher:
    def __init__(self, solana_client: SolanaAPI, target_mint: str):
        self.solana_client = solana_client
        self.target_mint = target_mint

    async def fetch_transactions(self) -> list[str]:
        last_signature = None
        results = []
        while True:
            try:
                signatures_response = await self.solana_client.get_signatures(self.target_mint, before=last_signature)
            except Exception as e:
                logger.error(f'Error fetching transactions: {e}')
                await asyncio.sleep(5)
                continue

            data = signatures_response.value
            if not data:
                break

            last_signature = data[-1].signature
            results.extend(
                [str(tx.signature) for tx in data if tx.confirmation_status == TransactionConfirmationStatus.Finalized]
            )
            await asyncio.sleep(5)  # TODO: remove after brake limits
        if not results:
            logger.warning(f'No transactions found for: {self.target_mint}')
        return results
