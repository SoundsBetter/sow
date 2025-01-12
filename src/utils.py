import json
from datetime import datetime


def chunked_iterable(iterable: list[str], chunk_size: int = 100) -> list[list[str]]:
    return [iterable[i:i + chunk_size] for i in range(0, len(iterable), chunk_size)]

def find_native_balance_change(account_data: list[dict], target_account: str) -> float:
    for account in account_data:
        if account["account"].strip() == target_account:
            return abs(account.get("nativeBalanceChange", 0)) / 10**9

def write_data_to_json_file(data) -> None:
    with open("data.json", "w") as f:
        f.write(json.dumps(data, indent=2))

def get_timestamp_from_datetime(datetime_str: str) -> int:
    dt = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M:%S")
    return int(dt.timestamp())
