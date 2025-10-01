import os
from dotenv import load_dotenv

dotenv_path = '/Users/poupou/Downloads/projectX/.env'
load_dotenv(dotenv_path)

import ccxt
from typing import List, Dict

class DataManager:

    def __init__(self):
        api_key    = os.getenv("BINANCE_API_KEY")
        api_secret = os.getenv("BINANCE_SECRET_KEY")
        if not api_key or not api_secret:
            raise RuntimeError("Clés API Binance manquantes (.env)")
        self.exchange = ccxt.binance({
            "apiKey": api_key,
            "secret": api_secret,
            "enableRateLimit": True
        })

    # === Portefeuille ===
    def get_user_portfolio(self, user_id: int) -> Dict:
        """
        Retourne le solde total en USDT et les balances disponibles.
        """
        balances = self.exchange.fetch_balance()
        total_usdt = balances["total"].get("USDT", 0.0)
        assets = []
        for coin, amount in balances["total"].items():
            if amount and amount > 0:
                assets.append({"symbol": coin, "amount": amount})
        return {"total_balance": total_usdt, "assets": assets}

    # === Historique de trades ===
    def get_trade_history(self, user_id: int, limit: int = 10) -> List[Dict]:
        """
        Retourne les derniers trades sur le marché DOGE/USDT (par défaut).
        """
        symbol = "DOGE/USDT"
        trades = self.exchange.fetch_my_trades(symbol, limit=limit)
        history = []
        for t in trades:
            history.append({
                "symbol": t["symbol"],
                "side": t["side"],
                "price": t["price"],
                "amount": t["amount"],
                "timestamp": t["datetime"]
            })
        return history

    # === Passage d'ordre ===
    def place_order(self, user_id: int, order_data: Dict) -> Dict:
        """
        Passe un ordre au marché.
        order_data doit contenir : { "symbol": "DOGE/USDT", "side": "buy"|"sell", "amount": float }
        """
        symbol = order_data.get("symbol", "DOGE/USDT")
        side   = order_data.get("side", "buy")
        amount = float(order_data.get("amount", 1.0))
        order  = self.exchange.create_market_order(symbol, side, amount)
        return {
            "id": order["id"],
            "symbol": order["symbol"],
            "side": order["side"],
            "price": order.get("price"),
            "amount": order["amount"],
            "status": order["status"]
        }

