# referral.py
from datetime import datetime, timedelta
from database import get_conn

def generate_referral_code(user_id):
    """Generate unique referral code for user"""
    return f"REF{user_id}"


def get_referral_stats(user_id):
    """Fetch user's referral stats"""
    conn = get_conn()
    c = conn.cursor()
    
    # Total referrals
    c.execute(
        'SELECT COUNT(*) FROM referrals WHERE referrer_id=%s',
        (user_id,)
    )
    total = c.fetchone()[0]
    
    # Converted referrals — who have subscribed
    c.execute(
        'SELECT COUNT(*) FROM referrals WHERE referrer_id=%s AND is_converted=1',
        (user_id,)
    )
    converted = c.fetchone()[0]
    
    conn.close()
    
    return {
        'total': total,
        'converted': converted,
        'pending': total - converted
    }


def apply_referral(referred_id, referral_code):
    """New user applies referral code"""
    # Extract referrer ID from code
    if not referral_code.startswith("REF"):
        return False, "Invalid referral code!"
    
    try:
        referrer_id = int(referral_code.replace("REF", ""))
    except:
        return False, "Invalid referral code!"
    
    # Cannot use your own code
    if referrer_id == referred_id:
        return False, "You cannot use your own referral code!"
    
    conn = get_conn()
    c = conn.cursor()
    
    # Check if already used
    c.execute(
        'SELECT id FROM referrals WHERE referred_id=%s',
        (referred_id,)
    )
    existing = c.fetchone()
    
    if existing:
        conn.close()
        return False, "You have already used a referral code!"
    
    # Save referral
    c.execute(
        'INSERT INTO referrals (referrer_id, referred_id) VALUES (%s, %s)',
        (referrer_id, referred_id)
    )
    conn.commit()
    conn.close()
    
    return True, referrer_id


def reward_referrer(referrer_id):
    """Give referrer 1 month free when referred user subscribes"""
    conn = get_conn()
    c = conn.cursor()
    
    # Check current plan
    c.execute(
        'SELECT plan, plan_expiry FROM users WHERE user_id=%s',
        (referrer_id,)
    )
    user = c.fetchone()
    
    if not user:
        conn.close()
        return
    
    plan, expiry = user
    
    # Add 30 days
    if expiry and datetime.strptime(expiry, '%Y-%m-%d') > datetime.now():
        # Plan is still active — extend by 30 days
        new_expiry = (datetime.strptime(expiry, '%Y-%m-%d') + timedelta(days=30)).strftime('%Y-%m-%d')
    else:
        # No plan or expired — give basic plan for 30 days
        new_expiry = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
        plan = 'basic'
    
    c.execute(
        'UPDATE users SET plan=%s, plan_expiry=%s WHERE user_id=%s',
        (plan, new_expiry, referrer_id)
    )
    
    # Mark referral as converted
    c.execute(
        'UPDATE referrals SET is_converted=1 WHERE referrer_id=%s AND is_converted=0',
        (referrer_id,)
    )
    
    conn.commit()
    conn.close()
    
    return new_expiry
