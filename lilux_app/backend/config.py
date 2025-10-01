import os
from cryptography.fernet import Fernet

class Config:
    # JWT Configuration
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'dHAoGlD98Vh0QR071nsw5pUax7wtnTrwsamujBrs2yw')
    JWT_ALGORITHM = 'HS256'
    JWT_EXPIRE_MINUTES = 60 * 24  # 24 hours
    
    # Database Configuration
    DATABASE_URL = "lilux_app.db"
    ENCRYPTION_KEY = os.getenv('ENCRYPTION_KEY', 'NeDXVnMXLAK0wKrFGm1zi6Ibs5bpJ1VEiDdX9VwYvRk=')
    
    # Rate Limiting
    LOGIN_RATE_LIMIT = "3/minute"

    # Binance config
    BINANCE_API_KEY="Jz3n5KPfMsPteiIiiH79gBo1tcc3NRKelycVZlzpTtaQbKGge2JuHwssNSsnBMWp"
    BINANCE_API_SECRET="YpsDnX3TyrbN9fjUsOGQ4aTAuEzeObbHqbHE6x9XYDALNdZv3x8dFRsxrVvnaQJM"
    BINANCE_SYMBOLS=["BTCUSDT","ETHUSDT","SOLUSDT","DOGEUSDT","TONUSDT","BNBUSDT","POLUSDT"]

    # CORS
    CORS_ORIGINS = ["http://localhost:5000", "http://127.0.0.1:5000"]
    
    # Default Admin User
    DEFAULT_USERNAME = "admin"
    DEFAULT_PASSWORD = "admin123"  # Will be hashed in database
    
    @classmethod
    def get_fernet_key(cls):
        """Get Fernet encryption key"""
        key = cls.ENCRYPTION_KEY
        if isinstance(key, str):
            key = key.encode()
        return Fernet(key)
    