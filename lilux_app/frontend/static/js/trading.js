document.addEventListener('DOMContentLoaded', () => {
    const startBtn = document.getElementById('startBot');
    const stopBtn  = document.getElementById('stopBot');
    const pairSel  = document.getElementById('pairSelector');

    startBtn.onclick = async () => {
        const pair = pairSel.value;
        await fetch('/api/binance/bot/start', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({symbol: pair})
        });
        alert(`Bot lancé sur ${pair}`);
    };

    stopBtn.onclick = async () => {
        await fetch('/api/binance/bot/stop', {method: 'POST'});
        alert('Bot arrêté');
    };

    // Widget TradingView
    new TradingView.widget({
        autosize: true,
        symbol: "BINANCE:" + pairSel.value,
        interval: "1",
        timezone: "Etc/UTC",
        theme: "dark",
        container_id: "tv_chart_container"
    });

    pairSel.onchange = () => location.reload(); // recharge la page sur nouvelle paire
});

// Fonction pour charger le graphique visu_bot
async function loadVisuBotChart() {
    const container = document.getElementById('visu-bot-container');
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
    
    try {
        const symbol = document.getElementById('visu-symbol')?.value || 'BTCUSDT';
        const timeframe = document.getElementById('visu-timeframe')?.value || '15m';
        
        console.log(`Chargement du graphique: ${symbol} - ${timeframe}`);
        
        const response = await fetch(`/api/chart/data?symbol=${symbol}&timeframe=${timeframe}&limit=200`);
        const data = await response.json();
        
        if (data.success && data.image) {
            container.innerHTML = `
                <div class="text-center">
                    <img src="${data.image}" 
                         class="img-fluid rounded" 
                         alt="Graphique d'analyse technique ${symbol}"
                         style="max-width: 100%; height: auto; background: #1a1a2e;">
                </div>
            `;
            
            // Afficher les stats si disponibles
            if (data.stats) {
                updateVisuBotStats(data.stats);
                const statsContainer = document.getElementById('visu-bot-stats');
                if (statsContainer) statsContainer.style.display = 'block';
            }
        } else {
            throw new Error(data.error || 'Erreur inconnue');
        }
        
    } catch (error) {
        console.error('Erreur chargement graphique:', error);
        container.innerHTML = `
            <div class="alert alert-warning text-center" role="alert">
                <i class="bi bi-exclamation-triangle me-2"></i>
                <strong>Service temporairement indisponible</strong><br>
                <small>${error.message}</small><br>
                <button class="btn btn-sm btn-outline-warning mt-2" onclick="loadVisuBotChart()">
                    Réessayer
                </button>
            </div>
        `;
    }
}

function updateVisuBotStats(stats) {
    const currentPriceEl = document.getElementById('current-price');
    const priceChangeEl = document.getElementById('price-change');
    const buySignalsEl = document.getElementById('buy-signals');
    const sellSignalsEl = document.getElementById('sell-signals');
    
    if (currentPriceEl) currentPriceEl.textContent = stats.last_price?.toFixed(6) || '-';
    if (priceChangeEl) {
        const changeClass = (stats.price_change || 0) >= 0 ? 'text-success' : 'text-danger';
        const changeSymbol = (stats.price_change || 0) >= 0 ? '+' : '';
        priceChangeEl.textContent = `${changeSymbol}${(stats.price_change || 0).toFixed(2)}`;
        priceChangeEl.className = `h5 ${changeClass}`;
    }
    if (buySignalsEl) buySignalsEl.textContent = stats.buy_signals || 0;
    if (sellSignalsEl) sellSignalsEl.textContent = stats.sell_signals || 0;
}

// Extension pour trading.js - Widget TradingView amélioré

function initializeTradingViewWidget(symbol = 'BTCUSDT') {
    const container = document.getElementById('tv_chart_container');
    if (!container) {
        console.warn('Conteneur TradingView non trouvé');
        return;
    }

    try {
        console.log(`Initialisation TradingView avancé: ${symbol}`);
        
        // Supprimer l'ancien widget
        if (tradingViewWidget) {
            try {
                tradingViewWidget.remove();
            } catch (e) {
                console.warn('Erreur suppression ancien widget:', e);
            }
        }

        // Configuration avancée du widget
        tradingViewWidget = new TradingView.widget({
            // Dimensions
            autosize: true,
            width: "100%",
            height: 600,
            
            // Marché et symbole
            symbol: "BINANCE:" + symbol,
            interval: "15", // Timeframe par défaut
            
            // Localisation
            timezone: "Europe/Paris",
            locale: "fr",
            
            // Apparence
            theme: "dark",
            style: "1", // 0=barres, 1=bougies, 2=ligne, 3=aire
            
            // Container
            container_id: "tv_chart_container",
            
            // Interface utilisateur
            toolbar_bg: "#1a1a2e",
            hide_top_toolbar: false, // Permet d'accéder aux outils
            hide_legend: false,
            hide_side_toolbar: false, // Barre latérale avec outils de dessin
            
            // Fonctionnalités avancées
            allow_symbol_change: true, // Permet de changer le symbole
            details: true, // Affiche les détails du symbole
            hotlist: true, // Liste des symboles populaires
            calendar: true, // Calendrier économique
            news: ["headlines"], // Actualités
            
            // Outils et indicateurs
            studies_overrides: {}, // Personnalisation des indicateurs
            disabled_features: [
                // Désactiver certaines fonctionnalités si nécessaire
                // "header_symbol_search",
                // "symbol_search_hot_key",
            ],
            enabled_features: [
                "study_templates", // Templates d'indicateurs
                "side_toolbar_in_fullscreen_mode",
                "header_in_fullscreen_mode",
                "remove_library_container_border",
                "chart_property_page_style",
                "show_chart_property_page",
            ],
            
            // Indicateurs par défaut
            studies: [
                // Vous pouvez ajouter des indicateurs automatiquement
                // "RSI@tv-basicstudies",
                // "MACD@tv-basicstudies",
                // "BB@tv-basicstudies", // Bollinger Bands
            ],
            
            // Watchlist personnalisée
            watchlist: [
                "BINANCE:BTCUSDT",
                "BINANCE:ETHUSDT", 
                "BINANCE:ADAUSDT",
                "BINANCE:DOGEUSDT",
                "BINANCE:SOLUSDT",
                "BINANCE:BNBUSDT",
                "BINANCE:MATICUSDT",
                "BINANCE:DOTUSDT",
                "BINANCE:LINKUSDT",
                "BINANCE:UNIUSDT"
            ],
            
            // Sauvegarde des paramètres
            save_image: true,
            loading_screen: { backgroundColor: "#1a1a2e", foregroundColor: "#667eea" },
            
            // Callbacks personnalisés
            overrides: {
                // Personnalisation des couleurs
                "paneProperties.background": "#1a1a2e",
                "paneProperties.vertGridProperties.color": "#363c4e",
                "paneProperties.horzGridProperties.color": "#363c4e",
                "symbolWatermarkProperties.transparency": 90,
                "scalesProperties.textColor": "#AAA",
                
                // Bougies
                "mainSeriesProperties.candleStyle.upColor": "#00ff88",
                "mainSeriesProperties.candleStyle.downColor": "#ff4757",
                "mainSeriesProperties.candleStyle.drawWick": true,
                "mainSeriesProperties.candleStyle.drawBorder": true,
                "mainSeriesProperties.candleStyle.borderColor": "#378658",
                "mainSeriesProperties.candleStyle.borderUpColor": "#00ff88",
                "mainSeriesProperties.candleStyle.borderDownColor": "#ff4757",
                "mainSeriesProperties.candleStyle.wickUpColor": "#00ff88",
                "mainSeriesProperties.candleStyle.wickDownColor": "#ff4757",
                
                // Volume
                "volumePaneSize": "medium",
                "mainSeriesProperties.showCountdown": true,
            }
        });

        console.log('TradingView widget avancé initialisé');
    } catch (error) {
        console.error('Erreur TradingView:', error);
        container.innerHTML = '<div class="alert alert-warning">Erreur chargement TradingView</div>';
    }
}

// Fonction pour ajouter des indicateurs personnalisés
function addCustomIndicator(indicatorName) {
    if (!tradingViewWidget) {
        console.warn('Widget TradingView non initialisé');
        return;
    }
    
    try {
        tradingViewWidget.chart().createStudy(indicatorName, false, false);
        console.log(`Indicateur ajouté: ${indicatorName}`);
        showNotification(`Indicateur ${indicatorName} ajouté`, 'success');
    } catch (error) {
        console.error('Erreur ajout indicateur:', error);
        showNotification('Erreur lors de l\'ajout de l\'indicateur', 'error');
    }
}

// Fonction pour changer le timeframe
function changeTimeframe(interval) {
    if (!tradingViewWidget) {
        console.warn('Widget TradingView non initialisé');
        return;
    }
    
    try {
        tradingViewWidget.chart().setResolution(interval);
        console.log(`Timeframe changé: ${interval}`);
        showNotification(`Timeframe changé: ${interval}`, 'info');
    } catch (error) {
        console.error('Erreur changement timeframe:', error);
    }
}

// Ajout des contrôles dans l'interface
function addTradingViewControls() {
    const controlsHTML = `
        <div class="tradingview-controls mb-3">
            <div class="row">
                <div class="col-md-4">
                    <label class="form-label small text-muted">Cryptomonnaies populaires</label>
                    <select id="tv-symbol-select" class="form-select form-select-sm">
                        <option value="BTCUSDT">Bitcoin (BTC/USDT)</option>
                        <option value="ETHUSDT">Ethereum (ETH/USDT)</option>
                        <option value="ADAUSDT">Cardano (ADA/USDT)</option>
                        <option value="DOGEUSDT">Dogecoin (DOGE/USDT)</option>
                        <option value="SOLUSDT">Solana (SOL/USDT)</option>
                        <option value="BNBUSDT">Binance Coin (BNB/USDT)</option>
                        <option value="MATICUSDT">Polygon (MATIC/USDT)</option>
                        <option value="DOTUSDT">Polkadot (DOT/USDT)</option>
                        <option value="LINKUSDT">Chainlink (LINK/USDT)</option>
                        <option value="UNIUSDT">Uniswap (UNI/USDT)</option>
                    </select>
                </div>
                <div class="col-md-3">
                    <label class="form-label small text-muted">Timeframe</label>
                    <select id="tv-timeframe-select" class="form-select form-select-sm">
                        <option value="1">1 minute</option>
                        <option value="5">5 minutes</option>
                        <option value="15" selected>15 minutes</option>
                        <option value="30">30 minutes</option>
                        <option value="60">1 heure</option>
                        <option value="240">4 heures</option>
                        <option value="1D">1 jour</option>
                        <option value="1W">1 semaine</option>
                    </select>
                </div>
                <div class="col-md-5">
                    <label class="form-label small text-muted">Indicateurs rapides</label>
                    <div class="btn-group" role="group">
                        <button type="button" class="btn btn-outline-primary btn-sm" onclick="addCustomIndicator('RSI@tv-basicstudies')">RSI</button>
                        <button type="button" class="btn btn-outline-primary btn-sm" onclick="addCustomIndicator('MACD@tv-basicstudies')">MACD</button>
                        <button type="button" class="btn btn-outline-primary btn-sm" onclick="addCustomIndicator('BB@tv-basicstudies')">Bollinger</button>
                        <button type="button" class="btn btn-outline-primary btn-sm" onclick="addCustomIndicator('MA@tv-basicstudies')">MA</button>
                        <button type="button" class="btn btn-outline-primary btn-sm" onclick="addCustomIndicator('EMA@tv-basicstudies')">EMA</button>
                    </div>
                </div>
            </div>
        </div>
    `;
    
    // Insérer les contrôles avant le container TradingView
    const container = document.getElementById('tv_chart_container');
    if (container) {
        container.insertAdjacentHTML('beforebegin', controlsHTML);
        
        // Gestionnaires d'événements
        document.getElementById('tv-symbol-select').addEventListener('change', function() {
            initializeTradingViewWidget(this.value);
        });
        
        document.getElementById('tv-timeframe-select').addEventListener('change', function() {
            changeTimeframe(this.value);
        });
    }
}

// Initialisation automatique lors du chargement de l'onglet trading
document.addEventListener('DOMContentLoaded', function() {
    const tradingTab = document.getElementById('trading-tab');
    if (tradingTab) {
        tradingTab.addEventListener('shown.bs.tab', function() {
            setTimeout(() => {
                addTradingViewControls();
                initializeTradingViewWidget();
            }, 100);
        });
    }
});

