# Solana Swap Event Collector

## Overview

Solana Swap Event Collector is a Python-based tool designed to fetch, parse, and process SWAP transactions for a specific SPL token on the Solana blockchain. By leveraging the Solana RPC and Helius APIs, this tool efficiently retrieves transaction data, validates it, and extracts meaningful information about swap events, including details such as transaction hash, token amounts, user addresses, and timestamps in UTC.

To start run `python -m src.fetch_pumpfun_swaps_via_mint`

To set mint address change `TARGET_MINT` in `settings`

To get minted tokens on Pump.fun run `python -m src.fetch_pumpfun_tokens_via_timerange`
