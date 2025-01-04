def chunked_iterable(iterable: list[str], chunk_size: int = 100) -> list[list[str]]:
    return [iterable[i:i + chunk_size] for i in range(0, len(iterable), chunk_size)]

def find_native_balance_change(account_data: list[dict], target_account: str) -> float:
    for account in account_data:
        if account["account"].strip() == target_account:
            return abs(account.get("nativeBalanceChange", 0)) / 10**9
