from dataclasses import dataclass
from datetime import datetime
from typing import Optional


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


@dataclass
class TransactionDeltas:
    """
    Stores a detailed description of all changes in SOL and SPL tokens:
      - deltas_sol: { pubkey: delta_lamports }
      - deltas_tokens: { (owner, mint): delta_amount }
    """
    deltas_sol: dict[str, int]
    deltas_tokens: dict[tuple[str, str], int]


def parse_sol_and_token_deltas(raw_result: dict) -> TransactionDeltas:
    """
    Takes the "result" from raw JSON (raw_json["result"]).
    Returns a TransactionDeltas object in which
    - deltas_sol: changes in SOL across accounts
    - deltas_tokens: changes in SPL tokens by (owner, mint)
    """
    message = raw_result.get("transaction", {}).get("message", {})
    meta = raw_result.get("meta", {})

    pre_balances = meta.get("preBalances", [])
    post_balances = meta.get("postBalances", [])

    account_keys_info = message.get("accountKeys", [])
    all_keys = [info["pubkey"] for info in account_keys_info]

    deltas_sol: dict[str, int] = {}
    for i in range(len(pre_balances)):
        if i < len(all_keys):
            pubkey = all_keys[i]
        else:
            pubkey = f"unknown_{i}"
        sol_diff = post_balances[i] - pre_balances[i]
        if sol_diff != 0:
            deltas_sol[pubkey] = sol_diff

    pre_token_balances = meta.get("preTokenBalances", [])
    post_token_balances = meta.get("postTokenBalances", [])

    pre_map = {}
    post_map = {}

    for tb in pre_token_balances:
        owner = tb["owner"]
        mint = tb["mint"]
        amount_str = tb["uiTokenAmount"]["amount"]
        pre_map[(owner, mint)] = int(float(amount_str))

    for tb in post_token_balances:
        owner = tb["owner"]
        mint = tb["mint"]
        amount_str = tb["uiTokenAmount"]["amount"]
        post_map[(owner, mint)] = int(float(amount_str))

    all_token_keys = set(pre_map.keys()) | set(post_map.keys())
    deltas_tokens: dict[tuple[str, str], int] = {}
    for k in all_token_keys:
        pre_amount = pre_map.get(k, 0)
        post_amount = post_map.get(k, 0)
        diff = post_amount - pre_amount
        if diff != 0:
            deltas_tokens[k] = diff

    return TransactionDeltas(deltas_sol=deltas_sol, deltas_tokens=deltas_tokens)


def build_transaction_data(raw_result: dict, mint_address: str) -> Optional[TransactionData]:
    slot = raw_result.get("slot", 0)
    signature = raw_result.get("transaction", {}).get("signatures", [""])[0]
    block_time = raw_result.get("blockTime", None)
    timestamp_str = None
    if block_time:
        timestamp_str = datetime.fromtimestamp(block_time).isoformat() + "Z"

    meta_info = raw_result.get("meta", {})
    if not meta_info:
        return

    sol_amount = meta_info.get("fee", 0)

    deltas = parse_sol_and_token_deltas(raw_result)
    token_amount = 0
    for (owner, mint), delta in deltas.deltas_tokens.items():
        if mint == mint_address:
            token_amount += delta

    is_buy = token_amount > 0

    message = raw_result.get("transaction", {}).get("message", {})
    account_keys = message.get("accountKeys", [])
    if account_keys:
        user_address = account_keys[0]["pubkey"]
    else:
        user_address = "Unknown"

    return TransactionData(
        slot=slot,
        txn_hash=signature,
        token_mint_address=mint_address,
        user_address=user_address,
        sol_amount=sol_amount,
        token_amount=token_amount,
        is_buy=is_buy,
        timestamp=timestamp_str if timestamp_str else "",
    )
