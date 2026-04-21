# market_mood.py
import yfinance as yf
from datetime import datetime

def get_market_mood():
    """Fetch Nifty and top stocks data to calculate market mood"""
    try:
        # Nifty 50 data
        nifty = yf.Ticker("^NSEI")
        nifty_info = nifty.info
        nifty_price = nifty_info.get('regularMarketPrice', 0)
        nifty_change = nifty_info.get('regularMarketChangePercent', 0)

        # Bank Nifty data
        banknifty = yf.Ticker("^NSEBANK")
        banknifty_info = banknifty.info
        banknifty_change = banknifty_info.get('regularMarketChangePercent', 0)

        # Check top 5 stocks
        top_stocks = ["RELIANCE.NS", "TCS.NS", "INFY.NS", "HDFCBANK.NS", "ICICIBANK.NS"]
        gainers = []
        losers = []

        for stock in top_stocks:
            try:
                s = yf.Ticker(stock)
                change = s.info.get('regularMarketChangePercent', 0)
                name = stock.replace(".NS", "")
                if change > 0:
                    gainers.append(f"{name} +{change:.1f}%")
                else:
                    losers.append(f"{name} {change:.1f}%")
            except:
                continue

        # Decide mood
        if nifty_change >= 1.0:
            mood = "🟢 Strongly Bullish"
            mood_msg = "Market is very strong today! Great day for longs."
        elif nifty_change >= 0.3:
            mood = "🟢 Bullish"
            mood_msg = "Market opened positively. Stay cautiously bullish."
        elif nifty_change <= -1.0:
            mood = "🔴 Strongly Bearish"
            mood_msg = "Market is falling heavily. Be careful today."
        elif nifty_change <= -0.3:
            mood = "🔴 Bearish"
            mood_msg = "Market is slightly down. Keep stop losses tight."
        else:
            mood = "🟡 Neutral"
            mood_msg = "Market is flat. Wait for a breakout."

        return {
            'mood': mood,
            'mood_msg': mood_msg,
            'nifty_price': nifty_price,
            'nifty_change': nifty_change,
            'banknifty_change': banknifty_change,
            'gainers': gainers,
            'losers': losers,
        }

    except Exception as e:
        print(f"Market mood error: {e}")
        return None


def format_mood_message(data):
    """Format message for sending"""
    if not data:
        return None

    nifty_sign = "+" if data['nifty_change'] >= 0 else ""
    banknifty_sign = "+" if data['banknifty_change'] >= 0 else ""

    gainers_text = ", ".join(data['gainers']) if data['gainers'] else "None"
    losers_text = ", ".join(data['losers']) if data['losers'] else "None"

    msg = (
        f"🌅 Good Morning! Today's Market Mood\n"
        f"━━━━━━━━━━━━━━━\n"
        f"{data['mood']}\n"
        f"{data['mood_msg']}\n\n"
        f"📊 Nifty 50: ₹{data['nifty_price']:,.0f} "
        f"({nifty_sign}{data['nifty_change']:.2f}%)\n"
        f"🏦 Bank Nifty: "
        f"({banknifty_sign}{data['banknifty_change']:.2f}%)\n\n"
        f"📈 Top Gainers: {gainers_text}\n"
        f"📉 Top Losers: {losers_text}\n"
        f"━━━━━━━━━━━━━━━\n"
        f"🔔 Check your alerts: /myalerts\n"
        f"📊 Stock info: /stockinfo SYMBOL"
    )

    return msg