"""
Flask Web Application for Stock Market Tracker
Simple web interface to track stocks
"""

from flask import Flask, render_template, request, jsonify
from stock_tracker import StockTracker
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
tracker = StockTracker()

@app.route('/')
def index():
    """Home page"""
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Stock Market Tracker</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                max-width: 1000px;
                margin: 0 auto;
                padding: 20px;
                background-color: #f5f5f5;
            }
            .container {
                background-color: white;
                padding: 20px;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            h1 {
                color: #333;
                text-align: center;
            }
            .input-section {
                display: flex;
                gap: 10px;
                margin-bottom: 20px;
                justify-content: center;
            }
            input {
                padding: 10px;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 14px;
            }
            button {
                padding: 10px 20px;
                background-color: #007bff;
                color: white;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                font-size: 14px;
            }
            button:hover {
                background-color: #0056b3;
            }
            table {
                width: 100%;
                border-collapse: collapse;
                margin-top: 20px;
            }
            th, td {
                padding: 12px;
                text-align: left;
                border-bottom: 1px solid #ddd;
            }
            th {
                background-color: #007bff;
                color: white;
            }
            tr:hover {
                background-color: #f9f9f9;
            }
            .positive {
                color: green;
            }
            .negative {
                color: red;
            }
            .error {
                color: red;
                text-align: center;
                padding: 10px;
                background-color: #ffe6e6;
                border-radius: 4px;
            }
            .info {
                color: #0056b3;
                text-align: center;
                padding: 10px;
                background-color: #e6f2ff;
                border-radius: 4px;
                margin-bottom: 20px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📈 Stock Market Tracker</h1>
            <div class="info">
                Configure your API keys in .env to fetch real-time stock data
            </div>
            <div class="input-section">
                <input type="text" id="symbol" placeholder="Enter stock symbol (e.g., AAPL)" />
                <button onclick="addStock()">Add Stock</button>
            </div>
            <div id="message"></div>
            <table id="stockTable">
                <thead>
                    <tr>
                        <th>Symbol</th>
                        <th>Price</th>
                        <th>Change</th>
                        <th>High</th>
                        <th>Low</th>
                        <th>Source</th>
                    </tr>
                </thead>
                <tbody id="tableBody">
                    <tr>
                        <td colspan="6" style="text-align: center; color: #999;">
                            No stocks added yet. Enter a symbol above to get started!
                        </td>
                    </tr>
                </tbody>
            </table>
        </div>
        <script>
            function addStock() {
                const symbol = document.getElementById('symbol').value.toUpperCase();
                const messageDiv = document.getElementById('message');
                
                if (!symbol) {
                    messageDiv.innerHTML = '<div class="error">Please enter a stock symbol</div>';
                    return;
                }
                
                fetch('/api/add_stock', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({symbol: symbol, source: 'alpha_vantage'})
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        messageDiv.innerHTML = '<div class="info">✓ ' + data.message + '</div>';
                        document.getElementById('symbol').value = '';
                        updateTable();
                    } else {
                        messageDiv.innerHTML = '<div class="error">✗ ' + data.message + '</div>';
                    }
                })
                .catch(error => {
                    messageDiv.innerHTML = '<div class="error">Error: ' + error + '</div>';
                });
            }
            
            function updateTable() {
                fetch('/api/portfolio')
                .then(response => response.json())
                .then(data => {
                    const tbody = document.getElementById('tableBody');
                    if (data.stocks.length === 0) {
                        tbody.innerHTML = '<tr><td colspan="6" style="text-align: center; color: #999;">No stocks added yet</td></tr>';
                        return;
                    }
                    
                    tbody.innerHTML = data.stocks.map(stock => `
                        <tr>
                            <td><strong>${stock.symbol}</strong></td>
                            <td>$${stock.price.toFixed(2)}</td>
                            <td class="${stock.change >= 0 ? 'positive' : 'negative'}">
                                ${stock.change >= 0 ? '+' : ''}${stock.change.toFixed(2)}
                            </td>
                            <td>${stock.high ? '$' + stock.high.toFixed(2) : 'N/A'}</td>
                            <td>${stock.low ? '$' + stock.low.toFixed(2) : 'N/A'}</td>
                            <td>${stock.source}</td>
                        </tr>
                    `).join('');
                });
            }
            
            // Update table on page load
            updateTable();
        </script>
    </body>
    </html>
    '''

@app.route('/api/add_stock', methods=['POST'])
def add_stock():
    """API endpoint to add stock"""
    data = request.json
    symbol = data.get('symbol', '').upper()
    source = data.get('source', 'alpha_vantage')
    
    if not symbol:
        return jsonify({'success': False, 'message': 'Symbol is required'}), 400
    
    if not tracker.alpha_vantage_key and source == 'alpha_vantage':
        return jsonify({
            'success': False,
            'message': 'Alpha Vantage API key not configured'
        }), 400
    
    tracker.add_stock(symbol, source=source)
    stock = next((s for s in tracker.stocks_data if s['symbol'] == symbol), None)
    
    if stock:
        return jsonify({
            'success': True,
            'message': f'Added {symbol}: ${stock["price"]}'
        })
    else:
        return jsonify({
            'success': False,
            'message': f'Failed to fetch data for {symbol}'
        }), 400

@app.route('/api/portfolio', methods=['GET'])
def get_portfolio():
    """API endpoint to get portfolio"""
    return jsonify({
        'stocks': tracker.stocks_data
    })

@app.route('/api/clear', methods=['POST'])
def clear_portfolio():
    """API endpoint to clear portfolio"""
    tracker.stocks_data = []
    return jsonify({'success': True, 'message': 'Portfolio cleared'})

if __name__ == '__main__':
    app.run(debug=True, port=5000)
