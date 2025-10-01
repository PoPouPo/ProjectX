document.addEventListener('DOMContentLoaded', () => {
    const tableBody = document.getElementById('transactionsBody');

    async function loadTransactions() {
        try {
            const res = await fetch('/api/binance/transactions');
            const data = await res.json();
            tableBody.innerHTML = '';
            data.forEach(trade => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${trade.symbol}</td>
                    <td>${trade.side}</td>
                    <td>${parseFloat(trade.qty).toFixed(4)}</td>
                    <td>${parseFloat(trade.price).toFixed(4)}</td>
                    <td>${new Date(trade.time).toLocaleString()}</td>
                `;
                tableBody.appendChild(row);
            });
        } catch (e) {
            console.error('Transactions error:', e);
        }
    }

    loadTransactions();
    setInterval(loadTransactions, 60_000);
});
