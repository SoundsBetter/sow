from dataclasses import dataclass

@dataclass
class SwapEvent:
    slot: int
    txn_hash: str
    token_mint_address: str
    user_address: str
    sol_amount: float
    token_amount: float
    is_buy: bool
    timestamp: str
