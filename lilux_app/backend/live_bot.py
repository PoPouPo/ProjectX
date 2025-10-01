"""
Trendline Continue SG – Version adaptée pour intégration dashboard web
Basé sur votre bot original mais avec les fonctions nécessaires pour visu_bot.py

Ce fichier contient:
1. Les fonctions fetch_ohlcv() et compute_signals() pour visu_bot.py
2. Votre logique de trading originale (optionnelle)
3. Configuration flexible avec/sans API réelle
"""

import os
import time
import math
import numpy as np
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

# Essai d'import CCXT (optionnel pour le dashboard)
try:
    import ccxt
    import requests
    CCXT_AVAILABLE = True
    load_dotenv()
except ImportError:
    CCXT_AVAILABLE = False
    print("⚠️ CCXT non disponible - Mode simulation activé")

# ======================
# Paramètres de stratégie (vos réglages originaux)
# ======================
SG_LENGTH = 150
SLOPE_LENGTH = 20
SMALEN = 50
SENS = 0.000085  # 0.85% du prix

# Configuration par défaut pour visu_bot.py
TIMEFRAME = '5m'
SYMBOL = 'DOGEUSDT'  # Format Binance pour visu_bot
POLL_SECONDS = 60 * 5

# ======================
# Configuration Exchange (optionnelle)
# ======================
if CCXT_AVAILABLE:
    TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
    TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
    EXCHANGE_ID = os.getenv('CCXT_EXCHANGE', 'binance')
    API_KEY = os.getenv('CCXT_APIKEY')
    API_SECRET = os.getenv('CCXT_SECRET')
    
    if API_KEY and API_SECRET:
        exchange_class = getattr(ccxt, EXCHANGE_ID)
        exchange = exchange_class({
            'apiKey': API_KEY,
            'secret': API_SECRET,
            'enableRateLimit': True,
        })
        EXCHANGE_CONFIGURED = True
    else:
        EXCHANGE_CONFIGURED = False
        print("⚠️ Clés API non configurées - Mode simulation")
else:
    EXCHANGE_CONFIGURED = False

# ======================
# Indicateurs helpers (vos fonctions originales)
# ======================

def ema(series: pd.Series, length: int) -> pd.Series:
    """Exponential Moving Average"""
    return series.ewm(span=length, adjust=False).mean()

def sma(series: pd.Series, length: int) -> pd.Series:
    """Simple Moving Average"""
    return series.rolling(length).mean()

def linreg_values(series: np.ndarray, length: int) -> float:
    """Retourne la valeur de la régression linéaire au dernier point"""
    if len(series) < length:
        return np.nan
    y = series[-length:]
    x = np.arange(length)
    try:
        slope, intercept = np.polyfit(x, y, 1)
        return intercept + slope * (length - 1)
    except:
        return np.nan

# ======================
# Fonction principale pour visu_bot.py
# ======================

def fetch_ohlcv(symbol: str, timeframe: str, limit: int = 500) -> pd.DataFrame:
    """
    Récupère les données OHLCV - Compatible avec visu_bot.py
    
    Args:
        symbol (str): Symbole au format Binance (ex: BTCUSDT, DOGEUSDT)
        timeframe (str): Timeframe (1m, 5m, 15m, 1h, 4h, 1d)
        limit (int): Nombre de bougies à récupérer
    
    Returns:
        pd.DataFrame: DataFrame avec colonnes timestamp, open, high, low, close, volume
    """
    
    # Conversion du format de symbole si nécessaire
    ccxt_symbol = symbol.replace('USDT', '/USDT') if '/' not in symbol else symbol
    
    if EXCHANGE_CONFIGURED:
        try:
            print(f"📊 Récupération données réelles: {ccxt_symbol} {timeframe} ({limit} bougies)")
            data = exchange.fetch_ohlcv(ccxt_symbol, timeframe=timeframe, limit=limit)
            df = pd.DataFrame(data, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            print(f"✅ {len(df)} bougies récupérées depuis {df['timestamp'].iloc[0]}")
            return df
        except Exception as e:
            print(f"❌ Erreur API réelle: {e}")
            print("🔄 Basculement vers simulation...")
    
    # Mode simulation si pas d'API ou erreur
    return generate_mock_data(symbol, timeframe, limit)

def generate_mock_data(symbol: str, timeframe: str, limit: int) -> pd.DataFrame:
    """Génère des données de test réalistes"""
    print(f"🎭 Génération données simulées: {symbol} {timeframe} ({limit} bougies)")
    
    # Prix de base selon le symbole
    base_prices = {
        'BTCUSDT': 43000, 'ETHUSDT': 2600, 'DOGEUSDT': 0.08,
        'ADAUSDT': 0.45, 'SOLUSDT': 95, 'BNBUSDT': 310
    }
    
    base_price = base_prices.get(symbol, 1.0)
    
    # Calcul des timestamps
    timeframe_minutes = {'1m': 1, '5m': 5, '15m': 15, '1h': 60, '4h': 240, '1d': 1440}
    interval_minutes = timeframe_minutes.get(timeframe, 5)
    
    now = datetime.now()
    timestamps = []
    for i in range(limit, 0, -1):
        timestamps.append(now - pd.Timedelta(minutes=i * interval_minutes))
    
    # Génération des données avec votre logique de volatilité
    data = []
    current_price = base_price
    
    for i, timestamp in enumerate(timestamps):
        # Tendance sinusoïdale + bruit réaliste
        trend = np.sin(i * 0.02) * 0.1
        noise = np.random.normal(0, 0.02)
        price_change = (trend + noise) * 0.05
        
        current_price *= (1 + price_change)
        
        # OHLC réaliste
        volatility = current_price * 0.003
        open_price = current_price + np.random.normal(0, volatility)
        close_price = current_price + np.random.normal(0, volatility)
        high_price = max(open_price, close_price) + abs(np.random.normal(0, volatility * 0.5))
        low_price = min(open_price, close_price) - abs(np.random.normal(0, volatility * 0.5))
        volume = np.random.uniform(100, 1000)
        
        data.append({
            'timestamp': timestamp,
            'open': round(open_price, 8),
            'high': round(high_price, 8),
            'low': round(low_price, 8),
            'close': round(close_price, 8),
            'volume': round(volume, 2)
        })
    
    df = pd.DataFrame(data)
    print(f"✅ Données simulées générées: prix moyen {df['close'].mean():.6f}")
    return df

def compute_signals(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calcule les signaux selon votre stratégie Trendline Continue SG
    Compatible avec visu_bot.py
    """
    if df.empty:
        return df
    
    print(f"🧮 Calcul signaux avec paramètres: SG_LENGTH={SG_LENGTH}, SLOPE_LENGTH={SLOPE_LENGTH}, SMALEN={SMALEN}")
    
    df = df.copy()
    
    # 1. SG = EMA(close, SG_LENGTH)
    df['sg'] = ema(df['close'], SG_LENGTH)
    
    # 2. slopeSG = linreg(sg, SLOPE_LENGTH, 0) - linreg(sg, SLOPE_LENGTH, 1)
    slope_sg = [np.nan] * len(df)
    for i in range(len(df)):
        if i + 1 >= SLOPE_LENGTH:
            window = df['sg'].values[:i+1]
            val0 = linreg_values(window, SLOPE_LENGTH)
            
            if i >= SLOPE_LENGTH:
                window_prev = df['sg'].values[:i]
                val1 = linreg_values(window_prev, SLOPE_LENGTH)
            else:
                val1 = np.nan
                
            if not np.isnan(val0) and not np.isnan(val1):
                slope_sg[i] = val0 - val1
    
    df['slopeSG'] = slope_sg
    
    # 3. trend (variable persistante)
    trend = [np.nan] * len(df)
    for i in range(len(df)):
        if i == 0:
            trend[i] = df['sg'].iloc[0] if not pd.isna(df['sg'].iloc[0]) else df['close'].iloc[0]
        else:
            inc = df['slopeSG'].iloc[i] if not pd.isna(df['slopeSG'].iloc[i]) else 0.0
            trend[i] = trend[i-1] + inc
    
    df['trend'] = trend
    
    # 4. trendline = SMA(trend, SMALEN)
    df['trendline'] = sma(pd.Series(df['trend']), SMALEN)
    
    # 5. slopeBlue = différence de trendline
    df['slopeBlue'] = df['trendline'] - df['trendline'].shift(1)
    
    # 6. minMove = pourcentage du prix
    df['minMove'] = df['close'] * SENS
    
    # 7. Conditions de signal (vos conditions originales)
    df['longCond'] = ((df['slopeBlue'] > df['minMove']) & 
                      (df['slopeBlue'].shift(1) <= df['minMove'])).fillna(False)
    
    df['shortCond'] = ((df['slopeBlue'] < -df['minMove']) & 
                       (df['slopeBlue'].shift(1) >= -df['minMove'])).fillna(False)
    
    # Statistiques
    buy_signals = df['longCond'].sum()
    sell_signals = df['shortCond'].sum()
    print(f"📈 Signaux calculés: {buy_signals} achats, {sell_signals} ventes")
    
    return df

# ======================
# Fonctions Telegram (optionnelles)
# ======================

def send_telegram(text: str):
    """Envoie un message Telegram si configuré"""
    if not CCXT_AVAILABLE or not TELEGRAM_TOKEN:
        print(f"📱 Telegram: {text}")
        return
        
    try:
        telegram_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        requests.post(telegram_url, data={"chat_id": TELEGRAM_CHAT_ID, "text": text})
        print(f"📱 Telegram envoyé: {text}")
    except Exception as e:
        print(f"❌ Erreur Telegram: {e}")

# ======================
# Bot de trading original (optionnel)
# ======================

def run_bot():
    """Votre bot de trading original"""
    if not EXCHANGE_CONFIGURED:
        print("❌ Exchange non configuré - Impossible de lancer le bot de trading")
        return
    
    print('🤖 Démarrage du bot de trading...')
    send_telegram(f"🚀 Bot de trading démarré sur {SYMBOL}")
    
    position = 0  # 0 flat, 1 long, -1 short
    entry_price = None
    required_bars = max(SG_LENGTH, SLOPE_LENGTH, SMALEN) + 5

    while True:
        try:
            df = fetch_ohlcv(SYMBOL.replace('USDT', '/USDT'), TIMEFRAME, limit=required_bars + 50)
            df = compute_signals(df)

            if len(df) < 2:
                print("❌ Pas assez de données")
                time.sleep(POLL_SECONDS)
                continue

            last = df.iloc[-1]
            prev = df.iloc[-2]
            confirmed = prev  # On utilise la barre précédente comme confirmée

            if confirmed['longCond'] and position <= 0:
                # Clôture short si existante
                if position == -1 and entry_price is not None:
                    pnl = entry_price - confirmed['close']
                    send_telegram(f"❌ Short fermé à {confirmed['close']:.6f} — PnL = {pnl:.6f} {SYMBOL}")
                    print(f"Close short: PnL={pnl:.6f}")

                position = 1
                entry_price = confirmed['close']
                send_telegram(f"✅ Signal ACHAT à {entry_price:.6f} — {SYMBOL} — {TIMEFRAME}")
                print(f"BUY @ {entry_price:.6f}")

            elif confirmed['shortCond'] and position >= 0:
                # Clôture long si existante
                if position == 1 and entry_price is not None:
                    pnl = confirmed['close'] - entry_price
                    send_telegram(f"❌ Long fermé à {confirmed['close']:.6f} — PnL = {pnl:.6f} {SYMBOL}")
                    print(f"Close long: PnL={pnl:.6f}")

                position = -1
                entry_price = confirmed['close']
                send_telegram(f"🚨 Signal VENTE à {entry_price:.6f} — {SYMBOL} — {TIMEFRAME}")
                print(f"SELL @ {entry_price:.6f}")

        except Exception as e:
            print(f"❌ Erreur boucle principale: {e}")
            send_telegram(f"⚠️ Erreur bot: {e}")

        time.sleep(POLL_SECONDS)

# ======================
# Fonctions de test et débogage
# ======================

def test_strategy():
    """Test rapide de la stratégie"""
    print("🧪 Test de la stratégie Trendline Continue SG")
    print("=" * 50)
    
    # Test avec différents symboles
    test_symbols = ['BTCUSDT', 'ETHUSDT', 'DOGEUSDT']
    
    for symbol in test_symbols:
        print(f"\n🔍 Test {symbol}:")
        try:
            df = fetch_ohlcv(symbol, TIMEFRAME, 200)
            df_signals = compute_signals(df)
            
            print(f"Prix actuel: {df_signals['close'].iloc[-1]:.6f}")
            print(f"SG (EMA): {df_signals['sg'].iloc[-1]:.6f}")
            print(f"Trendline: {df_signals['trendline'].iloc[-1]:.6f}")
            print(f"Dernier signal: {'LONG' if df_signals['longCond'].iloc[-1] else 'SHORT' if df_signals['shortCond'].iloc[-1] else 'AUCUN'}")
            
        except Exception as e:
            print(f"❌ Erreur test {symbol}: {e}")
    
    print(f"\n✅ Tests terminés")

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == 'test':
            test_strategy()
        elif sys.argv[1] == 'bot':
            run_bot()
        else:
            print("Usage: python live_bot.py [test|bot]")
    else:
        print("🎯 Module live_bot.py prêt pour intégration dashboard")
        print("💡 Utilisations possibles:")
        print("  - python live_bot.py test  # Test de la stratégie")
        print("  - python live_bot.py bot   # Lancer le bot de trading")
        print("  - import depuis visu_bot.py pour le dashboard web")
        print(f"📊 Configuration: CCXT={CCXT_AVAILABLE}, Exchange={EXCHANGE_CONFIGURED}")