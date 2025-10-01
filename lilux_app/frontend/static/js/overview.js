document.addEventListener('DOMContentLoaded', () => {
    const balanceEl = document.getElementById('totalBalance');
    const gainersEl = document.getElementById('topGainers');
    const losersEl  = document.getElementById('topLosers');

    async function loadOverview() {
        try {
            const res = await fetch('/api/binance/overview');
            const data = await res.json();

            balanceEl.textContent = `$${data.total_balance_usd.toFixed(2)}`;

            // top gainers
            gainersEl.innerHTML = '';
            data.top_gainers.forEach(c =>
                gainersEl.innerHTML += `<li>${c.symbol} : ${parseFloat(c.priceChangePercent).toFixed(2)}%</li>`
            );

            // top losers
            losersEl.innerHTML = '';
            data.top_losers.forEach(c =>
                losersEl.innerHTML += `<li>${c.symbol} : ${parseFloat(c.priceChangePercent).toFixed(2)}%</li>`
            );

            // graphique balance si back-end renvoie data.balance_history = [{time, value}]
            if (data.balance_history) {
                const ctx = document.getElementById('balanceChart').getContext('2d');
                new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: data.balance_history.map(p => p.time),
                        datasets: [{
                            label: 'Balance USDT',
                            data: data.balance_history.map(p => p.value),
                            fill: false,
                            borderColor: '#4ade80',
                            tension: 0.1
                        }]
                    }
                });
            }
        } catch (e) {
            console.error('Overview error:', e);
        }
    }

    loadOverview();
    setInterval(loadOverview, 60_000); // refresh chaque minute
});
