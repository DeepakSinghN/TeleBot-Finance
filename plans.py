# plans.py
from database import get_conn

PLANS = {
    'free':  {'alerts': 3,            'check_mins': 5, 'price': 0},
    'basic': {'alerts': 10,           'check_mins': 2, 'price': 99},
    'pro':   {'alerts': float('inf'), 'check_mins': 1, 'price': 249},
}

def get_user_plan(user_id):
    """Fetch user's current plan"""
    from datetime import datetime
    
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        'SELECT plan, plan_expiry FROM users WHERE user_id=%s', 
        (user_id,)
    )
    user = c.fetchone()
    conn.close()
    
    if not user:
        return 'free'
    
    plan, expiry = user
    
    # Check if plan has expired
    if expiry and datetime.now().strftime('%Y-%m-%d') > expiry:
        # Plan expired — downgrade to free
        downgrade_to_free(user_id)
        return 'free'
    
    return plan or 'free'

def get_alert_limit(user_id):
    """Get how many alerts user can set"""
    plan = get_user_plan(user_id)
    return PLANS[plan]['alerts']

def can_add_alert(user_id):
    """Check if user can add more alerts"""
    limit = get_alert_limit(user_id)
    
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        'SELECT COUNT(*) FROM alerts WHERE user_id=%s AND is_active=1',
        (user_id,)
    )
    current_count = c.fetchone()[0]
    conn.close()
    
    return current_count < limit, current_count, limit

def downgrade_to_free(user_id):
    """Downgrade user to free plan"""
    conn = get_conn()
    c = conn.cursor()
    c.execute(
        "UPDATE users SET plan='free', plan_expiry=NULL WHERE user_id=%s",
        (user_id,)
    )
    conn.commit()
    conn.close()
