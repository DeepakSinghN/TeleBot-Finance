# stock_data.py
import yfinance as yf
from commodity import COMMODITIES, get_commodity_price


def is_commodity(symbol):
    """Check if symbol is a commodity or stock"""
    return symbol.upper() in COMMODITIES

def get_price(symbol):
    try:
        stock = yf.Ticker(symbol)
        hist = stock.history(period="1d")
        if not hist.empty:
            return hist['Close'].iloc[-1]
        return None
    except:
        return None


def search_stock(name, exchange="NSE"):
    name = name.upper().strip()
    
    if exchange == "BSE":
        suffix = ".BO"
    else:
        suffix = ".NS"
    
    symbol = name + suffix
    price = get_price(symbol)
    
    if price:
        return symbol, price
    
    # Try other exchange
    if exchange == "NSE":
        alt_symbol = name + ".BO"
    else:
        alt_symbol = name + ".NS"
    
    alt_price = get_price(alt_symbol)
    if alt_price:
        return alt_symbol, alt_price
    
    return None, None


def get_stock_info(symbol):
    try:
        stock = yf.Ticker(symbol)
        hist = stock.history(period="5d")
        
        if hist.empty:
            return None
        
        current_price = hist['Close'].iloc[-1]
        prev_price = hist['Close'].iloc[-2] if len(hist) >= 2 else current_price
        change_pct = ((current_price - prev_price) / prev_price) * 100
        
        info = stock.info
        
        return {
            'name': info.get('longName', symbol),
            'price': current_price,
            'change': change_pct,
            'high_52w': info.get('fiftyTwoWeekHigh', 0),
            'low_52w': info.get('fiftyTwoWeekLow', 0),
            'pe_ratio': info.get('trailingPE', 0),
            'market_cap': info.get('marketCap', 0),
            'volume': info.get('volume', 0),
            'avg_volume': info.get('averageVolume', 0),
            'dividend': info.get('dividendYield', 0),
            'sector': info.get('sector', 'N/A'),
            'exchange': 'BSE' if '.BO' in symbol else 'NSE'
        }
    except Exception as e:
        print(f"Stock info error: {e}")
        return None