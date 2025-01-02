from pprint import pprint

from helius import TransactionsAPI


def parse_helius_swaps(enriched_txs):
    return enriched_txs

transaction_api = TransactionsAPI('a5b5b179-92f9-42bc-8910-6cfb0f595d61')
transaction_history = transaction_api.get_parsed_transaction_history(address='KbCZjfexzrExJr7DmTcg8rqKCqrc5cxTPVvopoKJGwg')

parse_helius_swaps(transaction_history)
pprint(transaction_history)
print(f'Transactions count: {len(transaction_history)}')

