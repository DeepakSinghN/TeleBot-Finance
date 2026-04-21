# watchlist.py
import yfinance as yf
from database import get_conn

def add_to_watchlist(user_id, symbol, target_price):
    conn = get_conn()
    c = conn.cursor()
    
    c.execute(
        'SELECT id FROM watchlist WHERE user_id=%s AND symbol=%s AND is_active=1',
        (user_id, symbol)
    )
    existing = c.fetchone()
    
    if existing:
        conn.close()
        return False
    
    c.execute(
        'INSERT INTO watchlist (user_id, symbol, target_price) VALUES (%s, %s, %s)',
        (user_id, symbol, target_price)
    )
    conn.commit()
    conn.close()
    return True


def get_watchlist(user_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        'SELECT id, symbol, target_price FROM watchlist WHERE user_id=%s AND is_active=1',
        (user_id,)
    )
    items = c.fetchall()
    conn.close()
    return items


def remove_from_watchlist(user_id, watchlist_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        'UPDATE watchlist SET is_active=0 WHERE id=%s AND user_id=%s',
        (watchlist_id, user_id)
    )
    conn.commit()
    conn.close()


def check_watchlist_targets():
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        'SELECT id, user_id, symbol, target_price FROM watchlist WHERE is_active=1'
    )
    items = c.fetchall()
    conn.close()
    
    triggered = []
    
    for item_id, user_id, symbol, target_price in items:
        try:
            stock = yf.Ticker(symbol)
            hist = stock.history(period="1d")
            
            if hist.empty:
                continue
            
            current_price = hist['Close'].iloc[-1]
            
            if current_price <= target_price:
                triggered.append({
                    'id': item_id,
                    'user_id': user_id,
                    'symbol': symbol.replace('.NS', ''),
                    'target_price': target_price,
                    'current_price': current_price
                })
                
                conn = get_conn()
                c = conn.cursor()
                c.execute(
                    'UPDATE watchlist SET is_active=0 WHERE id=%s',
                    (item_id,)
                )
                conn.commit()
                conn.close()
                
        except Exception as e:
            print(f"Watchlist check error {symbol}: {e}")
            continue
    
    return triggered
