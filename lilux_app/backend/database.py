import sqlite3
import hashlib
import json
from cryptography.fernet import Fernet
from .config import Config

class DatabaseManager:
    def __init__(self):
        self.db_path = Config.DATABASE_URL
        self.fernet = Config.get_fernet_key()
        self.init_database()
    
    def get_connection(self):
        """Get database connection"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_database(self):
        """Initialize database tables"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Users table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # API keys table (encrypted)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS api_keys (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                exchange TEXT NOT NULL,
                encrypted_data TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        
        # Portfolio data table (encrypted)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS portfolio (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                encrypted_data TEXT NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        
        # Trades table (encrypted)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                encrypted_data TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        """)
        
        # Create default admin user if doesn't exist
        self._create_default_user(cursor)
        
        conn.commit()
        conn.close()
    
    def _create_default_user(self, cursor):
        """Create default admin user"""
        import bcrypt
        
        cursor.execute("SELECT COUNT(*) FROM users WHERE username = ?", (Config.DEFAULT_USERNAME,))
        if cursor.fetchone()[0] == 0:
            password_hash = bcrypt.hashpw(Config.DEFAULT_PASSWORD.encode(), bcrypt.gensalt()).decode()
            cursor.execute(
                "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                (Config.DEFAULT_USERNAME, password_hash)
            )
    
    def encrypt_data(self, data):
        """Encrypt data using Fernet"""
        if isinstance(data, dict):
            data = json.dumps(data)
        return self.fernet.encrypt(data.encode()).decode()
    
    def decrypt_data(self, encrypted_data):
        """Decrypt data using Fernet"""
        decrypted = self.fernet.decrypt(encrypted_data.encode()).decode()
        try:
            return json.loads(decrypted)
        except json.JSONDecodeError:
            return decrypted
    
    def get_user_by_username(self, username):
        """Get user by username"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        user = cursor.fetchone()
        conn.close()
        return dict(user) if user else None

# Global database instance
db = DatabaseManager()