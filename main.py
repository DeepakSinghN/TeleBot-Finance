# main.py
import asyncio
import schedule
import time
import threading
from broadcaster import send_market_mood, send_earnings_alerts
from telegram.ext import (
    Application, CommandHandler, 
    ConversationHandler, MessageHandler, filters
)
from bot import (start, add_alert_start, get_symbol,
                 get_price_target, confirm_alert, my_alerts,
                 delete_alert, upgrade, pay, approve_payment, my_id, stock_info, mood, check_earnings, portfolio, add_holding_cmd, remove_holding_cmd, weekly_report_cmd, watchlist_cmd, add_watch_cmd, remove_watch_cmd, buy_report_cmd, pay_report_cmd, approve_report_cmd, refer_cmd, use_referral_cmd, stats_cmd, commodity_cmd, commodity_alert_cmd, currency_cmd, currency_alert_cmd, feedback_cmd,
                 WAITING_SYMBOL, WAITING_PRICE, WAITING_CONDITION)

from checker import check_and_send_alerts
from database import init_db
from broadcaster import send_market_mood, send_earnings_alerts, send_weekly_reports

TOKEN = "8427319193:AAGTKQttokXxYexhNY73jOr3Vebf9j4aHe0"

# Define conv handler — before handlers
conv_handler = ConversationHandler(
    entry_points=[CommandHandler('addalert', add_alert_start)],
    states={
        WAITING_SYMBOL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_symbol)],
        WAITING_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_price_target)],
        WAITING_CONDITION: [CommandHandler('confirm', confirm_alert)],
    },
    fallbacks=[CommandHandler('cancel', lambda u, c: ConversationHandler.END)]
)


def run_checker():
    """Check price every 1 minute"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    schedule.every(1).minutes.do(
        lambda: loop.run_until_complete(check_and_send_alerts())
    )
    
    while True:
        schedule.run_pending()
        time.sleep(30)

def run_scheduler(loop):
    def mood_job():
        asyncio.run_coroutine_threadsafe(send_market_mood(), loop)

    def earnings_job():
        asyncio.run_coroutine_threadsafe(send_earnings_alerts(), loop)

    def weekly_job():
        asyncio.run_coroutine_threadsafe(send_weekly_reports(), loop)

    # Market mood at 9:15 AM
    schedule.every().day.at("09:15").do(mood_job)
    
    # Earnings alert at 8:00 AM
    schedule.every().day.at("08:00").do(earnings_job)

    # Weekly report every Sunday
    schedule.every().sunday.at("10:00").do(weekly_job)

    while True:
        schedule.run_pending()
        time.sleep(30)

def main():
    init_db()
    
    # Run checker in background
    checker_thread = threading.Thread(target=run_checker, daemon=True)
    checker_thread.start()
    
    # Bot setup
    app = Application.builder().token(TOKEN).build()
    
    # Conversation handler for adding alerts
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('addalert', add_alert_start)],
        states={
            WAITING_SYMBOL: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_symbol)],
            WAITING_PRICE: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_price_target)],
            WAITING_CONDITION: [CommandHandler('confirm', confirm_alert)],
        },
        fallbacks=[CommandHandler('cancel', lambda u, c: ConversationHandler.END)]
    )
    
    app.add_handler(CommandHandler('start', start))
    app.add_handler(CommandHandler('mood', mood))
    app.add_handler(CommandHandler('myalerts', my_alerts))
    app.add_handler(conv_handler)
    app.add_handler(CommandHandler('deletealert', delete_alert))
    app.add_handler(CommandHandler('upgrade', upgrade))
    app.add_handler(CommandHandler('pay', pay))
    app.add_handler(CommandHandler('approve', approve_payment))
    app.add_handler(CommandHandler('myid', my_id))
    app.add_handler(CommandHandler('stockinfo', stock_info))
    app.add_handler(CommandHandler('earnings', check_earnings))
    app.add_handler(CommandHandler('portfolio', portfolio))
    app.add_handler(CommandHandler('addholding', add_holding_cmd))
    app.add_handler(CommandHandler('removeholding', remove_holding_cmd))
    app.add_handler(CommandHandler('weeklyreport', weekly_report_cmd))
    app.add_handler(CommandHandler('watchlist', watchlist_cmd))
    app.add_handler(CommandHandler('addwatch', add_watch_cmd))
    app.add_handler(CommandHandler('removewatch', remove_watch_cmd))
    app.add_handler(CommandHandler('buyreport', buy_report_cmd))
    app.add_handler(CommandHandler('payreport', pay_report_cmd))
    app.add_handler(CommandHandler('approvereport', approve_report_cmd))
    app.add_handler(CommandHandler('refer', refer_cmd))
    app.add_handler(CommandHandler('usereferral', use_referral_cmd))
    app.add_handler(CommandHandler('stats', stats_cmd))
    app.add_handler(CommandHandler('commodity', commodity_cmd))
    app.add_handler(CommandHandler('commodityalert', commodity_alert_cmd))
    app.add_handler(CommandHandler('currency', currency_cmd))
    app.add_handler(CommandHandler('currencyalert', currency_alert_cmd))
    app.add_handler(CommandHandler('feedback', feedback_cmd))
    
    print("✅ Bot is running...")
    app.run_polling()

if __name__ == '__main__':
    main()