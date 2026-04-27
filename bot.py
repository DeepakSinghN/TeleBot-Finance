# bot.py
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, 
    MessageHandler, filters, 
    ContextTypes, ConversationHandler
)
from database import get_conn
from stock_data import get_price, search_stock
from plans import can_add_alert, get_user_plan, PLANS
from stock_data import get_stock_info
from broadcaster import send_mood_to_one
from market_mood import get_market_mood, format_mood_message
from earnings import get_upcoming_earnings
from portfolio import add_holding, get_portfolio, remove_holding, format_portfolio_message
from weekly_report import get_weekly_data, format_weekly_report
from watchlist import add_to_watchlist, get_watchlist, remove_from_watchlist
from stock_report import generate_report, format_report, save_report_purchase, has_purchased_report
from referral import generate_referral_code, get_referral_stats, apply_referral, reward_referrer
from commodity import get_commodity_price, format_commodity_message, COMMODITIES
from currency import get_currency_rate, format_currency_message, CURRENCIES, get_all_currencies


TOKEN = "8427319193:AAGTKQttokXxYexhNY73jOr3Vebf9j4aHe0"

# Conversation states
WAITING_SYMBOL, WAITING_PRICE, WAITING_CONDITION = range(3)

# ─── /start command ───
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    
    # Save user to DB
    conn = get_conn()
    c = conn.cursor()
    c.execute('''INSERT INTO users (user_id, username) 
                 VALUES (%s, %s)
                 ON CONFLICT (user_id) DO NOTHING''',
              (user.id, user.username))
    conn.commit()
    conn.close()

    # Referral
    if context.args and context.args[0].startswith("REF"):
        code = context.args[0]
        success, result = apply_referral(user.id, code)
        if success:
            await update.message.reply_text(
                f"✅ Referral code applied!\n"
                f"When you subscribe,\n"
                f"your friend will get a reward!"
            )

    await update.message.reply_text(
        f"🚀 Welcome {user.first_name}!\n\n"
        "📌 Commands:\n\n"
        "🔔 Alerts\n"
        "/addalert — Add a new alert\n"
        "/myalerts — View your alerts\n"
        "/deletealert — Delete an alert\n\n"
        "📊 Stock Info\n"
        "/stockinfo — View stock info\n"
        "/mood — Today's market mood\n"
        "/earnings — Stock result date\n\n"
        "💼 Portfolio\n"
        "/addholding — Add a stock\n"
        "/removeholding — Remove a stock\n"
        "/portfolio — View portfolio\n\n"
        "📈 Reports\n"
        "/buyreport — Get full stock report\n"
        "/weeklyreport — This week's summary\n\n"
        "🥇 Commodity\n"
        "/commodity — Gold, Silver, Crude info\n"
        "/commodityalert — Set commodity alert\n\n"
        "💱 Currency\n"
        "/currency — View currency rates\n"
        "/currencyalert — Set currency alert\n\n"
        "🎁 Refer & Earn\n"
        "/refer — View your referral link\n"
        "/usereferral — Use a referral code\n\n"
        "💎 Premium\n"
        "/upgrade — View plans\n"
        "/myid — Your Telegram ID\n\n"
        "💬 Feedback\n"
        "/feedback — Share your feedback\n\n"
    )

# ─── Add Alert ───
async def add_alert_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    can_add, current, limit = can_add_alert(user_id)
    
    if not can_add:
        plan = get_user_plan(user_id)
        
        if plan == 'free':
            await update.message.reply_text(
                f"🚫 *Free Limit Reached!*\n\n"
                f"You have used {current}/{limit} alerts.\n\n"
                f"⭐ *Basic Plan — ₹99/month*\n"
                f"✅ 10 alerts\n"
                f"✅ Price check every 2 min\n\n"
                f"🚀 *Pro Plan — ₹249/month*\n"
                f"✅ Unlimited alerts\n"
                f"✅ Price check every 1 min\n\n"
                f"To upgrade: /upgrade",
                parse_mode='Markdown'
            )
        elif plan == 'basic':
            await update.message.reply_text(
                f"🚫 *Basic Limit Reached!*\n\n"
                f"You have used {current}/{limit} alerts.\n\n"
                f"🚀 *Pro Plan — ₹249/month*\n"
                f"✅ Unlimited alerts\n"
                f"✅ Price check every 1 min\n\n"
                f"Upgrade with /upgrade!",
                parse_mode='Markdown'
            )
        return ConversationHandler.END
    
    await update.message.reply_text(
        f"📊 Which stock? Enter the symbol\n"
        f"_({current}/{int(limit) if limit != float('inf') else 'Unlimited'} alerts used)_\n\n"
        f"For NSE: RELIANCE\n"
        f"For BSE: RELIANCE BSE\n\n"
        f"Default is NSE.",
        parse_mode='Markdown'
    )
    return WAITING_SYMBOL

# Upgrade
async def upgrade(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    plan = get_user_plan(user_id)
    
    await update.message.reply_text(
        f"💎 *Upgrade Plan*\n\n"
        f"Your current plan: *{plan.upper()}*\n\n"
        f"━━━━━━━━━━━━━━━\n"
        f"⭐ *BASIC — ₹299❌ → ₹99/month✅*\n"
        f"*(First 25 users only!)*\n\n"
        f"✅ 10 Price Alerts\n"
        f"✅ Price check every 2 min\n"
        f"✅ NSE + BSE Support\n"
        f"✅ Full Stock Info\n"
        f"✅ Portfolio Tracker\n"
        f"✅ Alert History\n"
        f"✅ Weekly Performance Report\n"
        f"✅ Earnings Date Alerts\n"
        f"✅ Gold, Silver, Crude Alerts\n"
        f"✅ Currency Rate Alerts\n\n"
        f"━━━━━━━━━━━━━━━\n"
        f"🚀 *PRO — ₹499❌ → ₹299/month✅*\n"
        f"*(First 50 users only!)*\n\n"
        f"✅ Everything in Basic, plus:\n\n"
        f"⚡ Unlimited Price Alerts\n"
        f"⚡ Fastest price check — every 1 min\n"
        f"⚡ Free Full Stock Reports\n"
        f"⚡ Multiple Price Targets per stock\n"
        f"⚡ Priority Support\n\n"
        f"━━━━━━━━━━━━━━━\n\n"
        f"💳 *How to Pay:*\n"
        f"1️⃣ Pay via UPI\n"
        f"2️⃣ Send UTR/Transaction ID\n"
        f"3️⃣ Will be activated in 30 min\n\n"
        f"UPI ID: `PhonePe: 7252058269@ybl`\n"
        f"GPay: `dndeepaknegi007@oksbi`\n\n"
        f"After payment:\n"
        f"/pay basic [UTR] — For Basic\n"
        f"/pay pro [UTR] — For Pro\n\n"
        f"_Example: /pay basic 123456789012_\n\n"
        f"⚡ *Limited time offer — Grab it now!*",
        parse_mode='Markdown'
    )

async def pay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if len(context.args) < 2:
        await update.message.reply_text(
            "❌ Correct format: `/pay basic 123456789012`",
            parse_mode='Markdown'
        )
        return
    
    plan = context.args[0].lower()
    utr = context.args[1]
    
    if plan not in ['basic', 'pro']:
        await update.message.reply_text("❌ Plan must be basic or pro!")
        return
    
    amount = PLANS[plan]['price']
    
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        'INSERT INTO payments (user_id, plan, amount, utr_number) VALUES (%s, %s, %s, %s)',
        (user_id, plan, amount, utr)
    )
    conn.commit()
    conn.close()
    
    await update.message.reply_text(
        f"✅ Payment Request Submitted!\n\n"
        f"Plan: {plan.upper()}\n"
        f"Amount: ₹{amount}\n"
        f"UTR: {utr}\n\n"
        f"⏳ Will be verified and activated in 30 min.",
    )
    
    ADMIN_ID = 6144164934
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=(
            f"💰 New Payment Request!\n\n"
            f"User ID: {user_id}\n"
            f"Plan: {plan.upper()}\n"
            f"Amount: ₹{amount}\n"
            f"UTR: {utr}\n\n"
            f"To approve:\n"
            f"/approve {user_id} {plan}"
        ),
    )

async def approve_payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ADMIN_ID = 6144164934
    
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Only admin can do this!")
        return
    
    if len(context.args) < 2:
        await update.message.reply_text("Format: `/approve USER_ID PLAN`", parse_mode='Markdown')
        return
    
    target_user_id = int(context.args[0])
    plan = context.args[1].lower()
    
    from datetime import datetime, timedelta
    expiry = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
    
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        'UPDATE users SET plan=%s, plan_expiry=%s WHERE user_id=%s',
        (plan, expiry, target_user_id)
    )
    c.execute(
        "UPDATE payments SET status='approved' WHERE user_id=%s AND status='pending'",
        (target_user_id,)
    )
    conn.commit()
    conn.close()

    conn2 = get_conn()
    c2 = conn2.cursor()
    c2.execute(
        'SELECT referrer_id FROM referrals WHERE referred_id=%s AND is_converted=0',
        (target_user_id,)
    )
    referral = c2.fetchone()
    conn2.close()
    
    if referral:
        referrer_id = referral[0]
        new_expiry = reward_referrer(referrer_id)
        try:
            await context.bot.send_message(
                chat_id=referrer_id,
                text=(
                    f"🎉 Reward Received!\n\n"
                    f"Your referral has subscribed!\n"
                    f"Your plan has been extended by 1 month!\n\n"
                    f"New Expiry: {new_expiry}"
                )
            )
        except Exception as e:
            print(f"Reward notify error: {e}")
    
    await context.bot.send_message(
        chat_id=target_user_id,
        text=(
            f"🎉 *Your Plan is Activated!*\n\n"
            f"Plan: *{plan.upper()}*\n"
            f"Expiry: {expiry}\n\n"
            f"Now set new alerts with /addalert! 🚀"
        ),
        parse_mode='Markdown'
    )
    
    await update.message.reply_text(f"✅ Activated {plan} plan for user {target_user_id}!")

async def get_symbol(update: Update, context: ContextTypes.DEFAULT_TYPE):
    symbol_input = update.message.text.upper().strip()
    
    if symbol_input.startswith('/'):
        await update.message.reply_text(
            "❌ Wrong Format!\n\n"
            "You entered a command instead of a stock symbol.\n\n"
            "✅ Correct Format:\n"
            "RELIANCE — NSE (default)\n"
            "RELIANCE BSE — BSE\n"
            "RELIANCE NSE — NSE\n\n"
            "❌ Wrong Format:\n"
            "/addalert TCS BSE — Do not add / at start\n\n"
            "Please enter just the stock symbol:"
        )
        return WAITING_SYMBOL
    
    parts = symbol_input.split()
    
    if len(parts) > 2:
        await update.message.reply_text(
            "❌ Wrong Format!\n\n"
            "✅ Correct Format:\n"
            "RELIANCE — NSE (default)\n"
            "RELIANCE BSE — BSE\n"
            "RELIANCE NSE — NSE\n\n"
            "❌ Wrong Format:\n"
            "RELIANCE TCS BSE — Too many words\n\n"
            "Please enter just the stock symbol:"
        )
        return WAITING_SYMBOL
    
    if len(parts) == 2 and parts[1] in ['NSE', 'BSE']:
        stock_name = parts[0]
        exchange = parts[1]
    elif len(parts) == 2 and parts[1] not in ['NSE', 'BSE']:
        await update.message.reply_text(
            "❌ Wrong Exchange!\n\n"
            "Exchange must be NSE or BSE only.\n\n"
            "✅ Correct Format:\n"
            "RELIANCE — NSE (default)\n"
            "RELIANCE BSE — BSE\n"
            "RELIANCE NSE — NSE\n\n"
            "Please enter again:"
        )
        return WAITING_SYMBOL
    else:
        stock_name = parts[0]
        exchange = "NSE"
    
    symbol, current_price = search_stock(stock_name, exchange)
    
    if not symbol:
        await update.message.reply_text(
            "❌ Stock not found. Enter correct symbol.\n\n"
            "Examples:\n"
            "RELIANCE — Search on NSE\n"
            "RELIANCE NSE — Force NSE\n"
            "RELIANCE BSE — Search on BSE"
        )
        return WAITING_SYMBOL
    
    context.user_data['symbol'] = symbol
    context.user_data['current_price'] = current_price
    exchange_tag = "BSE" if ".BO" in symbol else "NSE"
    
    await update.message.reply_text(
        f"✅ Stock Found!\n\n"
        f"📌 Stock: {stock_name}\n"
        f"🏦 Exchange: {exchange_tag}\n"
        f"💰 Current Price: ₹{current_price:.1f}\n\n"
        f"Now enter target price:\n"
        f"Example: 2500",
        parse_mode='Markdown'
    )
    return WAITING_PRICE

async def get_price_target(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        target = float(update.message.text.strip())
        context.user_data['target'] = target
        current = context.user_data['current_price']
        
        if target > current:
            condition = "above"
            msg = f"📈 Alert when price goes ABOVE ₹{target}?"
        else:
            condition = "below"
            msg = f"📉 Alert when price goes BELOW ₹{target}?"
        
        context.user_data['condition'] = condition
        
        await update.message.reply_text(
            f"{msg}\n\n"
            "Confirm:\n"
            "✅ /confirm — Yes, set it\n"
            "❌ /cancel — Cancel"
        )
        return WAITING_CONDITION
        
    except ValueError:
        await update.message.reply_text("❌ Enter numbers only. Example: 2500")
        return WAITING_PRICE

async def stock_info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    plan = get_user_plan(user_id)

    if not context.args:
        await update.message.reply_text(
            "📊 To view stock info:\n"
            "/stockinfo SYMBOL\n"
            "/stockinfo SYMBOL BSE\n\n"
            "Examples:\n"
            "/stockinfo RELIANCE\n"
            "/stockinfo RELIANCE BSE"
        )
        return

    symbol_input = context.args[0].upper().strip()
    exchange = "NSE"
    if len(context.args) > 1 and context.args[1].upper() == "BSE":
        exchange = "BSE"
    
    symbol, _ = search_stock(symbol_input, exchange)
    
    if not symbol:
        await update.message.reply_text(
            "❌ Stock not found.\n"
            "Example: /stockinfo RELIANCE\n"
            "For BSE: /stockinfo RELIANCE BSE"
        )
        return

    await update.message.reply_text(f"🔍 Fetching data for {symbol_input}...")
    info = get_stock_info(symbol)

    if not info:
        await update.message.reply_text("❌ Could not fetch data.")
        return

    change_emoji = "📈" if info['change'] >= 0 else "📉"
    change_sign = "+" if info['change'] >= 0 else ""
    exchange_tag = info['exchange']

    if plan == 'free':
        await update.message.reply_text(
            f"📊 {info['name']}\n"
            f"🏦 Exchange: {exchange_tag}\n"
            f"💰 Price: ₹{info['price']:.1f}\n"
            f"{change_emoji} Change: {change_sign}{info['change']:.2f}%\n\n"
            f"🔒 PE Ratio: Upgrade to view\n"
            f"🔒 Market Cap: Upgrade to view\n"
            f"🔒 52W High/Low: Upgrade to view\n\n"
            f"Upgrade with /upgrade for full info!"
        )
    elif plan == 'basic':
        market_cap_cr = info['market_cap'] / 10000000 if info['market_cap'] else 0
        await update.message.reply_text(
            f"📊 {info['name']}\n"
            f"🏦 Exchange: {exchange_tag}\n"
            f"💰 Price: ₹{info['price']:.1f}\n"
            f"{change_emoji} Change: {change_sign}{info['change']:.2f}%\n\n"
            f"📈 52W High: ₹{info['high_52w']:.1f}\n"
            f"📉 52W Low: ₹{info['low_52w']:.1f}\n"
            f"🏢 Market Cap: ₹{market_cap_cr:.0f} Cr\n"
            f"📊 PE Ratio: {info['pe_ratio']:.1f}\n"
            f"🏭 Sector: {info['sector']}\n\n"
            f"🔒 Volume Analysis: Available in Pro\n"
            f"🔒 Dividend: Available in Pro"
        )
    elif plan in ['pro', 'proplus']:
        market_cap_cr = info['market_cap'] / 10000000 if info['market_cap'] else 0
        dividend = info['dividend'] * 100 if info['dividend'] else 0
        await update.message.reply_text(
            f"📊 {info['name']}\n"
            f"🏦 Exchange: {exchange_tag}\n"
            f"💰 Price: ₹{info['price']:.1f}\n"
            f"{change_emoji} Change: {change_sign}{info['change']:.2f}%\n\n"
            f"📈 52W High: ₹{info['high_52w']:.1f}\n"
            f"📉 52W Low: ₹{info['low_52w']:.1f}\n"
            f"🏢 Market Cap: ₹{market_cap_cr:.0f} Cr\n"
            f"📊 PE Ratio: {info['pe_ratio']:.1f}\n"
            f"🏭 Sector: {info['sector']}\n"
            f"📦 Volume: {info['volume']:,}\n"
            f"💸 Dividend: {dividend:.2f}%\n\n"
            f"🎯 Set an alert: /addalert"
        )

async def confirm_alert(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    symbol = context.user_data['symbol']
    target = context.user_data['target']
    condition = context.user_data['condition']
    
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        'INSERT INTO alerts (user_id, symbol, target_price, condition) VALUES (%s, %s, %s, %s)',
        (user_id, symbol, target, condition)
    )
    conn.commit()
    conn.close()
    
    emoji = "📈" if condition == "above" else "📉"
    await update.message.reply_text(
        f"{emoji} *Alert Set!*\n\n"
        f"Stock: {symbol}\n"
        f"Target: ₹{target}\n"
        f"Condition: Price {condition} ₹{target}\n\n"
        f"I will notify you when price hits this level! 🔔",
        parse_mode='Markdown'
    )
    return ConversationHandler.END

async def my_alerts(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        'SELECT id, symbol, target_price, condition FROM alerts WHERE user_id=%s AND is_active=1',
        (user_id,)
    )
    alerts = c.fetchall()
    conn.close()
    
    if not alerts:
        await update.message.reply_text("📭 No active alerts found.\nCreate one with /addalert!")
        return
    
    msg = "🔔 *Your Active Alerts:*\n\n"
    for alert in alerts:
        emoji = "📈" if alert[3] == "above" else "📉"
        msg += f"{emoji} ID:{alert[0]} | {alert[1]} | ₹{alert[2]} ({alert[3]})\n"
    
    msg += "\n_To delete use /deletealert [ID]_"
    await update.message.reply_text(msg, parse_mode='Markdown')

async def my_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await update.message.reply_text(
        f"🆔 Your Telegram ID:\n`{user_id}`",
        parse_mode='Markdown'
    )

async def delete_alert(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        'SELECT id, symbol, target_price, condition FROM alerts WHERE user_id=%s AND is_active=1',
        (user_id,)
    )
    alerts = c.fetchall()
    conn.close()
    
    if not alerts:
        await update.message.reply_text("📭 No active alerts to delete!")
        return
    
    msg = "🗑️ *Which alert to delete?*\n\n"
    for alert in alerts:
        emoji = "📈" if alert[3] == "above" else "📉"
        msg += f"{emoji} ID: `{alert[0]}` | {alert[1]} | ₹{alert[2]}\n"
    
    msg += "\n_Enter ID to delete_\n"
    msg += "_Example: `/deletealert 3`_"
    
    if context.args:
        try:
            alert_id = int(context.args[0])
            
            conn = get_conn()
            c = conn.cursor()
            c.execute(
                'SELECT id, symbol FROM alerts WHERE id=%s AND user_id=%s AND is_active=1',
                (alert_id, user_id)
            )
            alert = c.fetchone()
            
            if not alert:
                await update.message.reply_text("❌ Alert not found or already deleted!")
                conn.close()
                return
            
            c.execute(
                'UPDATE alerts SET is_active=0 WHERE id=%s AND user_id=%s',
                (alert_id, user_id)
            )
            conn.commit()
            conn.close()
            
            await update.message.reply_text(
                f"✅ *Alert Deleted!*\n\n"
                f"Stock: {alert[1]}\n"
                f"ID: {alert_id}",
                parse_mode='Markdown'
            )
        except ValueError:
            await update.message.reply_text("❌ Enter correct ID!\nExample: `/deletealert 3`", parse_mode='Markdown')
    else:
        await update.message.reply_text(msg, parse_mode='Markdown')

async def mood(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔍 Fetching market data...")
    message = await send_mood_to_one(context.bot, update.effective_user.id)
    await update.message.reply_text(message)

async def check_earnings(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "📅 Enter symbol to check earnings date\n"
            "Example: /earnings RELIANCE"
        )
        return
    
    symbol_input = context.args[0].upper().strip()
    symbol = symbol_input + ".NS"
    await update.message.reply_text(f"🔍 Searching earnings date for {symbol_input}...")
    earnings = get_upcoming_earnings(symbol)
    
    if not earnings:
        await update.message.reply_text(
            f"📭 No upcoming earnings date found for {symbol_input}.\n"
            f"Result may not have been announced yet."
        )
        return
    
    days_left = earnings['days_left']
    if days_left < 0:
        timing_msg = f"Result came {abs(days_left)} days ago."
        emoji = "✅"
    elif days_left == 0:
        timing_msg = "Result is TODAY!"
        emoji = "🚨"
    elif days_left == 1:
        timing_msg = "Result is TOMORROW!"
        emoji = "⚠️"
    else:
        timing_msg = f"Result in {days_left} days."
        emoji = "📅"
    
    await update.message.reply_text(
        f"{emoji} Earnings Info\n\n"
        f"📌 Stock: {symbol_input}\n"
        f"📅 Date: {earnings['earnings_date']}\n"
        f"⏳ {timing_msg}\n\n"
        f"💡 Stocks see big movement\n"
        f"around results — stay prepared!\n\n"
        f"🔔 Set alert: /addalert"
    )

async def portfolio(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    plan = get_user_plan(user_id)
    
    if plan == 'free':
        await update.message.reply_text(
            "🔒 Portfolio Tracker available in Basic and Pro!\n\n"
            "⭐ Basic — ₹99/month\n"
            "🚀 Pro — ₹249/month\n\n"
            "Upgrade with /upgrade!"
        )
        return
    
    await update.message.reply_text("📊 Loading portfolio...")
    data = get_portfolio(user_id)
    
    if not data:
        await update.message.reply_text(
            "📭 Portfolio is empty!\n\n"
            "To add a stock:\n"
            "/addholding RELIANCE 10 2400"
        )
        return
    
    msg = format_portfolio_message(data)
    await update.message.reply_text(msg)

async def add_holding_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    plan = get_user_plan(user_id)
    
    if plan == 'free':
        await update.message.reply_text(
            "🔒 Portfolio Tracker available in Basic and Pro!\n\n"
            "Upgrade with /upgrade!"
        )
        return
    
    if len(context.args) < 3:
        await update.message.reply_text(
            "❌ Correct format:\n"
            "/addholding SYMBOL QUANTITY BUY_PRICE\n"
            "/addholding SYMBOL QUANTITY BUY_PRICE BSE\n\n"
            "Examples:\n"
            "/addholding RELIANCE 10 2400\n"
            "/addholding RELIANCE 10 2400 BSE"
        )
        return
    
    try:
        stock_name = context.args[0].upper()
        exchange = "NSE"
        if len(context.args) > 3 and context.args[3].upper() == "BSE":
            exchange = "BSE"
        suffix = ".BO" if exchange == "BSE" else ".NS"
        symbol = stock_name + suffix
        quantity = float(context.args[1])
        buy_price = float(context.args[2])
        add_holding(user_id, symbol, quantity, buy_price)
        await update.message.reply_text(
            f"✅ Added to Portfolio!\n\n"
            f"📌 Stock: {stock_name}\n"
            f"🏦 Exchange: {exchange}\n"
            f"📦 Quantity: {quantity}\n"
            f"💰 Buy Price: ₹{buy_price}\n\n"
            f"View portfolio: /portfolio"
        )
    except ValueError:
        await update.message.reply_text(
            "❌ Enter quantity and price as numbers only!\n"
            "Example: /addholding RELIANCE 10 2400"
        )

async def remove_holding_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not context.args:
        await update.message.reply_text("❌ Enter symbol:\n/removeholding RELIANCE")
        return
    symbol = context.args[0].upper() + ".NS"
    remove_holding(user_id, symbol)
    await update.message.reply_text(f"✅ {context.args[0].upper()} removed from portfolio!")

async def weekly_report_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    plan = get_user_plan(user_id)
    if plan == 'free':
        await update.message.reply_text(
            "🔒 Weekly Report available in Basic and Pro!\n\n"
            "⭐ Basic — ₹99/month\n"
            "🚀 Pro — ₹249/month\n\n"
            "Upgrade with /upgrade!"
        )
        return
    await update.message.reply_text("📊 Generating report...")
    data = get_weekly_data(user_id)
    message = format_weekly_report(user_id, data)
    await update.message.reply_text(message)

async def watchlist_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    plan = get_user_plan(user_id)
    items = get_watchlist(user_id)
    if not items:
        await update.message.reply_text(
            "📭 Watchlist is empty!\n\n"
            "To add a stock:\n"
            "/addwatch RELIANCE 2200"
        )
        return
    limits = {'free': 5, 'basic': 10, 'pro': 999}
    limit = limits.get(plan, 5)
    msg = "👀 Your Watchlist\n"
    msg += "━━━━━━━━━━━━━━━\n\n"
    for i, item in enumerate(items):
        if i >= limit:
            msg += "\n🔒 Upgrade to view more stocks!"
            break
        item_id, symbol, target = item
        symbol_clean = symbol.replace('.NS', '')
        msg += f"📌 ID:{item_id} | {symbol_clean} | Target: ₹{target}\n"
    msg += "\nTo remove: /removewatch ID"
    await update.message.reply_text(msg)

async def add_watch_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    plan = get_user_plan(user_id)
    limits = {'free': 5, 'basic': 10, 'pro': 999}
    limit = limits.get(plan, 5)
    current_watchlist = get_watchlist(user_id)
    if len(current_watchlist) >= limit:
        await update.message.reply_text(
            f"🚫 Watchlist limit reached!\n\n"
            f"Plan: {plan.upper()} ({len(current_watchlist)}/{limit})\n\n"
            f"Upgrade with /upgrade to add more!"
        )
        return
    if len(context.args) < 2:
        await update.message.reply_text(
            "❌ Correct format:\n"
            "/addwatch SYMBOL TARGET_PRICE\n\n"
            "Example:\n"
            "/addwatch RELIANCE 2200"
        )
        return
    try:
        symbol = context.args[0].upper() + ".NS"
        target_price = float(context.args[1])
        added = add_to_watchlist(user_id, symbol, target_price)
        if not added:
            await update.message.reply_text(f"⚠️ {context.args[0].upper()} is already in watchlist!")
            return
        await update.message.reply_text(
            f"✅ Added to Watchlist!\n\n"
            f"📌 Stock: {context.args[0].upper()}\n"
            f"🎯 Target: ₹{target_price}\n\n"
            f"I will alert you when price hits ₹{target_price}! 🔔\n\n"
            f"View watchlist: /watchlist"
        )
    except ValueError:
        await update.message.reply_text("❌ Enter price as number only!")

async def remove_watch_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not context.args:
        await update.message.reply_text("❌ Enter ID:\n/removewatch 3\n\nView IDs with: /watchlist")
        return
    try:
        watch_id = int(context.args[0])
        remove_from_watchlist(user_id, watch_id)
        await update.message.reply_text("✅ Removed from watchlist!")
    except ValueError:
        await update.message.reply_text("❌ Enter correct ID!")

async def buy_report_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    plan = get_user_plan(user_id)
    if not context.args:
        await update.message.reply_text(
            "📋 To buy a stock report:\n"
            "/buyreport SYMBOL\n"
            "/buyreport SYMBOL BSE\n\n"
            "💰 Price:\n"
            "Free users: ₹29 per report\n"
            "Basic users: ₹19 per report\n"
            "Pro users: FREE"
        )
        return
    symbol_input = context.args[0].upper().strip()
    exchange = "NSE"
    if len(context.args) > 1 and context.args[1].upper() == "BSE":
        exchange = "BSE"
    suffix = ".BO" if exchange == "BSE" else ".NS"
    symbol = symbol_input + suffix
    if plan in ['pro', 'proplus']:
        await update.message.reply_text(f"Generating report — {symbol_input} ({exchange})...")
        data = generate_report(symbol)
        msg = format_report(data)
        await update.message.reply_text(msg)
        return
    if has_purchased_report(user_id, symbol):
        await update.message.reply_text(f"You have already purchased this report!\n\nGenerating report — {symbol_input} ({exchange})...")
        data = generate_report(symbol)
        msg = format_report(data)
        await update.message.reply_text(msg)
        return
    price = 19 if plan == 'basic' else 29
    await update.message.reply_text(
        f"📋 {symbol_input} ({exchange}) Full Report\n\n"
        f"💰 Price: ₹{price}\n\n"
        f"Pay via UPI:\n"
        f"UPI: apna@upi\n"
        f"Amount: ₹{price}\n\n"
        f"After payment send UTR:\n"
        f"/payreport {symbol_input} UTR_NUMBER"
    )

async def pay_report_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    plan = get_user_plan(user_id)
    if len(context.args) < 2:
        await update.message.reply_text("❌ Correct format:\n/payreport SYMBOL UTR_NUMBER\n\nExample:\n/payreport RELIANCE 123456789012")
        return
    symbol_input = context.args[0].upper()
    utr = context.args[1]
    price = 19 if plan == 'basic' else 29
    await update.message.reply_text(
        f"✅ Payment request submitted!\n\n"
        f"Stock: {symbol_input}\n"
        f"Amount: ₹{price}\n"
        f"UTR: {utr}\n\n"
        f"⏳ Report will be sent within 15 min after verification."
    )
    ADMIN_ID = 6144164934
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=(
            f"📋 Report Purchase Request!\n\n"
            f"User ID: {user_id}\n"
            f"Stock: {symbol_input}\n"
            f"Amount: ₹{price}\n"
            f"UTR: {utr}\n\n"
            f"To approve:\n"
            f"/approvereport {user_id} {symbol_input}"
        )
    )

async def approve_report_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ADMIN_ID = 6144164934
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Only admin can do this!")
        return
    if len(context.args) < 2:
        await update.message.reply_text("Format: /approvereport USER_ID SYMBOL")
        return
    target_user_id = int(context.args[0])
    symbol_input = context.args[1].upper()
    symbol = symbol_input + ".NS"
    save_report_purchase(target_user_id, symbol)
    await update.message.reply_text(f"⏳ Generating report for {symbol_input}...")
    data = generate_report(symbol)
    msg = format_report(data)
    await context.bot.send_message(chat_id=target_user_id, text=(f"🎉 Your Report is Ready!\n\n{msg}"))
    await update.message.reply_text(f"✅ Report sent to {target_user_id}!")

async def refer_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    code = generate_referral_code(user_id)
    stats = get_referral_stats(user_id)
    bot = await context.bot.get_me()
    referral_link = f"https://t.me/{bot.username}?start={code}"
    await update.message.reply_text(
        f"🎁 Refer & Earn!\n\n"
        f"Share this link with friends:\n"
        f"{referral_link}\n\n"
        f"Or share referral code:\n"
        f"{code}\n\n"
        f"📊 Your Stats:\n"
        f"Total Referrals: {stats['total']}\n"
        f"Converted: {stats['converted']}\n"
        f"Pending: {stats['pending']}\n\n"
        f"🎁 Reward:\n"
        f"Friend subscribes → You get 1 month FREE!"
    )

async def use_referral_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not context.args:
        await update.message.reply_text("❌ Enter referral code:\n/usereferral REF123456")
        return
    code = context.args[0].upper().strip()
    success, result = apply_referral(user_id, code)
    if not success:
        await update.message.reply_text(f"❌ {result}")
        return
    referrer_id = result
    await update.message.reply_text(
        f"✅ Referral code applied!\n\n"
        f"When you subscribe to any plan,\n"
        f"your friend will get 1 month FREE!\n\n"
        f"View plans: /upgrade"
    )
    try:
        await context.bot.send_message(
            chat_id=referrer_id,
            text=(f"🎉 Someone joined using your referral!\n\nWhen they subscribe,\nyou will get 1 month FREE! 🎁")
        )
    except Exception as e:
        print(f"Referrer notify error: {e}")

async def stats_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ADMIN_ID = 6144164934
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ Only admin can view this!")
        return
    conn = get_conn()
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM users')
    total_users = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM users WHERE plan='free'")
    free_users = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM users WHERE plan='basic'")
    basic_users = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM users WHERE plan='pro'")
    pro_users = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM users WHERE plan='proplus'")
    proplus_users = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM alerts WHERE is_active=1")
    active_alerts = c.fetchone()[0]
    conn.close()
    revenue = (basic_users * 99) + (pro_users * 249) + (proplus_users * 499)
    await update.message.reply_text(
        f"📊 Bot Stats\n"
        f"━━━━━━━━━━━━━━━\n\n"
        f"👥 Total Users: {total_users}\n\n"
        f"💎 Plans\n"
        f"Free: {free_users}\n"
        f"Basic: {basic_users}\n"
        f"Pro: {pro_users}\n"
        f"Pro+: {proplus_users}\n\n"
        f"🔔 Active Alerts: {active_alerts}\n\n"
        f"💰 Est. Revenue: ₹{revenue:,}"
    )

async def commodity_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            "🥇 Commodity Info\n\n"
            "Available Commodities:\n"
            "GOLD — Gold\n"
            "SILVER — Silver\n"
            "CRUDE — Crude Oil\n"
            "NATURALGAS — Natural Gas\n\n"
            "Usage:\n"
            "/commodity GOLD\n"
            "/commodity SILVER\n"
            "/commodity CRUDE"
        )
        return
    commodity_key = context.args[0].upper().strip()
    if commodity_key not in COMMODITIES:
        await update.message.reply_text("❌ Commodity not found!\n\nAvailable:\nGOLD, SILVER, CRUDE, NATURALGAS")
        return
    await update.message.reply_text(f"🔍 Fetching {commodity_key} data...")
    data = get_commodity_price(commodity_key)
    msg = format_commodity_message(data)
    await update.message.reply_text(msg)

async def commodity_alert_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if len(context.args) < 2:
        await update.message.reply_text(
            "❌ Correct format:\n"
            "/commodityalert COMMODITY TARGET_USD\n\n"
            "Examples:\n"
            "/commodityalert GOLD 2100\n"
            "/commodityalert CRUDE 85\n\n"
            "Note: Target will be in USD"
        )
        return
    commodity_key = context.args[0].upper().strip()
    if commodity_key not in COMMODITIES:
        await update.message.reply_text("❌ Commodity not found!\n\nAvailable:\nGOLD, SILVER, CRUDE, NATURALGAS")
        return
    try:
        target_price = float(context.args[1])
    except ValueError:
        await update.message.reply_text("❌ Enter target price as number only!")
        return
    data = get_commodity_price(commodity_key)
    if not data:
        await update.message.reply_text("❌ Could not fetch data. Try again later.")
        return
    current_usd = data['usd_price']
    condition = "above" if target_price > current_usd else "below"
    condition_text = "goes above" if condition == "above" else "goes below"
    symbol = f"COMM:{commodity_key}"
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        'INSERT INTO alerts (user_id, symbol, target_price, condition) VALUES (%s, %s, %s, %s)',
        (user_id, symbol, target_price, condition)
    )
    conn.commit()
    conn.close()
    await update.message.reply_text(
        f"✅ Commodity Alert Set!\n\n"
        f"{data['emoji']} {data['name']}\n"
        f"Current: ${current_usd:.2f}\n"
        f"Target: ${target_price:.2f}\n"
        f"Condition: Price {condition_text} ${target_price}\n\n"
        f"I will notify you when alert triggers! 🔔"
    )

async def currency_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("🔍 Fetching all currency rates...")
        all_data = get_all_currencies()
        if not all_data:
            await update.message.reply_text("❌ Could not fetch data.")
            return
        msg = "💱 Currency Rates\n━━━━━━━━━━━━━━━\n\n"
        for data in all_data:
            change_emoji = "📈" if data['change_pct'] >= 0 else "📉"
            change_sign = "+" if data['change_pct'] >= 0 else ""
            msg += f"{data['emoji']} {data['short']}/INR: ₹{data['rate']:.2f} {change_emoji} {change_sign}{data['change_pct']:.2f}%\n"
        msg += "\n━━━━━━━━━━━━━━━\nFor details:\n/currency USDINR\n/currency EURINR\n/currency GBPINR\n/currency JPYINR"
        await update.message.reply_text(msg)
        return
    currency_key = context.args[0].upper().strip()
    if currency_key not in CURRENCIES:
        await update.message.reply_text("❌ Currency not found!\n\nAvailable:\nUSDINR — Dollar\nEURINR — Euro\nGBPINR — Pound\nJPYINR — Yen\n\nExample: /currency USDINR")
        return
    await update.message.reply_text(f"🔍 Fetching {currency_key}...")
    data = get_currency_rate(currency_key)
    msg = format_currency_message(data)
    await update.message.reply_text(msg)

async def currency_alert_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if len(context.args) < 2:
        await update.message.reply_text(
            "❌ Correct format:\n"
            "/currencyalert PAIR TARGET\n\n"
            "Examples:\n"
            "/currencyalert USDINR 85\n"
            "/currencyalert EURINR 90\n\n"
            "Meaning: Alert when USD/INR hits ₹85"
        )
        return
    currency_key = context.args[0].upper().strip()
    if currency_key not in CURRENCIES:
        await update.message.reply_text("❌ Currency not found!\n\nAvailable: USDINR, EURINR, GBPINR, JPYINR")
        return
    try:
        target_price = float(context.args[1])
    except ValueError:
        await update.message.reply_text("❌ Enter target as number only!")
        return
    data = get_currency_rate(currency_key)
    if not data:
        await update.message.reply_text("❌ Could not fetch data. Try again later.")
        return
    current_rate = data['rate']
    condition = "above" if target_price > current_rate else "below"
    condition_text = "goes above" if condition == "above" else "goes below"
    symbol = f"CURR:{currency_key}"
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        'INSERT INTO alerts (user_id, symbol, target_price, condition) VALUES (%s, %s, %s, %s)',
        (user_id, symbol, target_price, condition)
    )
    conn.commit()
    conn.close()
    await update.message.reply_text(
        f"✅ Currency Alert Set!\n\n"
        f"{data['emoji']} {data['short']}/INR\n"
        f"Current Rate: ₹{current_rate:.2f}\n"
        f"Target: ₹{target_price:.2f}\n"
        f"Condition: Rate {condition_text} ₹{target_price}\n\n"
        f"I will notify you when alert triggers! 🔔"
    )

# Feedback Form
async def feedback_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    
    if not context.args:
        await update.message.reply_text(
            "💬 We'd love to hear from you!\n\n"
            "Send your feedback like this:\n"
            "/feedback Your message here\n\n"
            "Examples:\n"
            "/feedback Add more stocks support\n"
            "/feedback Love the gold alerts feature!\n"
            "/feedback App is very easy to use"
        )
        return
    
    feedback_text = ' '.join(context.args)
    
    await update.message.reply_text(
        "✅ Feedback Received!\n\n"
        "Thank you for helping us improve StockSathi.\n"
        "We read every feedback personally! 🙏"
    )
    
    # Admin ko bhejo
    ADMIN_ID = 6144164934
    await context.bot.send_message(
        chat_id=ADMIN_ID,
        text=(
            f"💬 New Feedback!\n\n"
            f"User ID: {user_id}\n"
            f"Name: {update.effective_user.first_name}\n"
            f"Username: @{update.effective_user.username}\n\n"
            f"Message:\n{feedback_text}"
        )
    )
