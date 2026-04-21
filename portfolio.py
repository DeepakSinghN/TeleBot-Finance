# portfolio.py
import yfinance as yf
from database import get_conn

def add_holding(user_id, symbol, quantity, buy_price):
    conn = get_conn()
    c = conn.cursor()
    
    c.execute(
        'SELECT id, quantity, buy_price FROM portfolio WHERE user_id=%s AND symbol=%s',
        (user_id, symbol)
    )
    existing = c.fetchone()
    
    if existing:
        old_qty = existing[1]
        old_price = existing[2]
        new_qty = old_qty + quantity
        new_avg = ((old_qty * old_price) + (quantity * buy_price)) / new_qty
        c.execute(
            'UPDATE portfolio SET quantity=%s, buy_price=%s WHERE user_id=%s AND symbol=%s',
            (new_qty, new_avg, user_id, symbol)
        )
    else:
        c.execute(
            'INSERT INTO portfolio (user_id, symbol, quantity, buy_price) VALUES (%s, %s, %s, %s)',
            (user_id, symbol, quantity, buy_price)
        )
    
    conn.commit()
    conn.close()


def remove_holding(user_id, symbol):
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        'DELETE FROM portfolio WHERE user_id=%s AND symbol=%s',
        (user_id, symbol)
    )
    conn.commit()
    conn.close()


def get_portfolio(user_id):
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        'SELECT symbol, quantity, buy_price FROM portfolio WHERE user_id=%s',
        (user_id,)
    )
    holdings = c.fetchall()
    conn.close()
    
    if not holdings:
        return None
    
    portfolio = []
    total_invested = 0
    total_current = 0
    
    for symbol, quantity, buy_price in holdings:
        try:
            stock = yf.Ticker(symbol)
            hist = stock.history(period="1d")
            current_price = hist['Close'].iloc[-1] if not hist.empty else buy_price
            
            invested = quantity * buy_price
            current_value = quantity * current_price
            pnl = current_value - invested
            pnl_pct = ((current_price - buy_price) / buy_price) * 100
            
            total_invested += invested
            total_current += current_value
            
            portfolio.append({
                'symbol': symbol.replace('.NS', '').replace('.BO', ''),
                'exchange': 'BSE' if '.BO' in symbol else 'NSE',
                'quantity': quantity,
                'buy_price': buy_price,
                'current_price': current_price,
                'pnl': pnl,
                'pnl_pct': pnl_pct
            })
        except Exception as e:
            print(f"Portfolio error {symbol}: {e}")
            continue
    
    total_pnl = total_current - total_invested
    total_pnl_pct = ((total_pnl) / total_invested * 100) if total_invested > 0 else 0
    
    return {
        'holdings': portfolio,
        'total_invested': total_invested,
        'total_current': total_current,
        'total_pnl': total_pnl,
        'total_pnl_pct': total_pnl_pct
    }


def format_portfolio_message(data):
    if not data or not data['holdings']:
        return "📭 Portfolio is empty. Add a stock with /addholding."
    
    msg = "📊 Your Portfolio\n"
    msg += "━━━━━━━━━━━━━━━\n"
    
    for h in data['holdings']:
        pnl_emoji = "📈" if h['pnl'] >= 0 else "📉"
        sign = "+" if h['pnl'] >= 0 else ""
        
        msg += (
            f"\n{pnl_emoji} {h['symbol']} ({h['exchange']})\n"
            f"   Qty: {h['quantity']} | Avg: ₹{h['buy_price']:.1f}\n"
            f"   CMP: ₹{h['current_price']:.1f}\n"
            f"   P&L: {sign}₹{h['pnl']:.0f} ({sign}{h['pnl_pct']:.1f}%)\n"
        )
    
    total_emoji = "📈" if data['total_pnl'] >= 0 else "📉"
    total_sign = "+" if data['total_pnl'] >= 0 else ""
    
    msg += (
        f"\n━━━━━━━━━━━━━━━\n"
        f"💰 Invested: ₹{data['total_invested']:,.0f}\n"
        f"💼 Current: ₹{data['total_current']:,.0f}\n"
        f"{total_emoji} Total P&L: {total_sign}₹{data['total_pnl']:,.0f} "
        f"({total_sign}{data['total_pnl_pct']:.1f}%)\n"
    )
    
    return msg
