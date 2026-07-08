"""
Stock Market Tracker - Main Application
Tracks real-time stock prices using free APIs
"""

import os
import requests
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class StockTracker:
    """Main class for tracking stock market data"""
    
    def __init__(self):
        self.alpha_vantage_key = os.getenv('ALPHA_VANTAGE_API_KEY')
        self.finnhub_key = os.getenv('FINNHUB_API_KEY')
        self.base_url_alpha = 'https://www.alphavantage.co/query'
        self.base_url_finnhub = 'https://finnhub.io/api/v1'
        self.stocks_data = []
    
    def get_stock_price_alpha_vantage(self, symbol):
        """
        Fetch stock price using Alpha Vantage API
        
        Args:
            symbol (str): Stock symbol (e.g., 'AAPL')
        
        Returns:
            dict: Stock data including price, timestamp
        """
        try:
            params = {
                'function': 'GLOBAL_QUOTE',
                'symbol': symbol,
                'apikey': self.alpha_vantage_key
            }
            
            response = requests.get(self.base_url_alpha, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if 'Global Quote' in data and data['Global Quote']:
                quote = data['Global Quote']
                return {
                    'symbol': symbol,
                    'price': float(quote.get('05. price', 0)),
                    'change': float(quote.get('09. change', 0)),
                    'change_percent': quote.get('10. change percent', 'N/A'),
                    'timestamp': datetime.now().isoformat(),
                    'source': 'Alpha Vantage'
                }
            else:
                print(f"No data found for {symbol}")
                return None
        
        except requests.RequestException as e:
            print(f"Error fetching data from Alpha Vantage: {e}")
            return None
    
    def get_stock_price_finnhub(self, symbol):
        """
        Fetch stock price using Finnhub API
        
        Args:
            symbol (str): Stock symbol (e.g., 'AAPL')
        
        Returns:
            dict: Stock data including price, timestamp
        """
        try:
            params = {
                'symbol': symbol,
                'token': self.finnhub_key
            }
            
            response = requests.get(f'{self.base_url_finnhub}/quote', params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if 'c' in data:  # current price
                return {
                    'symbol': symbol,
                    'price': data.get('c', 0),
                    'high': data.get('h', 0),
                    'low': data.get('l', 0),
                    'open': data.get('o', 0),
                    'previous_close': data.get('pc', 0),
                    'timestamp': datetime.now().isoformat(),
                    'source': 'Finnhub'
                }
            else:
                print(f"No data found for {symbol}")
                return None
        
        except requests.RequestException as e:
            print(f"Error fetching data from Finnhub: {e}")
            return None
    
    def add_stock(self, symbol, source='alpha_vantage'):
        """
        Add stock to tracker
        
        Args:
            symbol (str): Stock symbol
            source (str): API source ('alpha_vantage' or 'finnhub')
        """
        if source == 'alpha_vantage':
            data = self.get_stock_price_alpha_vantage(symbol)
        elif source == 'finnhub':
            data = self.get_stock_price_finnhub(symbol)
        else:
            print(f"Unknown source: {source}")
            return
        
        if data:
            self.stocks_data.append(data)
            print(f"✓ Added {symbol}: ${data['price']}")
        else:
            print(f"✗ Failed to add {symbol}")
    
    def get_portfolio(self):
        """Get current portfolio data as DataFrame"""
        if not self.stocks_data:
            print("Portfolio is empty")
            return None
        
        df = pd.DataFrame(self.stocks_data)
        return df
    
    def display_portfolio(self):
        """Display portfolio in formatted table"""
        df = self.get_portfolio()
        if df is not None:
            print("\n" + "="*60)
            print("STOCK MARKET TRACKER - PORTFOLIO")
            print("="*60)
            print(df.to_string(index=False))
            print("="*60 + "\n")
    
    def save_to_csv(self, filename='portfolio.csv'):
        """Save portfolio to CSV file"""
        df = self.get_portfolio()
        if df is not None:
            df.to_csv(filename, index=False)
            print(f"Portfolio saved to {filename}")


def main():
    """Main application entry point"""
    print("🚀 Stock Market Tracker Started\n")
    
    # Initialize tracker
    tracker = StockTracker()
    
    # Check if API keys are configured
    if not tracker.alpha_vantage_key and not tracker.finnhub_key:
        print("⚠️  Warning: No API keys configured!")
        print("Please add your API keys to .env file")
        print("See .env.example for configuration template\n")
    
    # Example: Track popular stocks
    stocks_to_track = ['AAPL', 'GOOGL', 'MSFT', 'TSLA', 'AMZN']
    
    print(f"Tracking {len(stocks_to_track)} stocks using Alpha Vantage API...\n")
    
    for stock in stocks_to_track:
        tracker.add_stock(stock, source='alpha_vantage')
    
    # Display portfolio
    tracker.display_portfolio()
    
    # Save to CSV
    tracker.save_to_csv('portfolio.csv')


if __name__ == '__main__':
    main()
