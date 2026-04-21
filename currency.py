# currency.py
import yfinance as yf

# Currency pairs and their Yahoo Finance symbols
CURRENCIES = {
    'USDINR': {'symbol': 'INR=X',    'name': 'US Dollar',      'short': 'USD', 'emoji': '💵'},
    'EURINR': {'symbol': 'EURINR=X', 'name': 'Euro',           'short': 'EUR', 'emoji': '💶'},
    'GBPINR': {'symbol': 'GBPINR=X', 'name': 'British Pound',  'short': 'GBP', 'emoji': '💷'},
    'JPYINR': {'symbol': 'JPYINR=X', 'name': 'Japanese Yen',   'short': 'JPY', 'emoji': '💴'},
}


def get_currency_rate(currency_key):
    """Fetch current currency rate"""
    currency_key = currency_key.upper()
    
    if currency_key not in CURRENCIES:
        return None
    
    currency = CURRENCIES[currency_key]
    
    try:
        ticker = yf.Ticker(currency['symbol'])
        hist = ticker.history(period="5d")
        
        if hist.empty or len(hist) < 2:
            return None
        
        current_rate = hist['Close'].iloc[-1]
        prev_rate = hist['Close'].iloc[-2]
        change_pct = ((current_rate - prev_rate) / prev_rate) * 100
        change_abs = current_rate - prev_rate
        
        # Week high/low
        week_high = hist['High'].max()
        week_low = hist['Low'].min()
        
        # Today's high/low
        today_high = hist['High'].iloc[-1]
        today_low = hist['Low'].iloc[-1]
        
        return {
            'key': currency_key,
            'name': currency['name'],
            'short': currency['short'],
            'emoji': currency['emoji'],
            'rate': current_rate,
            'prev_rate': prev_rate,
            'change_pct': change_pct,
            'change_abs': change_abs,
            'today_high': today_high,
            'today_low': today_low,
            'week_high': week_high,
            'week_low': week_low,
        }
        
    except Exception as e:
        print(f"Currency error {currency_key}: {e}")
        return None


def format_currency_message(data):
    """Format currency info message"""
    if not data:
        return "❌ Could not fetch currency data."
    
    change_emoji = "📈" if data['change_pct'] >= 0 else "📉"
    change_sign = "+" if data['change_pct'] >= 0 else ""
    
    msg = (
        f"{data['emoji']} {data['short']}/INR\n"
        f"━━━━━━━━━━━━━━━\n"
        f"💰 Rate: ₹{data['rate']:.2f}\n"
        f"{change_emoji} Change: {change_sign}{data['change_abs']:.2f} "
        f"({change_sign}{data['change_pct']:.2f}%)\n\n"
        f"📊 Today's Range:\n"
        f"High: ₹{data['today_high']:.2f}\n"
        f"Low:  ₹{data['today_low']:.2f}\n\n"
        f"📅 5 Day Range:\n"
        f"High: ₹{data['week_high']:.2f}\n"
        f"Low:  ₹{data['week_low']:.2f}\n\n"
        f"Meaning: 1 {data['short']} = ₹{data['rate']:.2f}"
    )
    
    return msg


def get_all_currencies():
    """Fetch all currency rates at once"""
    results = []
    for key in CURRENCIES:
        data = get_currency_rate(key)
        if data:
            results.append(data)
    return results