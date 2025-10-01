let isTradingViewInitialized = false;

// ==========================================================
// Lilux Main JS - Version avec intégration visu_bot
// ==========================================================

class LiluxApp {
    constructor() {
        this.token = localStorage.getItem('auth_token');
        // API Base URL - ajusté pour FastAPI
        this.apiBase = 'http://127.0.0.1:8000';
    }

    logout() {
        localStorage.removeItem('auth_token');
        localStorage.removeItem('user_data');
        this.token = null;
        alert("Vous avez été déconnecté.");
        // window.location.href = '/login';
    }

    /**
     * Gère tous les appels à l'API de manière centralisée.
     */
    async apiCall(endpoint, options = {}) {
        const config = {
            headers: { 'Content-Type': 'application/json', ...options.headers },
            ...options
        };
        if (this.token) {
            config.headers['Authorization'] = `Bearer ${this.token}`;
        }
        try {
            const response = await fetch(`${this.apiBase}${endpoint}`, config);
            if (response.status === 401) {
                this.logout();
                return null;
            }
            if (!response.ok) {
                throw new Error(`API Error: ${response.statusText}`);
            }
            return await response.json();
        } catch (error) {
            console.error('API call error:', error);
            throw error;
        }
    }

    // --- Méthodes utilitaires ---
    showLoading(elementId) {
        const el = document.getElementById(elementId);
        if (el) {
            const colSpan = el.closest('table')?.querySelector('thead tr').cells.length || 1;
            el.innerHTML = `<tr><td colspan="${colSpan}">
                <div class="loading-placeholder">
                    <div class="spinner-border text-primary" role="status"><span class="visually-hidden">Chargement...</span></div>
                    <p class="mt-2">Chargement...</p>
                </div>
            </td></tr>`;
        }
    }

    showError(elementId, message) {
        const el = document.getElementById(elementId);
        if (el) {
            const colSpan = el.closest('table')?.querySelector('thead tr').cells.length || 1;
            el.innerHTML = `<tr><td colspan="${colSpan}">
                <div class="alert alert-danger m-3" role="alert">
                    <i class="bi bi-exclamation-triangle-fill me-2"></i>${message}
                </div>
            </td></tr>`;
        }
    }
    
    formatCurrency(amount, currency = 'USDT') {
        const options = { minimumFractionDigits: 2, maximumFractionDigits: amount > 1 ? 2 : 6 };
        return new Intl.NumberFormat('fr-FR', options).format(amount) + ' ' + currency;
    }

    formatDate(dateString) {
        return new Date(dateString).toLocaleString('fr-FR', { dateStyle: 'short', timeStyle: 'short'});
    }
}

// --- Instance globale de l'application ---
const app = new LiluxApp();

// --- Variables globales pour les graphiques et l'état ---
let priceChart, portfolioChart, tradingViewWidget, visuBotChart;
let currentPair = 'BTCUSDT';
let botActive = false;

// --- Initialisation au chargement de la page ---
document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 Lilux Trading Dashboard Initialisation...');
    
    initializeCharts();
    initializeDashboard();
    setupEventListeners();
});

/**
 * Initialise les graphiques Chart.js (Évolution et Répartition).
 */
function initializeCharts() {
    // Graphique d'évolution de la balance
    const priceCtx = document.getElementById('priceChart').getContext('2d');
    priceChart = new Chart(priceCtx, {
        type: 'line',
        data: { 
            labels: [], 
            datasets: [{ 
                label: 'Balance (USDT)', 
                data: [], 
                borderColor: '#00d4ff', 
                backgroundColor: 'rgba(0,212,255,0.1)', 
                borderWidth: 2, 
                fill: true, 
                tension: 0.4 
            }] 
        },
        options: { 
            responsive: true, 
            maintainAspectRatio: false, 
            scales: { 
                x: { ticks: { color: '#a0a0a0' }, grid: { color: 'rgba(255,255,255,0.1)' } }, 
                y: { ticks: { color: '#a0a0a0' }, grid: { color: 'rgba(255,255,255,0.1)' } } 
            }, 
            plugins: { legend: { display: false } } 
        }
    });

    // Graphique de répartition du portfolio
    const portfolioCtx = document.getElementById('portfolioChart').getContext('2d');
    portfolioChart = new Chart(portfolioCtx, {
        type: 'doughnut',
        data: { 
            labels: [], 
            datasets: [{ 
                data: [], 
                backgroundColor: ['#667eea', '#764ba2', '#f093fb', '#f5576c', '#4facfe', '#00f2fe'], 
                borderWidth: 0 
            }] 
        },
        options: { 
            responsive: true, 
            maintainAspectRatio: false, 
            plugins: { 
                legend: { 
                    position: 'bottom', 
                    labels: { 
                        color: '#ffffff', 
                        padding: 20 
                    } 
                } 
            } 
        }
    });

    // Initialisation du conteneur pour le graphique visu_bot
    initializeVisuBotContainer();
}

/**
 * NOUVELLE FONCTION : Initialise le conteneur pour le graphique visu_bot
 */
function initializeVisuBotContainer() {
    // Création d'une nouvelle section dans l'onglet Trading pour le graphique visu_bot
    const tradingPane = document.getElementById('trading');
    if (tradingPane) {
        const existingCard = tradingPane.querySelector('.modern-card');
        if (existingCard) {
            // Ajout du graphique visu_bot avant le graphique TradingView
            const visuBotCard = document.createElement('div');
            visuBotCard.className = 'modern-card mb-4';
            visuBotCard.innerHTML = `
                <div class="card-header bg-transparent border-0 p-3 d-flex justify-content-between align-items-center">
                    <h5 class="mb-0"><i class="bi bi-activity me-2"></i>Analyse Technique - Visu Bot</h5>
                    <div>
                        <button id="refresh-visu-bot" class="btn btn-sm me-2">
                            <i class="bi bi-arrow-clockwise"></i> Actualiser
                        </button>
                        <select id="visu-symbol" class="form-select form-select-sm d-inline-block w-auto me-2">
                            <option value="BTCUSDT" selected>BTC/USDT</option>
                            <option value="ETHUSDT">ETH/USDT</option>
                            <option value="DOGEUSDT">DOGE/USDT</option>
                            <option value="ADAUSDT">ADA/USDT</option>
                        </select>
                        <select id="visu-timeframe" class="form-select form-select-sm d-inline-block w-auto">
                            <option value="1m">1m</option>
                            <option value="5m">5m</option>
                            <option value="15m" selected>15m</option>
                            <option value="1h">1h</option>
                            <option value="4h">4h</option>
                        </select>
                    </div>
                </div>
                <div class="card-body p-3">
                    <div id="visu-bot-container" style="min-height: 400px; position: relative;">
                        <div class="loading-placeholder">
                            <div class="spinner-border text-primary" role="status">
                                <span class="visually-hidden">Chargement...</span>
                            </div>
                            <p class="mt-2">Chargement du graphique d'analyse technique...</p>
                        </div>
                    </div>
                    <div id="visu-bot-stats" class="row mt-3" style="display: none;">
                        <div class="col-md-3">
                            <div class="text-center">
                                <h6 class="text-muted mb-1">Prix Actuel</h6>
                                <span id="current-price" class="h5">-</span>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="text-center">
                                <h6 class="text-muted mb-1">Variation</h6>
                                <span id="price-change" class="h5">-</span>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="text-center">
                                <h6 class="text-muted mb-1">Signaux Achat</h6>
                                <span id="buy-signals" class="h5 text-success">-</span>
                            </div>
                        </div>
                        <div class="col-md-3">
                            <div class="text-center">
                                <h6 class="text-muted mb-1">Signaux Vente</h6>
                                <span id="sell-signals" class="h5 text-danger">-</span>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            existingCard.parentNode.insertBefore(visuBotCard, existingCard);
        }
    }
}

/**
 * Point d'entrée pour charger toutes les données du dashboard.
 */
function initializeDashboard() {
    refreshOverview();
    refreshPortfolio();
    refreshTransactions();
    // Chargement initial du graphique visu_bot
    loadVisuBotChart();
}

/**
 * Met en place les gestionnaires d'événements pour les éléments interactifs.
 */
function setupEventListeners() {
    // S'assure que le graphique TradingView se charge quand on clique sur l'onglet
    const tradingTab = document.getElementById('trading-tab');
    tradingTab.addEventListener('shown.bs.tab', function () {
        if (!isTradingViewInitialized) {
            initTradingViewChart(currentPair, '15m');
            isTradingViewInitialized = true;
        }
        // Chargement du graphique visu_bot si pas encore fait
        if (!visuBotChart) {
            loadVisuBotChart();
        }
    });

    // Sélecteurs pour le graphique TradingView
    document.getElementById('select-symbol').addEventListener('change', e => {
        isTradingViewInitialized = true;
        currentPair = e.target.value;
        initTradingViewChart(currentPair, document.getElementById('select-timeframe').value);
    });
    document.getElementById('select-timeframe').addEventListener('change', e => {
        initTradingViewChart(currentPair, e.target.value);
    });

    // NOUVEAUX ÉVÉNEMENTS : Gestionnaires pour le graphique visu_bot
    const refreshVisuBtn = document.getElementById('refresh-visu-bot');
    if (refreshVisuBtn) {
        refreshVisuBtn.addEventListener('click', () => loadVisuBotChart());
    }

    const visuSymbolSelect = document.getElementById('visu-symbol');
    if (visuSymbolSelect) {
        visuSymbolSelect.addEventListener('change', () => loadVisuBotChart());
    }

    const visuTimeframeSelect = document.getElementById('visu-timeframe');
    if (visuTimeframeSelect) {
        visuTimeframeSelect.addEventListener('change', () => loadVisuBotChart());
    }

    // Bouton pour activer/désactiver le bot
    const botBtn = document.getElementById('toggle-bot');
    botBtn.addEventListener('click', () => {
        botActive = !botActive;
        botBtn.textContent = botActive ? 'LIVE BOT ON' : 'LIVE BOT OFF';
        botBtn.classList.toggle('btn-success', botActive);
        botBtn.classList.toggle('btn-danger', !botActive);
        console.log('Bot status:', botActive);
    });
}

// --- NOUVELLES FONCTIONS pour le graphique visu_bot ---

/**
 * Charge et affiche le graphique généré par visu_bot.py
 */
async function loadVisuBotChart() {
    const container = document.getElementById('visu-bot-container');
    const statsContainer = document.getElementById('visu-bot-stats');
    
    if (!container) return;
    
    // Affichage du loader
    container.innerHTML = `
        <div class="loading-placeholder">
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Chargement...</span>
            </div>
            <p class="mt-2">Génération du graphique d'analyse technique...</p>
        </div>
    `;
    
    if (statsContainer) {
        statsContainer.style.display = 'none';
    }

    try {
        // Récupération des paramètres sélectionnés
        const symbol = document.getElementById('visu-symbol')?.value || 'BTCUSDT';
        const timeframe = document.getElementById('visu-timeframe')?.value || '15m';
        
        console.log(`📊 Chargement du graphique visu_bot: ${symbol} - ${timeframe}`);
        
        // Appel à l'API pour récupérer les données du graphique
        const response = await app.apiCall(`/api/chart/data?symbol=${symbol}&timeframe=${timeframe}&limit=200`);
        
        if (response && response.success) {
            // Affichage de l'image générée par matplotlib
            if (response.image) {
                container.innerHTML = `
                    <div class="text-center">
                        <img src="${response.image}" 
                             class="img-fluid rounded" 
                             alt="Graphique d'analyse technique ${symbol}"
                             style="max-width: 100%; height: auto; background: #1a1a2e;">
                    </div>
                `;
            }
            
            // Mise à jour des statistiques
            if (response.stats && statsContainer) {
                updateVisuBotStats(response.stats);
                statsContainer.style.display = 'block';
            }
            
            console.log('✅ Graphique visu_bot chargé avec succès');
            
        } else {
            throw new Error(response?.error || 'Erreur inconnue');
        }
        
    } catch (error) {
        console.error('❌ Erreur lors du chargement du graphique visu_bot:', error);
        
        // Affichage d'un message d'erreur utilisateur
        container.innerHTML = `
            <div class="alert alert-warning text-center" role="alert">
                <i class="bi bi-exclamation-triangle me-2"></i>
                <strong>Service temporairement indisponible</strong><br>
                <small>Le module d'analyse technique n'est pas disponible actuellement.</small><br>
                <button class="btn btn-sm btn-outline-warning mt-2" onclick="loadVisuBotChart()">
                    <i class="bi bi-arrow-clockwise"></i> Réessayer
                </button>
            </div>
        `;
    }
}

/**
 * Met à jour les statistiques du graphique visu_bot
 */
function updateVisuBotStats(stats) {
    if (!stats) return;
    
    const currentPriceEl = document.getElementById('current-price');
    const priceChangeEl = document.getElementById('price-change');
    const buySignalsEl = document.getElementById('buy-signals');
    const sellSignalsEl = document.getElementById('sell-signals');
    
    if (currentPriceEl) {
        currentPriceEl.textContent = app.formatCurrency(stats.last_price);
    }
    
    if (priceChangeEl) {
        const changeClass = stats.price_change >= 0 ? 'text-success' : 'text-danger';
        const changeSymbol = stats.price_change >= 0 ? '+' : '';
        priceChangeEl.textContent = `${changeSymbol}${stats.price_change.toFixed(2)}`;
        priceChangeEl.className = `h5 ${changeClass}`;
    }
    
    if (buySignalsEl) {
        buySignalsEl.textContent = stats.buy_signals || 0;
    }
    
    if (sellSignalsEl) {
        sellSignalsEl.textContent = stats.sell_signals || 0;
    }
}

// --- Fonctions de chargement et de rendu des données (inchangées) ---

async function refreshOverview() {
    try {
        const data = await app.apiCall('/api/binance/overview');
        document.getElementById('totalBalance').textContent = `${data.total_balance_usd.toLocaleString('fr-FR', { minimumFractionDigits: 2 })}`;
        document.getElementById('totalProfit').textContent = `${data.total_profit_usd.toLocaleString('fr-FR', { minimumFractionDigits: 2 })}`;
        document.getElementById('totalTrades').textContent = data.trades_today;
        document.getElementById('successRate').textContent = `${data.winrate.toFixed(1)}%`;
        
        updateTopList('topGainers', data.top_gainers, true);
        updateTopList('topLosers', data.top_losers, false);

        if (data.balance_history && data.balance_history.length > 0) {
            priceChart.data.labels = data.balance_history.map(p => new Date(p.time).toLocaleDateString('fr-FR'));
            priceChart.data.datasets[0].data = data.balance_history.map(p => p.value);
            priceChart.update();
        }
    } catch (e) {
        console.error('Erreur chargement overview:', e);
    }
}

async function refreshPortfolio() {
    const containerId = 'portfolioTableBody';
    app.showLoading(containerId);
    try {
        const data = await app.apiCall('/api/binance/portfolio');
        
        portfolioChart.data.labels = data.portfolio.map(a => a.asset);
        portfolioChart.data.datasets[0].data = data.portfolio.map(a => a.value_usdt);
        portfolioChart.update();

        renderPortfolioTable(data.portfolio);

    } catch (e) {
        app.showError(containerId, 'Erreur lors du chargement du portfolio.');
    }
}

async function refreshTransactions() {
    const containerId = 'transactionsTableBody';
    app.showLoading(containerId);
    try {
        const data = await app.apiCall('/api/binance/transactions');
        renderTransactionsTable(data.transactions);
    } catch (e) {
        app.showError(containerId, 'Erreur lors du chargement des transactions.');
    }
}

// --- Fonctions de rendu HTML (inchangées) ---

function updateTopList(containerId, list, isUp) {
    const container = document.getElementById(containerId);
    if (!container) return;
    container.innerHTML = list.map(c => `
        <div class="d-flex justify-content-between align-items-center mb-2">
            <span>${c.symbol}</span>
            <span class="${isUp ? 'price-up' : 'price-down'}">${parseFloat(c.priceChangePercent).toFixed(2)}%</span>
        </div>
    `).join('');
}

function renderPortfolioTable(portfolioData) {
    const tbody = document.getElementById('portfolioTableBody');
    if (!tbody) return;
    if (portfolioData.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="text-center p-4">Aucun actif dans le portfolio.</td></tr>';
        return;
    }
    tbody.innerHTML = portfolioData.map(asset => {
        const change = asset.change24h || 0;
        const pnl = asset.pnl || 0;
        const changeClass = change >= 0 ? 'price-up' : 'price-down';
        const pnlClass = pnl >= 0 ? 'price-up' : 'price-down';
        return `
            <tr>
                <td>${asset.asset}</td>
                <td>${asset.qty.toFixed(6)}</td>
                <td>${app.formatCurrency(asset.price, 'USDT')}</td>
                <td>${app.formatCurrency(asset.value_usdt, 'USDT')}</td>
                <td class="${changeClass}">${change.toFixed(2)}%</td>
                <td class="${pnlClass}">${app.formatCurrency(pnl, 'USDT')}</td>
            </tr>
        `;
    }).join('');
}

function renderTransactionsTable(transactionsData) {
    const tbody = document.getElementById('transactionsTableBody');
    if (!tbody) return;
    if (transactionsData.length === 0) {
        tbody.innerHTML = '<tr><td colspan="7" class="text-center p-4">Aucune transaction récente.</td></tr>';
        return;
    }
    tbody.innerHTML = transactionsData.map(trade => {
        const typeClass = trade.type.toLowerCase() === 'achat' ? 'bg-success' : 'bg-danger';
        const statusMap = {
            'Complété': 'bg-success',
            'En attente': 'bg-warning',
            'Annulé': 'bg-secondary'
        };
        return `
            <tr>
                <td>${app.formatDate(trade.date)}</td>
                <td>${trade.pair}</td>
                <td><span class="badge ${typeClass}">${trade.type.toUpperCase()}</span></td>
                <td>${trade.quantity}</td>
                <td>${app.formatCurrency(trade.price)}</td>
                <td>${app.formatCurrency(trade.total)}</td>
                <td><span class="badge ${statusMap[trade.status]}">${trade.status}</span></td>
            </tr>
        `;
    }).join('');
}

// --- Fonctions TradingView (inchangées) ---

function initTradingViewChart(symbol = 'BTCUSDT', interval = '15') {
    const container = document.getElementById('tradingview_chart');
    if (!container) return;
    
    if (tradingViewWidget) {
        try {
            tradingViewWidget.remove();
            tradingViewWidget = null;
        } catch(e) {
            console.error("Erreur lors de la suppression du widget TV", e);
            container.innerHTML = '';
        }
    }
    tradingViewWidget = new TradingView.widget({
        container_id: 'tradingview_chart',
        width: '100%',
        height: 450,
        symbol: `BINANCE:${symbol}`,
        interval: interval,
        timezone: "Europe/Paris",
        theme: "dark",
        style: "1",
        locale: "fr",
        toolbar_bg: "#f1f3f6",
        enable_publishing: false,
        allow_symbol_change: true,
        hide_top_toolbar: true,
        save_image: false
    });
}