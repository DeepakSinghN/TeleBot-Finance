# earnings.py
import yfinance as yf
from datetime import datetime, timedelta
from database import get_conn

def get_upcoming_earnings(symbol):
    """Fetch upcoming earnings date for a stock"""
    try:
        stock = yf.Ticker(symbol)
        calendar = stock.calendar
        
        if calendar is None or calendar.empty:
            return None
        
        # Fetch earnings date
        if 'Earnings Date' in calendar.index:
            earnings_date = calendar.loc['Earnings Date'].iloc[0]
            
            # Convert datetime to date
            if hasattr(earnings_date, 'date'):
                earnings_date = earnings_date.date()
            
            today = datetime.now().date()
            days_left = (earnings_date - today).days
            
            return {
                'symbol': symbol,
                'earnings_date': earnings_date,
                'days_left': days_left
            }
        return None
        
    except Exception as e:
        print(f"Earnings fetch error {symbol}: {e}")
        return None


def check_earnings_for_alerts():
    """
    Check earnings for all active alert stocks
    Send alert if result is today or tomorrow
    """
    conn = get_conn()
    c = conn.cursor()
    
    # Fetch all unique active stocks
    c.execute(
        'SELECT DISTINCT user_id, symbol FROM alerts WHERE is_active=1'
    )
    stocks = c.fetchall()
    conn.close()
    
    alerts_to_send = []
    
    for user_id, symbol in stocks:
        earnings = get_upcoming_earnings(symbol)
        
        if not earnings:
            continue
        
        days_left = earnings['days_left']
        
        # Only alert 1 day before or on the day
        if days_left in [0, 1]:
            alerts_to_send.append({
                'user_id': user_id,
                'symbol': symbol,
                'earnings_date': earnings['earnings_date'],
                'days_left': days_left
            })
    
    return alerts_to_send


def format_earnings_message(data):
    """Format earnings alert message"""
    symbol_clean = data['symbol'].replace('.NS', '').replace('.BO', '')
    
    if data['days_left'] == 0:
        timing = "TODAY"
        emoji = "🚨"
        tip = "Stock may see big movement after today's result!"
    else:
        timing = "TOMORROW"
        emoji = "⚠️"
        tip = "Manage your position before tomorrow's result."
    
    msg = (
        f"{emoji} Earnings Alert!\n\n"
        f"📌 Stock: {symbol_clean}\n"
        f"📅 Result: {timing} ({data['earnings_date']})\n\n"
        f"💡 Tip: {tip}\n\n"
        f"📊 Stock info: /stockinfo {symbol_clean}\n"
        f"🔔 Set alert: /addalert"
    )
    
    return msg
