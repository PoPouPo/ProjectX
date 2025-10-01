import os, time, hmac, hashlib, requests
from .config import Config
import urllib.parse

BASE = "https://api.binance.com"

def _now(): 
    return int(time.time() * 1000)

def _sign(query_string):
    """Génère la signature HMAC-SHA256"""
    print(f"DEBUG - String to sign: '{query_string}'")
    print(f"DEBUG - Secret key length: {len(Config.BINANCE_API_SECRET)}")
    
    signature = hmac.new(
        Config.BINANCE_API_SECRET.encode('utf-8'),
        query_string.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    print(f"DEBUG - Generated signature: {signature}")
    return signature

def _get(path, params=None, signed=False):
    params = params or {}
    headers = {'X-MBX-APIKEY': Config.BINANCE_API_KEY}
    
    if signed:
        # Les paramètres doivent être dans cet ordre : timestamp puis recvWindow
        params = {
            'timestamp': _now(),
            'recvWindow': 5000
        }
        # Trier par ordre alphabétique (Binance est très strict là-dessus)
        params = dict(sorted(params.items()))
        query_string = urllib.parse.urlencode(params, doseq=True)
        signature = _sign(query_string)
        params['signature'] = signature
    
    full_url = BASE + path
    print(f"DEBUG - Making request to: {full_url}")
    print(f"DEBUG - Params: {params}")
    print(f"DEBUG - Headers: {headers}")
    
    r = requests.get(full_url, params=params, headers=headers, timeout=15)
    
    print("Full URL:", r.url)
    print("Response status:", r.status_code)
    print("Response text:", r.text)
    
    r.raise_for_status()
    return r.json()

# Testez d'abord avec une requête simple
def test_binance_connection():
    """Testez cette fonction pour debugger"""
    try:
        # Test 1: Requête publique (devrait fonctionner)
        print("=== TEST REQUÊTE PUBLIQUE ===")
        price = _get("/api/v3/ticker/price", {"symbol": "BTCUSDT"})
        print("✓ Requête publique OK")
        
        # Test 2: Requête signée
        print("\n=== TEST REQUÊTE SIGNÉE ===")
        account = _get("/api/v3/account", signed=True)
        print("✓ Requête signée OK")
        return True
    except Exception as e:
        print(f"✗ Erreur: {e}")
        return False

# --- Fonctions appelées par les routes ---
def total_balance_usdt():
    try:
        acc = _get("/api/v3/account", signed=True)
        total = 0.0
        for b in acc["balances"]:
            qty = float(b["free"]) + float(b["locked"])
            if qty == 0: 
                continue
            if b["asset"] == "USDT":
                total += qty
            else:
                try:
                    symbol = b["asset"] + "USDT"
                    price_data = _get("/api/v3/ticker/price", {"symbol": symbol})
                    p = float(price_data["price"])
                    total += qty * p
                except Exception as e:
                    print(f"Erreur pour {b['asset']}: {e}")
                    pass
        return round(total, 2)
    except Exception as e:
        print(f"Erreur dans total_balance_usdt: {e}")
        return 0.0

def get_market_price(symbol: str):
    res = _get("/api/v3/ticker/price", {"symbol": symbol.upper()})
    return {"symbol": symbol.upper(), "price": res["price"]}

# Dans binance_service.py, renommer la fonction
def top_gainers_losers(limit=5, min_volume_usdt=500000):
    """
    Version optimisée qui élimine le bruit
    """
    try:
        tickers = _get("/api/v3/ticker/24hr")
        
        qualified = []
        for t in tickers:
            if not t["symbol"].endswith("USDT"):
                continue
                
            try:
                change = float(t.get("priceChangePercent", 0))
                volume = float(t.get("quoteVolume", 0))
                price = float(t.get("lastPrice", 0))
                
                # Filtres pour éliminer le bruit
                if (volume >= min_volume_usdt and    # Volume minimum
                    price >= 0.01 and                # Prix minimum  
                    abs(change) < 500 and            # Variation raisonnable
                    "UP" not in t["symbol"] and      # Exclure les leviers
                    "DOWN" not in t["symbol"] and
                    "BULL" not in t["symbol"] and
                    "BEAR" not in t["symbol"]):
                    
                    qualified.append(t)
                    
            except (ValueError, TypeError):
                continue
        
        # Trier par performance
        qualified.sort(key=lambda x: float(x.get("priceChangePercent", 0)))
        
        losers = qualified[:limit]
        gainers = qualified[-limit:][::-1]
        
        return gainers, losers
        
    except Exception as e:
        print(f"Erreur gainers/losers: {e}")
        return [], []
        
def portfolio():
    try:
        acc = _get("/api/v3/account", signed=True)
        out = []
        for b in acc["balances"]:
            qty = float(b["free"]) + float(b["locked"])
            if qty > 0.000001:  # Seuil plus bas pour capturer les petites quantités
                val = None
                if b["asset"] == "USDT":
                    val = qty
                else:
                    try:
                        symbol = b["asset"] + "USDT"
                        price_data = _get("/api/v3/ticker/price", {"symbol": symbol})
                        p = float(price_data["price"])
                        val = qty * p
                    except Exception as e:
                        print(f"Erreur prix pour {b['asset']}: {e}")
                        pass
                if val is not None:
                    out.append({
                        "asset": b["asset"], 
                        "qty": round(qty, 6), 
                        "value_usdt": round(val, 2)
                    })
        return sorted(out, key=lambda x: x["value_usdt"] or 0, reverse=True)
    except Exception as e:
        print(f"Erreur dans portfolio: {e}")
        return []
