document.addEventListener('DOMContentLoaded', () => {
    const ctx = document.getElementById('portfolioChart').getContext('2d');

    async function loadPortfolio() {
        try {
            const res = await fetch('/api/binance/portfolio');
            const data = await res.json();
            const assets = data.portfolio.map(p => p.asset);
            const values = data.portfolio.map(p => p.value_usdt);

            new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: assets,
                    datasets: [{
                        data: values,
                        backgroundColor: assets.map(() => `hsl(${Math.random()*360},70%,60%)`)
                    }]
                },
                options: {responsive: true, plugins:{legend:{position:'right'}}}
            });
        } catch (e) {
            console.error('Portfolio error:', e);
        }
    }

    loadPortfolio();
});
