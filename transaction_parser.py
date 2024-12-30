from dataclasses import dataclass


@dataclass
class SolDelta:
    """Change in SOL (in lamports) for a specific account."""
    pubkey: str
    delta_lamports: int


@dataclass
class TokenDelta:
    """Change in SPL-tokens for (owner, mint)."""
    owner: str
    mint: str
    delta_amount: int


def parse_full_deltas(tx_data: dict):
    """
    Takes raw transaction data as input (in the format returned 
    by RPC with encoding='jsonParsed').
    Returns:
      - list of deltas_sol: [SolDelta(pubkey, delta_lamports), ...]
      - list of deltas_tokens: [TokenDelta(owner, mint, delta_amount), ...]
    """
    message = tx_data["transaction"]["message"]
    meta = tx_data["meta"]

    # === 1. Collect the list of accountKeys addresses (in the order they appear in pre/postBalances).
    # If there are addressTableLookups, there might be additional addresses, 
    # but for simplicity, assume the library has accounted for them.
    all_keys = [acc["pubkey"] for acc in message["accountKeys"]]

    pre_balances = meta.get("preBalances", [])
    post_balances = meta.get("postBalances", [])

    # === 2. Calculate SOL deltas ===
    sol_deltas = []
    for i in range(len(pre_balances)):
        pubkey = all_keys[i] if i < len(all_keys) else f"Unknown_{i}"
        delta = post_balances[i] - pre_balances[i]
        if delta != 0:
            sol_deltas.append(SolDelta(pubkey=pubkey, delta_lamports=delta))

    # === 3. Calculate SPL-token deltas ===
    pre_map = {}  # (owner, mint) -> int_amount
    post_map = {}  # (owner, mint) -> int_amount

    pre_token_balances = meta.get("preTokenBalances", [])
    post_token_balances = meta.get("postTokenBalances", [])

    for tb in pre_token_balances:
        owner = tb["owner"]
        mint = tb["mint"]
        amount_int = int(tb["uiTokenAmount"]["amount"])
        pre_map[(owner, mint)] = amount_int

    for tb in post_token_balances:
        owner = tb["owner"]
        mint = tb["mint"]
        amount_int = int(tb["uiTokenAmount"]["amount"])
        post_map[(owner, mint)] = amount_int

    all_token_keys = set(pre_map.keys()) | set(post_map.keys())

    token_deltas = []
    for k in all_token_keys:
        pre_amount = pre_map.get(k, 0)
        post_amount = post_map.get(k, 0)
        diff = post_amount - pre_amount
        if diff != 0:
            token_deltas.append(TokenDelta(owner=k[0], mint=k[1], delta_amount=diff))

    return sol_deltas, token_deltas
