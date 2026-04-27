# checker.py
import yfinance as yf
import asyncio
from telegram import Bot
from commodity import get_commodity_price, COMMODITIES
from currency import get_currency_rate, CURRENCIES
from database import get_conn

TOKEN = "8427319193:AAGTKQttokXxYexhNY73jOr3Vebf9j4aHe0"

async def check_and_send_alerts():
    bot = Bot(token=TOKEN)
    conn = get_conn()
    c = conn.cursor()
    
    # Fetch all active alerts
    c.execute(
        'SELECT id, user_id, symbol, target_price, condition FROM alerts WHERE is_active=1'
    )
    alerts = c.fetchall()
    
    for alert in alerts:
        alert_id, user_id, symbol, target, condition = alert
        
        # ─── Commodity Alert Check ───
        if symbol.startswith("COMM:"):
            commodity_key = symbol.replace("COMM:", "")
            try:
                data = get_commodity_price(commodity_key)
                if not data:
                    continue
                current_price = data['usd_price']
                alert_emoji = data['emoji']
                alert_name = data['name']
                is_commodity = True
                is_currency = False
            except:
                continue
        
        # ─── Currency Alert Check ───
        elif symbol.startswith("CURR:"):
            currency_key = symbol.replace("CURR:", "")
            try:
                data = get_currency_rate(currency_key)
                if not data:
                    continue
                current_price = data['rate']
                alert_emoji = data['emoji']
                alert_name = f"{data['short']}/INR"
                is_commodity = False
                is_currency = True
            except:
                continue
        
        # ─── Normal Stock Alert Check ───
        else:
            try:
                stock = yf.Ticker(symbol)
                hist = stock.history(period="1d")
                if hist.empty:
                    continue
                current_price = hist['Close'].iloc[-1]
                alert_emoji = "🚀" if condition == "above" else "🔻"
                alert_name = symbol
                is_commodity = False
                is_currency = False
            except:
                continue
        
        # Check if condition is met
        triggered = False
        if condition == "above" and current_price >= target:
            triggered = True
        elif condition == "below" and current_price <= target:
            triggered = True
        
        if triggered:
            # ─── Commodity Message ───
            if is_commodity:
                await bot.send_message(
                    chat_id=user_id,
                    text=(
                        f"{alert_emoji} Commodity Alert!\n\n"
                        f"📌 {alert_name}\n"
                        f"💵 Current: ${current_price:.2f}\n"
                        f"🎯 Target: ${target:.2f}\n\n"
                        f"Time to make your move! 💪"
                    )
                )
            
            # ─── Currency Message ───
            elif is_currency:
                await bot.send_message(
                    chat_id=user_id,
                    text=(
                        f"{alert_emoji} Currency Alert!\n\n"
                        f"📌 {alert_name}\n"
                        f"💰 Current Rate: ₹{current_price:.2f}\n"
                        f"🎯 Target: ₹{target:.2f}\n\n"
                        f"Time to make your move! 💪"
                    )
                )
            
            # ─── Stock Message ───
            else:
                await bot.send_message(
                    chat_id=user_id,
                    text=(
                        f"{alert_emoji} ALERT TRIGGERED!\n\n"
                        f"📌 Stock: {symbol}\n"
                        f"💰 Current Price: ₹{current_price:.1f}\n"
                        f"🎯 Target: ₹{target:.1f}\n\n"
                        f"Time to make your move! 💪"
                    )
                )
            
           # Delete alert permanently
            c.execute(
                'DELETE FROM alerts WHERE id=%s',
                (alert_id,)
)
            
            # Save to alert history
            c.execute(
                '''INSERT INTO alert_history 
                   (user_id, symbol, target_price, triggered_price)
                   VALUES (%s, %s, %s, %s)''',
                (user_id, symbol, target, current_price)
            )
            
            conn.commit()
    
    conn.close()
