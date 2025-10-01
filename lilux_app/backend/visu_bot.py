"""
visu_bot.py - Module de visualisation adapté pour l'architecture Lilux
Compatible avec live_bot.py dans lilux_app/backend/
"""

import matplotlib
matplotlib.use('Agg')  # Backend non-interactif pour serveur web

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd
import base64
from io import BytesIO
import json
import sys
import os
from datetime import datetime

# Ajouter le chemin du backend pour les imports
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(current_dir)

try:
    from live_bot import fetch_ohlcv, compute_signals, SYMBOL, TIMEFRAME
    LIVE_BOT_AVAILABLE = True
    print("✅ Module live_bot importé avec succès")
except ImportError as e:
    LIVE_BOT_AVAILABLE = False
    print(f"⚠️ Module live_bot non disponible: {e}")
    # Valeurs par défaut si live_bot n'est pas disponible
    SYMBOL = 'BTCUSDT'
    TIMEFRAME = '15m'

def plot_chart_web(df: pd.DataFrame, symbol: str, timeframe: str) -> str:
    """
    Génère un graphique matplotlib et le retourne en base64
    
    Args:
        df: DataFrame avec les données OHLC et signaux
        symbol: Symbole tradé
        timeframe: Intervalle de temps
    
    Returns:
        str: Image encodée en base64
    """
    print(f"🎨 Génération graphique pour {symbol} {timeframe}")
    
    # Configuration matplotlib pour thème sombre
    plt.style.use('dark_background')
    fig, ax = plt.subplots(figsize=(14, 8))
    fig.patch.set_facecolor('#1a1a2e')
    ax.set_facecolor('#1a1a2e')
    
    # Calcul de la largeur des bougies
    if len(df) > 1:
        time_diff = (df['timestamp'].iloc[-1] - df['timestamp'].iloc[0]).total_seconds()
        delta_days = time_diff / (24 * 3600)
        width = max(0.0008 * delta_days / len(df), 0.0001)
    else:
        width = 0.001
    
    # Tracé des bougies OHLC
    for idx, row in df.iterrows():
        if pd.isna(row['open']) or pd.isna(row['close']):
            continue
            
        color = '#00ff88' if row['close'] >= row['open'] else '#ff4757'
        alpha = 0.8
        
        # Ligne haute-basse
        ax.plot([row['timestamp'], row['timestamp']], 
                [row['low'], row['high']], 
                color=color, linewidth=1.5, alpha=alpha)
        
        # Corps de la bougie
        body_height = abs(row['close'] - row['open'])
        body_bottom = min(row['open'], row['close'])
        
        if body_height > 0:
            rect = plt.Rectangle(
                (mdates.date2num(row['timestamp']) - width/2, body_bottom),
                width, body_height,
                facecolor=color, edgecolor=color, alpha=alpha
            )
            ax.add_patch(rect)
        else:
            # Doji - ligne horizontale
            ax.plot([mdates.date2num(row['timestamp']) - width/2, 
                    mdates.date2num(row['timestamp']) + width/2],
                   [row['close'], row['close']], 
                   color=color, linewidth=2)
    
    # Indicateurs techniques
    if 'sg' in df.columns:
        valid_sg = df.dropna(subset=['sg'])
        if not valid_sg.empty:
            ax.plot(valid_sg['timestamp'], valid_sg['sg'], 
                   label='SG (EMA)', color='#00d4ff', linewidth=2.5, alpha=0.9)
    
    if 'trendline' in df.columns:
        valid_trendline = df.dropna(subset=['trendline'])
        if not valid_trendline.empty:
            ax.plot(valid_trendline['timestamp'], valid_trendline['trendline'], 
                   label='Trendline', color='#667eea', linewidth=2.5, alpha=0.9)
    
    # Signaux d'achat et de vente
    if 'longCond' in df.columns:
        buys = df[df['longCond'] == True]
        if not buys.empty:
            ax.scatter(buys['timestamp'], buys['close'], 
                      marker='^', color='#00ff88', s=150, 
                      label='Signal Achat', zorder=10, 
                      edgecolor='white', linewidth=2)
    
    if 'shortCond' in df.columns:
        sells = df[df['shortCond'] == True]
        if not sells.empty:
            ax.scatter(sells['timestamp'], sells['close'], 
                      marker='v', color='#ff4757', s=150, 
                      label='Signal Vente', zorder=10, 
                      edgecolor='white', linewidth=2)
    
    # Configuration des axes et du style
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m %H:%M'))
    
    # Adaptation de l'intervalle selon le timeframe
    if len(df) > 100:
        ax.xaxis.set_major_locator(mdates.HourLocator(interval=max(1, len(df)//20)))
    else:
        ax.xaxis.set_major_locator(mdates.HourLocator(interval=2))
    
    fig.autofmt_xdate(rotation=45)
    
    # Titre et légende
    ax.set_title(f"{symbol} - Analyse Technique ({timeframe})", 
                color='white', fontsize=16, fontweight='bold', pad=20)
    
    # Légende avec style personnalisé
    legend = ax.legend(loc='upper left', framealpha=0.9, 
                      facecolor='#1a1a2e', edgecolor='#667eea',
                      fontsize=11)
    legend.get_frame().set_linewidth(1.5)
    
    # Grille subtile
    ax.grid(True, alpha=0.2, color='#667eea', linestyle='--', linewidth=0.5)
    
    # Style des axes
    ax.tick_params(colors='white', labelsize=10)
    for spine in ax.spines.values():
        spine.set_color('#667eea')
        spine.set_linewidth(1.5)
    
    # Ajustement de la mise en page
    plt.tight_layout()
    
    # Conversion en base64
    buffer = BytesIO()
    plt.savefig(buffer, format='png', dpi=120, bbox_inches='tight', 
                facecolor='#1a1a2e', edgecolor='none', 
                pad_inches=0.2)
    buffer.seek(0)
    
    image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
    plt.close(fig)  # Libération de la mémoire
    
    print(f"✅ Graphique généré avec succès ({len(image_base64)} bytes)")
    return f"data:image/png;base64,{image_base64}"

def generate_mock_data(symbol: str, timeframe: str, limit: int) -> pd.DataFrame:
    """Génère des données de test si live_bot n'est pas disponible"""
    print(f"🎭 Génération données simulées: {symbol} {timeframe} ({limit} bougies)")
    
    import numpy as np
    from datetime import timedelta
    
    # Prix de base selon le symbole
    base_prices = {
        'BTCUSDT': 43000, 'ETHUSDT': 2600, 'DOGEUSDT': 0.08,
        'ADAUSDT': 0.45, 'SOLUSDT': 95, 'BNBUSDT': 310
    }
    
    base_price = base_prices.get(symbol, 1000)
    
    # Calcul des timestamps
    timeframe_minutes = {'1m': 1, '5m': 5, '15m': 15, '1h': 60, '4h': 240, '1d': 1440}
    interval_minutes = timeframe_minutes.get(timeframe, 15)
    
    now = datetime.now()
    timestamps = []
    for i in range(limit, 0, -1):
        timestamps.append(now - timedelta(minutes=i * interval_minutes))
    
    # Génération des données OHLCV
    data = []
    current_price = base_price
    
    for i, timestamp in enumerate(timestamps):
        # Tendance + volatilité
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
    
    # Ajout d'indicateurs basiques pour la démo
    df['sg'] = df['close'].ewm(span=21).mean()
    df['trendline'] = df['close'].rolling(window=50).mean()
    
    # Signaux simples
    df['longCond'] = (df['close'] > df['sg']) & (df['close'].shift(1) <= df['sg'].shift(1))
    df['shortCond'] = (df['close'] < df['sg']) & (df['close'].shift(1) >= df['sg'].shift(1))
    
    print(f"✅ Données simulées générées: prix moyen {df['close'].mean():.6f}")
    return df

def get_chart_data(symbol: str = None, timeframe: str = None, limit: int = 200):
    """
    Fonction principale pour obtenir les données du graphique
    Compatible avec l'architecture Lilux
    """
    # Valeurs par défaut
    current_symbol = symbol or SYMBOL
    current_timeframe = timeframe or TIMEFRAME
    
    print(f"📊 Demande graphique: {current_symbol} {current_timeframe} (limit={limit})")
    
    try:
        # Récupération des données
        if LIVE_BOT_AVAILABLE:
            print("🔄 Utilisation du module live_bot")
            df = fetch_ohlcv(current_symbol, current_timeframe, limit=limit)
            df = compute_signals(df)
        else:
            print("🎭 Utilisation de données simulées")
            df = generate_mock_data(current_symbol, current_timeframe, limit)
        
        if df.empty:
            raise ValueError("Aucune donnée récupérée")
        
        print(f"📈 Données récupérées: {len(df)} lignes")
        
        # Génération du graphique
        image_b64 = plot_chart_web(df, current_symbol, current_timeframe)
        
        # Calcul des statistiques
        last_price = float(df['close'].iloc[-1])
        price_change = 0
        if len(df) > 1:
            price_change = float(df['close'].iloc[-1] - df['close'].iloc[-2])
        
        buy_signals = int(df.get('longCond', pd.Series([])).sum()) if 'longCond' in df.columns else 0
        sell_signals = int(df.get('shortCond', pd.Series([])).sum()) if 'shortCond' in df.columns else 0
        
        stats = {
            'last_price': last_price,
            'price_change': price_change,
            'buy_signals': buy_signals,
            'sell_signals': sell_signals,
            'total_signals': buy_signals + sell_signals
        }
        
        print(f"📊 Stats calculées: prix={last_price:.6f}, change={price_change:.6f}, signaux={buy_signals}/{sell_signals}")
        
        return {
            'success': True,
            'image': image_b64,
            'stats': stats,
            'symbol': current_symbol,
            'timeframe': current_timeframe,
            'data_points': len(df)
        }
        
    except Exception as e:
        print(f"❌ Erreur génération graphique: {e}")
        import traceback
        traceback.print_exc()
        
        return {
            'success': False,
            'error': str(e),
            'image': None,
            'stats': None,
            'symbol': current_symbol,
            'timeframe': current_timeframe
        }

# === Test et debug ===

def test_chart_generation():
    """Test de génération de graphique"""
    print("🧪 Test génération graphique")
    print("=" * 50)
    
    test_params = [
        ('BTCUSDT', '15m'),
        ('ETHUSDT', '1h'),
        ('DOGEUSDT', '5m')
    ]
    
    for symbol, timeframe in test_params:
        print(f"\n🔍 Test {symbol} {timeframe}:")
        result = get_chart_data(symbol, timeframe, 100)
        
        if result['success']:
            stats = result['stats']
            print(f"✅ Succès - Prix: {stats['last_price']:.6f}")
            print(f"   Signaux: {stats['buy_signals']} achats, {stats['sell_signals']} ventes")
            print(f"   Image: {len(result['image'])} caractères")
        else:
            print(f"❌ Erreur: {result['error']}")
    
    print(f"\n✅ Tests terminés")

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        if sys.argv[1] == 'test':
            test_chart_generation()
        else:
            print("Usage: python visu_bot.py [test]")
    else:
        print("🎯 Module visu_bot.py prêt")
        print(f"📊 live_bot disponible: {LIVE_BOT_AVAILABLE}")
        print("💡 Utilisation:")
        print("  - from visu_bot import get_chart_data")
        print("  - chart = get_chart_data('BTCUSDT', '15m', 200)")
        print("  - python visu_bot.py test  # Test complet")