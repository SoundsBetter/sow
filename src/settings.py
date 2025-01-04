class Settings:
    HELIUS_API_KEY = 'a5b5b179-92f9-42bc-8910-6cfb0f595d61'
    RPC_URL = 'https://api.mainnet-beta.solana.com'
    TX_SOURCE = 'PUMP_FUN'
    TX_TYPES = ['SWAP', 'CREATE']  # TODO: Find out needed types
    TARGET_MINT = '4WZ8JEcvz5eUPSH25MNPt1aSv1WpUVRa4cPT8WRgpump'
    HELIUS_MAX_TASKS = 1  # TODO: increase after brake limits


settings = Settings()
