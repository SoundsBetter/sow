class BaseSettings:
    HELIUS_API_KEY = 'a5b5b179-92f9-42bc-8910-6cfb0f595d61'
    RPC_URL = 'https://api.mainnet-beta.solana.com'
    TX_SOURCE = 'PUMP_FUN'
    TX_TYPE = 'SWAP'


class Settings(BaseSettings):
    TARGET_MINT = 'EWbs7dsWY9PvkXZEi7giuA1j7VLLXejBC6T8KViTpump'
    HELIUS_MAX_TASKS = 1  # TODO: increase after brake limits


settings = Settings()
