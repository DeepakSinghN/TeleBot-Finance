# weekly_report.py
from datetime import datetime, timedelta
from database import get_conn

def get_weekly_data(user_id):
    """Fetch this week's data for user"""
    conn = get_conn()
    c = conn.cursor()
    
    # This week's triggered alerts
    week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
    
    c.execute(
        '''SELECT symbol, target_price, triggered_price, triggered_at 
           FROM alert_history 
           WHERE user_id=%s AND triggered_at >= %s''',
        (user_id, week_ago)
    )
    triggered = c.fetchall()
    
    # Total active alerts
    c.execute(
        'SELECT COUNT(*) FROM alerts WHERE user_id=%s AND is_active=1',
        (user_id,)
    )
    active_alerts = c.fetchone()[0]
    
    conn.close()
    
    return {
        'triggered': triggered,
        'active_alerts': active_alerts,
        'week_ago': week_ago
    }


def format_weekly_report(user_id, data):
    """Format weekly report message"""
    triggered = data['triggered']
    active = data['active_alerts']
    
    if not triggered and active == 0:
        return (
            "📊 Weekly Report\n"
            "━━━━━━━━━━━━━━━\n\n"
            "No activity this week.\n\n"
            "Set alerts: /addalert\n"
            "View stocks: /stockinfo SYMBOL"
        )
    
    msg = "📊 Your Weekly Report\n"
    msg += "━━━━━━━━━━━━━━━\n\n"
    
    if triggered:
        msg += f"✅ Triggered Alerts: {len(triggered)}\n\n"
        
        best = None
        worst = None
        best_pct = float('-inf')
        worst_pct = float('inf')
        
        for symbol, target, trig_price, trig_at in triggered:
            symbol_clean = symbol.replace('.NS', '')
            pct = ((trig_price - target) / target) * 100
            
            if pct > best_pct:
                best_pct = pct
                best = symbol_clean
            if pct < worst_pct:
                worst_pct = pct
                worst = symbol_clean
            
            sign = "+" if pct >= 0 else ""
            pnl_emoji = "📈" if pct >= 0 else "📉"
            msg += f"{pnl_emoji} {symbol_clean}: {sign}{pct:.1f}%\n"
        
        msg += "\n"
        
        if best:
            msg += f"🏆 Best: {best} ({'+' if best_pct >= 0 else ''}{best_pct:.1f}%)\n"
        if worst and worst != best:
            msg += f"📉 Worst: {worst} ({'+' if worst_pct >= 0 else ''}{worst_pct:.1f}%)\n"
    else:
        msg += "❌ No alerts triggered this week.\n"
    
    msg += (
        f"\n━━━━━━━━━━━━━━━\n"
        f"🔔 Active Alerts: {active}\n\n"
        f"For next week:\n"
        f"/addalert — Set a new alert\n"
        f"/mood — Check market mood"
    )
    
    return msg
