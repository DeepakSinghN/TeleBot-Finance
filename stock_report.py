# stock_report.py
import yfinance as yf
from datetime import datetime
import pytz
from database import get_conn

def generate_report(symbol):
    """Generate full stock report"""
    try:
        stock = yf.Ticker(symbol)
        hist = stock.history(period="1y")
        
        if hist.empty:
            return None
        
        # Current price
        current_price = hist['Close'].iloc[-1]
        
        # 52 Week High/Low
        week_52_high = hist['High'].max()
        week_52_low = hist['Low'].min()
        
        # Support & Resistance — last 30 days
        last_30 = hist.tail(30)
        support = last_30['Low'].min()
        resistance = last_30['High'].max()
        
        # Average Volume
        avg_volume = hist['Volume'].mean()
        current_volume = hist['Volume'].iloc[-1]
        volume_signal = "High" if current_volume > avg_volume * 1.5 else "Normal"
        
        # Moving Averages
        ma_20 = hist['Close'].tail(20).mean()
        ma_50 = hist['Close'].tail(50).mean()
        
        # Calculate RSI
        delta = hist['Close'].diff()
        gain = delta.where(delta > 0, 0).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        current_rsi = rsi.iloc[-1]
        
        # Fundamental data
        info = stock.info
        pe_ratio = info.get('trailingPE', 0)
        market_cap = info.get('marketCap', 0)
        market_cap_cr = market_cap / 10000000 if market_cap else 0
        sector = info.get('sector', 'N/A')
        dividend = info.get('dividendYield', 0)
        dividend = dividend * 100 if dividend else 0
        
        # Decide trend
        if current_price > ma_20 > ma_50:
            trend = "📈 Uptrend"
            trend_msg = "Stock is moving up"
        elif current_price < ma_20 < ma_50:
            trend = "📉 Downtrend"
            trend_msg = "Stock is moving down"
        else:
            trend = "➡️ Sideways"
            trend_msg = "Stock is moving in a range"
        
        # RSI Signal
        if current_rsi > 70:
            rsi_signal = "Overbought — Sell pressure may come"
        elif current_rsi < 30:
            rsi_signal = "Oversold — Buying opportunity may arise"
        else:
            rsi_signal = "Normal Range"
        
        # Buy/Sell Recommendation
        score = 0
        if current_price > ma_20:
            score += 1
        if current_price > ma_50:
            score += 1
        if current_rsi < 60:
            score += 1
        if current_price < resistance * 0.95:
            score += 1
        
        if score >= 3:
            recommendation = "BUY — Conditions are favorable"
            risk = "Low to Medium"
        elif score == 2:
            recommendation = "HOLD — Wait for confirmation"
            risk = "Medium"
        else:
            recommendation = "AVOID — Do not buy right now"
            risk = "High"
        
        return {
            'symbol': symbol.replace('.NS', '').replace('.BO', ''),
            'exchange': 'BSE' if '.BO' in symbol else 'NSE',
            'current_price': current_price,
            'week_52_high': week_52_high,
            'week_52_low': week_52_low,
            'support': support,
            'resistance': resistance,
            'ma_20': ma_20,
            'ma_50': ma_50,
            'rsi': current_rsi,
            'rsi_signal': rsi_signal,
            'volume_signal': volume_signal,
            'trend': trend,
            'trend_msg': trend_msg,
            'pe_ratio': pe_ratio,
            'market_cap_cr': market_cap_cr,
            'sector': sector,
            'dividend': dividend,
            'recommendation': recommendation,
            'risk': risk,
            'generated_at': datetime.now(pytz.timezone('Asia/Kolkata')).strftime('%d %B %Y %I:%M %p')
        }
        
    except Exception as e:
        print(f"Report generate error: {e}")
        return None


def format_report(data):
    """Format report message"""
    if not data:
        return "❌ Could not generate report. Check the stock symbol."
    
    msg = (
        f"📋 Full Stock Report\n"
        f"━━━━━━━━━━━━━━━\n"
        f"📌 Stock: {data['symbol']} ({data['exchange']})\n"
        f"💰 Current Price: ₹{data['current_price']:.1f}\n"
        f"🕐 Generated: {data['generated_at']}\n\n"
        
        f"📊 Technical Analysis\n"
        f"━━━━━━━━━━━━━━━\n"
        f"Trend: {data['trend']}\n"
        f"({data['trend_msg']})\n\n"
        
        f"🎯 Key Levels:\n"
        f"Support:    ₹{data['support']:.1f}\n"
        f"Resistance: ₹{data['resistance']:.1f}\n\n"
        
        f"📈 Moving Averages:\n"
        f"MA 20:  ₹{data['ma_20']:.1f}\n"
        f"MA 50:  ₹{data['ma_50']:.1f}\n\n"
        
        f"📉 RSI: {data['rsi']:.1f}\n"
        f"{data['rsi_signal']}\n\n"
        
        f"📦 Volume: {data['volume_signal']}\n\n"
        
        f"52W High: ₹{data['week_52_high']:.1f}\n"
        f"52W Low:  ₹{data['week_52_low']:.1f}\n\n"
        
        f"🏢 Fundamentals\n"
        f"━━━━━━━━━━━━━━━\n"
        f"Sector: {data['sector']}\n"
        f"Market Cap: ₹{data['market_cap_cr']:.0f} Cr\n"
        f"PE Ratio: {data['pe_ratio']:.1f}\n"
        f"Dividend: {data['dividend']:.2f}%\n\n"
        
        f"🎯 Recommendation\n"
        f"━━━━━━━━━━━━━━━\n"
        f"{data['recommendation']}\n"
        f"Risk Level: {data['risk']}\n\n"
        
        f"Disclaimer: This is for educational\n"
        f"purposes only — not investment advice.\n"
        f"Always do your own research."
    )
    
    return msg


def save_report_purchase(user_id, symbol):
    """Save report purchase to DB"""
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        '''INSERT INTO report_purchases (user_id, symbol)
           VALUES (%s, %s)''',
        (user_id, symbol)
    )
    conn.commit()
    conn.close()


def has_purchased_report(user_id, symbol):
    """Check if user has already purchased this report"""
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        '''SELECT id FROM report_purchases 
           WHERE user_id=%s AND symbol=%s AND is_active=1''',
        (user_id, symbol)
    )
    result = c.fetchone()
    conn.close()
    return result is not None
