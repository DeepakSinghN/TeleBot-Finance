# commodity.py
import yfinance as yf

# Commodities and their Yahoo Finance symbols
COMMODITIES = {
    'GOLD': {'symbol': 'GC=F', 'name': 'Gold', 'unit': 'USD/oz', 'emoji': '🥇'},
    'SILVER': {'symbol': 'SI=F', 'name': 'Silver', 'unit': 'USD/oz', 'emoji': '🥈'},
    'CRUDE': {'symbol': 'CL=F', 'name': 'Crude Oil', 'unit': 'USD/barrel', 'emoji': '🛢️'},
    'NATURALGAS': {'symbol': 'NG=F', 'name': 'Natural Gas', 'unit': 'USD/MMBtu', 'emoji': '⛽'},
}

# USD to INR conversion
def get_usd_inr():
    try:
        fx = yf.Ticker("INR=X")
        hist = fx.history(period="1d")
        if not hist.empty:
            return hist['Close'].iloc[-1]
        return 83.0  # Default rate
    except:
        return 83.0


def get_commodity_price(commodity_key):
    """Fetch current commodity price"""
    commodity_key = commodity_key.upper()
    
    if commodity_key not in COMMODITIES:
        return None
    
    commodity = COMMODITIES[commodity_key]
    
    try:
        ticker = yf.Ticker(commodity['symbol'])
        hist = ticker.history(period="5d")
        
        if hist.empty or len(hist) < 2:
            return None
        
        usd_price = hist['Close'].iloc[-1]
        prev_price = hist['Close'].iloc[-2]
        change_pct = ((usd_price - prev_price) / prev_price) * 100
        
        # Convert to INR
        usd_inr = get_usd_inr()
        inr_price = usd_price * usd_inr
        
        # Per 10g price for Gold/Silver
        if commodity_key == 'GOLD':
            # 1 oz = 31.1 grams
            inr_per_10g = (inr_price / 31.1) * 10
        elif commodity_key == 'SILVER':
            inr_per_10g = (inr_price / 31.1) * 10
        else:
            inr_per_10g = None
        
        return {
            'key': commodity_key,
            'name': commodity['name'],
            'emoji': commodity['emoji'],
            'unit': commodity['unit'],
            'usd_price': usd_price,
            'inr_price': inr_price,
            'inr_per_10g': inr_per_10g,
            'change_pct': change_pct,
            'usd_inr': usd_inr,
            'high': hist['High'].iloc[-1],
            'low': hist['Low'].iloc[-1],
            'week_high': hist['High'].max(),
            'week_low': hist['Low'].min()
        }
        
    except Exception as e:
        print(f"Commodity error {commodity_key}: {e}")
        return None


def format_commodity_message(data):
    """Format commodity info message"""
    if not data:
        return "❌ Could not fetch commodity data."
    
    change_emoji = "📈" if data['change_pct'] >= 0 else "📉"
    change_sign = "+" if data['change_pct'] >= 0 else ""
    
    msg = (
        f"{data['emoji']} {data['name']}\n"
        f"━━━━━━━━━━━━━━━\n"
        f"💵 USD Price: ${data['usd_price']:.2f} {data['unit']}\n"
        f"💰 INR Price: ₹{data['inr_price']:,.0f}\n"
    )
    
    # Per 10g price for Gold and Silver
    if data['inr_per_10g']:
        msg += f"⚖️ Per 10g: ₹{data['inr_per_10g']:,.0f}\n"
    
    msg += (
        f"{change_emoji} Change: {change_sign}{data['change_pct']:.2f}%\n\n"
        f"📊 Today's Range:\n"
        f"High: ${data['high']:.2f}\n"
        f"Low:  ${data['low']:.2f}\n\n"
        f"📅 5 Day Range:\n"
        f"High: ${data['week_high']:.2f}\n"
        f"Low:  ${data['week_low']:.2f}\n\n"
        f"💱 USD/INR: ₹{data['usd_inr']:.2f}"
    )
    
    return msg