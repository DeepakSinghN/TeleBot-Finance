# broadcaster.py
import asyncio
from telegram import Bot
from market_mood import get_market_mood, format_mood_message
from earnings import check_earnings_for_alerts, format_earnings_message
from weekly_report import get_weekly_data, format_weekly_report
from database import get_conn

TOKEN = "8427319193:AAGTKQttokXxYexhNY73jOr3Vebf9j4aHe0"

async def send_market_mood():
    """Send market mood to all users"""
    print(f"Market mood broadcast starting...")

    data = get_market_mood()
    if not data:
        print("Could not fetch market data.")
        return

    message = format_mood_message(data)
    if not message:
        return

    conn = get_conn()
    c = conn.cursor()
    c.execute('SELECT user_id FROM users')
    users = c.fetchall()
    conn.close()

    bot = Bot(token=TOKEN)

    success = 0
    failed = 0

    for user in users:
        user_id = user[0]
        try:
            await bot.send_message(
                chat_id=user_id,
                text=message
            )
            success += 1
            await asyncio.sleep(0.1)
        except Exception as e:
            print(f"Could not send message to user {user_id}: {e}")
            failed += 1

    print(f"Broadcast complete! Success: {success}, Failed: {failed}")

async def send_earnings_alerts():
    """Send earnings alerts for upcoming results"""
    print("Checking earnings alerts...")
    
    alerts = check_earnings_for_alerts()
    
    if not alerts:
        print("No upcoming earnings found.")
        return
    
    bot = Bot(token=TOKEN)
    
    for alert in alerts:
        try:
            message = format_earnings_message(alert)
            await bot.send_message(
                chat_id=alert['user_id'],
                text=message
            )
            print(f"Earnings alert sent: {alert['user_id']} - {alert['symbol']}")
            await asyncio.sleep(0.1)
        except Exception as e:
            print(f"Earnings alert error: {e}")

async def send_mood_to_one(bot, user_id):
    """Send mood to one user — for /mood command"""
    data = get_market_mood()
    if not data:
        return "❌ Market data is not available right now."
    return format_mood_message(data)

# Weekly Report
async def send_weekly_reports():
    """Send weekly report to all users every Sunday"""
    print("Sending weekly reports...")
    
    conn = get_conn()
    c = conn.cursor()
    c.execute('SELECT user_id FROM users')
    users = c.fetchall()
    conn.close()
    
    bot = Bot(token=TOKEN)
    
    for user in users:
        user_id = user[0]
        try:
            data = get_weekly_data(user_id)
            message = format_weekly_report(user_id, data)
            
            await bot.send_message(
                chat_id=user_id,
                text=message
            )
            await asyncio.sleep(0.1)
        except Exception as e:
            print(f"Weekly report error {user_id}: {e}")
