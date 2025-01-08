class Settings:
    HELIUS_API_KEY = 'a5b5b179-92f9-42bc-8910-6cfb0f595d61'
    RPC_URL = 'https://api.mainnet-beta.solana.com'
    TX_SOURCES = ['PUMP_FUN', 'SYSTEM_PROGRAM']  # TODO: Find out needed sources
    TX_TYPES = ['SWAP', 'CREATE', 'TRANSFER']  # TODO: Find out needed types
    TARGET_MINT = '3Qr5bfs13ktHcoSHM1GLeYvsHk6WHoy23PRL44bxpump'


settings = Settings()
