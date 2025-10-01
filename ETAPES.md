# 1) Priorités — ordre d’implémentation (faites ça dans cet ordre)

1. **Sécurité & config** : `.env`, `config.py`, chiffrement Fernet.
2. **DB minimal & users** : `database.py` + table users + création d’un admin.
3. **Auth** : login JWT, rate-limit basique.
4. **Routes placeholders** : `get_portfolio`, `get_trades`, `submit_order` (stubs appelables).
5. **DataManager / OrderManager** : stubs qui appellent ccxt (ou que tu remplaceras).
6. **Frontend AJAX** : `main.js` qui récupère `/api/portfolio`.
7. **Tests** : vérifier login 401, endpoint `/api/portfolio` retourne mock.
8. **Remplir avec ton code métier** (DataManager, ChartBuilder).
9. Optionnel : logging, UI improvements, real encryption for DB file if besoin (sqlcipher).

---

# 2) Fichiers essentiels (copier-coller)

## `.env.example`

```
# .env.example -> copy to .env and fill
JWT_SECRET=change_me_super_secret
FERNET_KEY=change_me_base64_32bytes
ADMIN_USER=admin
ADMIN_PASSWORD=adminpass
DATABASE_URL=sqlite:///./lilux.db
```

* `FERNET_KEY` : génère-la avec `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`

---

## `requirements.txt`

```
fastapi
uvicorn[standard]
python-multipart
jinja2
aiofiles
python-jose[cryptography]
bcrypt
cryptography
pydantic
sqlalchemy
databases
ccxt
requests
pytest
httpx
```

(adapte selon tes libs réelles)

---

## `backend/config.py`

```python
import os
from pydantic import BaseSettings

class Settings(BaseSettings):
    jwt_secret: str
    fernet_key: str
    database_url: str
    admin_user: str = "admin"
    admin_password: str = "admin"
    class Config:
        env_file = ".env"

settings = Settings()
```

---

## `backend/database.py`

Simple SQLite via SQLAlchemy + helper pour stocker api keys chiffrées (varchar).

```python
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Text
from sqlalchemy.engine import Engine
from sqlalchemy.sql import select
from backend.config import settings
from cryptography.fernet import Fernet

engine: Engine = create_engine(settings.database_url, connect_args={"check_same_thread": False})
metadata = MetaData()

users = Table(
    "users", metadata,
    Column("id", Integer, primary_key=True),
    Column("username", String, unique=True, nullable=False),
    Column("password_hash", String, nullable=False),
    Column("api_key_enc", Text, nullable=True),
    Column("api_secret_enc", Text, nullable=True),
)

def init_db():
    metadata.create_all(engine)

# Helper encrypt/decrypt
fernet = Fernet(settings.fernet_key.encode())

def encrypt_token(plain: str) -> str:
    return fernet.encrypt(plain.encode()).decode()

def decrypt_token(token: str) -> str:
    return fernet.decrypt(token.encode()).decode()
```

---

## `backend/auth.py`

Login + JWT + bcrypt

```python
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from datetime import datetime, timedelta
from jose import jwt
import bcrypt
from backend.config import settings
from backend.database import engine, users, init_db
from sqlalchemy import select

JWT_ALGO = "HS256"
router = APIRouter()

class LoginIn(BaseModel):
    username: str
    password: str

def create_jwt(username: str):
    exp = datetime.utcnow() + timedelta(hours=1)
    return jwt.encode({"sub": username, "exp": exp}, settings.jwt_secret, algorithm=JWT_ALGO)

@router.post("/login")
async def login(payload: LoginIn):
    conn = engine.connect()
    query = select(users).where(users.c.username == payload.username)
    res = conn.execute(query).first()
    if not res:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    pwd_hash = res['password_hash'].encode()
    if not bcrypt.checkpw(payload.password.encode(), pwd_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_jwt(payload.username)
    return {"access_token": token}
```

**Note** : ajoute initialisation admin après `init_db()` (voir run.py).

---

## `backend/routes/dashboard.py`

Stubs requis — les remplaceront par ton code métier.

```python
from fastapi import APIRouter, Depends, HTTPException, Request
from typing import Dict, Any
from backend.database import engine
from jose import jwt
from backend.config import settings
from sqlalchemy import select, text

router = APIRouter()

# simple dependency to check JWT
def get_current_user(request: Request):
    auth = request.headers.get("authorization")
    if not auth:
        raise HTTPException(401, "Missing credentials")
    scheme, token = auth.split()
    payload = jwt.decode(token, settings.jwt_secret, algorithms=["HS256"])
    return payload.get("sub")

@router.get("/api/portfolio")
async def get_portfolio(user = Depends(get_current_user)):
    # TODO: replace mock with DataManager/PortfolioSimulator
    return {
        "user": user,
        "total_usdt": 1000.0,
        "positions": [],
        "pnls": {"realized": 0.0, "unrealized": 0.0}
    }

@router.get("/api/trades")
async def get_trades(user = Depends(get_current_user)):
    # TODO: replace with real trade history
    return {"trades": []}

@router.post("/api/orders")
async def submit_order(payload: Dict[str, Any], user = Depends(get_current_user)):
    # payload expected: {symbol, side, qty, price (optional), sl, tp}
    # TODO: call simulate_order() and/or order_manager.place_order()
    return {"status": "ok", "detail": "Order simulated (replace with real implementation)"}
```

---

## `backend/routes/orders.py`

(empty router or forward to order\_manager). You can leave it minimal; dashboard routes cover API.

---

## `backend/data_manager.py` (stub / exemple ccxt)

```python
import ccxt
from backend.config import settings

def create_exchange(api_key: str, api_secret: str):
    ex = ccxt.binance({
        "apiKey": api_key,
        "secret": api_secret,
        "enableRateLimit": True,
    })
    return ex

def fetch_ohlcv(exchange, symbol="DOGE/USDT", timeframe="5m", limit=500):
    return exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
```

Tu remplaceras `api_key`/`api_secret` par la décryption depuis DB.

---

## `backend/order_manager.py` (stub)

```python
def place_order(exchange, symbol, side, qty, price=None, order_type="market"):
    if order_type == "market":
        return exchange.create_market_order(symbol, side, qty)
    else:
        return exchange.create_limit_order(symbol, side, qty, price)
```

(Handling TP/SL peut être simulé via OCO; adapte selon ccxt / Binance API)

---

## `run.py`

Démarre FastAPI + crée DB + admin par défaut

```python
import uvicorn
from backend.database import init_db, engine, users
import bcrypt
from backend.config import settings
from sqlalchemy import insert

def ensure_admin():
    conn = engine.connect()
    q = users.select().where(users.c.username == settings.admin_user)
    if not conn.execute(q).first():
        pw_hash = bcrypt.hashpw(settings.admin_password.encode(), bcrypt.gensalt())
        stmt = insert(users).values(username=settings.admin_user, password_hash=pw_hash.decode())
        conn.execute(stmt)

if __name__ == "__main__":
    init_db()
    ensure_admin()
    uvicorn.run("backend.main:app", host="0.0.0.0", port=5000, reload=True)
```

---

## `backend/main.py`

Montre l’app FastAPI, templates Jinja2, CORS

```python
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from backend.auth import router as auth_router
from backend.routes import dashboard as dashboard_router

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost", "http://localhost:5000", "http://127.0.0.1:5000"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

templates = Jinja2Templates(directory="frontend/templates")
app.mount("/static", StaticFiles(directory="frontend/static"), name="static")

app.include_router(auth_router)
app.include_router(dashboard_router)
```

---

## `frontend/templates/login.html` (snippet)

```html
<!doctype html>
<html>
<head>
  <link rel="stylesheet" href="/static/css/style.css">
</head>
<body>
  <div class="container">
    <form id="loginForm">
      <input name="username" placeholder="username" />
      <input name="password" placeholder="password" type="password" />
      <button type="submit">Login</button>
    </form>
  </div>
  <script src="/static/js/main.js"></script>
</body>
</html>
```

---

## `frontend/static/js/main.js`

AJAX login + fetch portfolio example

```javascript
document.getElementById("loginForm")?.addEventListener("submit", async (e) => {
  e.preventDefault();
  const form = e.target;
  const username = form.username.value;
  const password = form.password.value;
  const res = await fetch("/login", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({username, password})
  });
  if (res.ok) {
    const data = await res.json();
    localStorage.setItem("jwt", data.access_token);
    // go to dashboard
    window.location = "/dashboard";
  } else {
    alert("Login failed");
  }
});

async function fetchPortfolio() {
  const token = localStorage.getItem("jwt");
  const res = await fetch("/api/portfolio", {
    headers: { "Authorization": `Bearer ${token}` }
  });
  console.log(await res.json());
}

// call for demo
// fetchPortfolio();
```

---

## `frontend/templates/dashboard.html` (snippet)

```html
<!doctype html>
<html>
  <head><link rel="stylesheet" href="/static/css/style.css"></head>
  <body>
    <div class="container">
      <div id="graph">Graph placeholder</div>
      <div id="portfolio">Portfolio placeholder</div>
    </div>
    <script src="/static/js/main.js"></script>
    <script>
      document.addEventListener("DOMContentLoaded", () => fetchPortfolio());
    </script>
  </body>
</html>
```

---

## `tests/test_auth.py`

```python
from fastapi.testclient import TestClient
from backend.main import app

client = TestClient(app)

def test_invalid_login():
    res = client.post("/login", json={"username":"nope","password":"bad"})
    assert res.status_code == 401
```

---

# 3) Checklist & conseils pratiques pour avancer

* [ ] Copier `.env.example`→`.env` et remplir `FERNET_KEY` (générée).
* [ ] `pip install -r requirements.txt`
* [ ] `python run.py` → vérifie que `lilux.db` est créé et admin présent.
* [ ] Tester login via `curl` or UI, récupérer JWT.
* [ ] Tester `/api/portfolio` (doit retourner mock).
* [ ] Brancher progressivement `backend/data_manager.py` en remplaçant mock dans `get_portfolio`.
* [ ] Brancher `order_manager.place_order` dans `submit_order` (ne pas envoyer sur mainnet avant testnet!).
* [ ] Mettre en place tests d’intégration contre Binance Testnet (ccxt/credentials de test).
* [ ] Ajouter sauvegarde chiffrée des clés : stocker `encrypt_token(api_key)` dans `users.api_key_enc`.

---

# 4) Suggestions d’amélioration rapide (après MVP)

* Mettre en place un stockage persistant pour SQLite sur Render (volume).
* Ajouter logs (python `logging`) et rotation d’erreurs.
* Endpoint pour `upload_api_keys` qui chiffre et stocke `api_key`/`secret`.
* Intégrer ChartBuilder pour remplacer `#graph` via Plotly (serve des données via `/api/ohlcv`).
* Tests E2E avec pytest+httpx.

---

# 5) Prochaine étape que je peux faire pour toi maintenant

Je peux :

* Générer les fichiers complets (tous les snippets ci-dessus) en un seul patch prêt à coller, ou
* Implémenter `submit_order()` pour utiliser ccxt + Binance Testnet (exemple concret), ou
* T’aider à écrire le code pour chiffrer/déchiffrer les clés et un endpoint `POST /api/keys` pour les enregistrer.

Dis-moi **quelle action tu veux que j’exécute maintenant** (par ex. : “génère tous les fichiers ci-dessus en un seul bloc prêt à déposer” ou “implémente submit\_order() pour testnet”). Je le fais tout de suite.
