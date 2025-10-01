# Fichier : lilux_app/routes/dashboard.py

from fastapi import APIRouter, Request, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from datetime import datetime, timedelta
import jwt
import os
import sys

# Ajouter le chemin du backend pour les imports
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# Imports des modules existants
from ..auth import get_current_user
from ..data_manager import DataManager 
from .. import binance_service as bs

# Import du module visu_bot (avec gestion d'erreur)
try:
    from ..visu_bot import get_chart_data
    VISU_BOT_AVAILABLE = True
    print("✅ Module visu_bot chargé avec succès")
except ImportError as e:
    VISU_BOT_AVAILABLE = False
    print(f"⚠️ Module visu_bot non disponible: {e}")

# --- Initialisation ---
router = APIRouter()
templates = Jinja2Templates(directory="lilux_app/frontend/templates")
dm = DataManager()

# Configuration JWT
SECRET_KEY = "lilux_secret_key_2024_change_this_in_production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480

# --- Modèles Pydantic ---
class LoginSchema(BaseModel):
    username: str
    password: str

class OrderSchema(BaseModel):
    pair: str
    type: str
    amount: float
    price: float

# === ROUTE DE LOGIN ===
@router.post("/api/login")
async def login(credentials: LoginSchema):
    """Route de connexion"""
    if credentials.username == "admin" and credentials.password == "admin123":
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        token_data = {
            "sub": credentials.username,
            "exp": expire,
            "id": 1,
            "username": credentials.username
        }
        token = jwt.encode(token_data, SECRET_KEY, algorithm=ALGORITHM)
        return {
            "token": token,
            "username": credentials.username,
            "message": "Connexion réussie"
        }
    else:
        raise HTTPException(status_code=401, detail="Identifiants incorrects")

# === Routes principales de l'interface ===

@router.get("/dashboard", response_class=HTMLResponse)
async def serve_dashboard(request: Request):
    """Sert la page principale du dashboard en utilisant un template Jinja2."""
    return templates.TemplateResponse("dashboard.html", {"request": request})

# === NOUVELLES ROUTES pour le graphique visu_bot ===

@router.get("/api/chart/data")
async def get_chart_api(
    symbol: str = Query(default="BTCUSDT"),
    timeframe: str = Query(default="15m"),
    limit: int = Query(default=200, le=1000)
):
    """API pour récupérer les données du graphique de trading"""
    print(f"🎯 Requête graphique: {symbol} {timeframe} (limit={limit})")
    
    if not VISU_BOT_AVAILABLE:
        return JSONResponse(
            status_code=503,
            content={
                "success": False,
                "error": "Module visu_bot non disponible",
                "message": "Vérifiez que live_bot.py et visu_bot.py sont présents"
            }
        )
    
    try:
        chart_data = get_chart_data(symbol=symbol, timeframe=timeframe, limit=limit)
        print(f"✅ Graphique généré avec succès pour {symbol}")
        return JSONResponse(content=chart_data)
    except Exception as e:
        print(f"❌ Erreur génération graphique: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "success": False,
                "error": str(e),
                "message": "Erreur lors de la génération du graphique"
            }
        )

@router.post("/api/chart/update")
async def update_chart(chart_request: dict):
    """API POST pour mettre à jour le graphique avec de nouveaux paramètres"""
    return await get_chart_api(
        symbol=chart_request.get('symbol', 'BTCUSDT'),
        timeframe=chart_request.get('timeframe', '15m'),
        limit=chart_request.get('limit', 200)
    )

# === Routes de l'API pour l'authentification et les données utilisateur ===

@router.get("/api/me")
async def get_me(current_user: dict = Depends(get_current_user)):
    """Route sécurisée qui renvoie les infos de l'utilisateur connecté."""
    return current_user

@router.get("/api/portfolio")
async def get_portfolio(current_user: dict = Depends(get_current_user)):
    """Récupère le portfolio de l'utilisateur connecté."""
    user_id = current_user.get("id")
    if not user_id:
        raise HTTPException(status_code=403, detail="User ID not found in token")
    return dm.get_user_portfolio(user_id)

@router.get("/api/trades")
async def get_trades(limit: int = 10, current_user: dict = Depends(get_current_user)):
    """Récupère l'historique des trades de l'utilisateur connecté."""
    user_id = current_user.get("id")
    return dm.get_trade_history(user_id, limit)

@router.post("/api/orders")
async def submit_order(order: OrderSchema, current_user: dict = Depends(get_current_user)):
    """Soumet un nouvel ordre d'achat ou de vente."""
    user_id = current_user.get("id")
    return dm.place_order(user_id, order.dict())

# === Routes de l'API pour les données de marché Binance ===

@router.get("/api/binance/overview")
async def api_overview():
    """Route unique et efficace pour l'aperçu du marché."""
    try:
        gainers, losers = bs.top_gainers_losers()
        return {
            "total_balance_usd": bs.total_balance_usdt(),
            "total_profit_usd": 1250.42,
            "trades_today": 15,
            "winrate": 75.6,
            "top_gainers": gainers,
            "top_losers": losers,
            "balance_history": [
                {"time": "2024-01-01T00:00:00Z", "value": 10000},
                {"time": "2024-01-02T00:00:00Z", "value": 10250},
                {"time": "2024-01-03T00:00:00Z", "value": 12450}
            ]
        }
    except Exception as e:
        print(f"❌ Erreur api_overview: {e}")
        # Données demo en cas d'erreur
        return {
            "total_balance_usd": 12450.67,
            "total_profit_usd": 1250.42,
            "trades_today": 15,
            "winrate": 75.6,
            "top_gainers": [
                {"symbol": "BTCUSDT", "priceChangePercent": "3.45"},
                {"symbol": "ETHUSDT", "priceChangePercent": "2.87"}
            ],
            "top_losers": [
                {"symbol": "DOGEUSDT", "priceChangePercent": "-2.11"},
                {"symbol": "DOTUSDT", "priceChangePercent": "-1.87"}
            ],
            "balance_history": []
        }

@router.get("/api/binance/portfolio")
async def api_portfolio():
    """Cette route est publique et renvoie un portfolio global ou d'exemple."""
    try:
        return {"portfolio": bs.portfolio()}
    except Exception as e:
        print(f"❌ Erreur api_portfolio: {e}")
        # Portfolio demo
        return {
            "portfolio": [
                {
                    "asset": "BTC",
                    "qty": 0.5,
                    "price": 43500.0,
                    "value_usdt": 21750.0,
                    "change24h": 2.34,
                    "pnl": 1250.0
                },
                {
                    "asset": "ETH",
                    "qty": 5.2,
                    "price": 2650.0,
                    "value_usdt": 13780.0,
                    "change24h": 1.87,
                    "pnl": 780.0
                }
            ]
        }

@router.get("/api/binance/market")
async def api_market(symbol: str):
    """Récupère le prix actuel pour un symbole donné."""
    try:
        return bs.get_market_price(symbol)
    except Exception as e:
        print(f"❌ Erreur api_market: {e}")
        # Prix demo
        demo_prices = {
            "BTCUSDT": {"price": 43500.0, "change": 2.34},
            "ETHUSDT": {"price": 2650.0, "change": 1.87},
            "DOGEUSDT": {"price": 0.08, "change": -0.95}
        }
        return demo_prices.get(symbol, {"price": 1.0, "change": 0.0})

# === Route de santé ===
@router.get("/api/health")
async def health_check():
    """Vérification de l'état de l'application"""
    return {
        "status": "healthy",
        "visu_bot_available": VISU_BOT_AVAILABLE,
        "version": "1.0.0"
    }