"""Where signups come from, and how many people reach the signup pages.

The marketing site (wordplayleague.com/attribution.js) remembers each
visitor's first touch - referring site, landing page, utm_* tags - and adds
it, plus which button was clicked, to every link into the app's auth pages:

    /auth/register?wpl_ref=google.com&wpl_land=/wordle-stats&wpl_cta=/#hero&utm_source=...

Here:
  - every GET of a tracked auth page is logged to signup_funnel_events
    ("arrival"), so the Monday report can show arrivals by source and button
    next to accounts created (the click-through / conversion numbers)
  - the first touch is kept in a first-party cookie (wpl_src, 60 days, never
    overwritten) so it survives the email-verification round trip and Google
    sign-in
  - when an account is created, its source is stamped on users.signup_source
    (short label) and users.signup_detail (everything we know)

A logged-out Slack install lands on /auth/register?slack_installed=1, so with
no other source it is labelled slack_app_directory. Arrivals with nothing at
all are 'direct' (or the referring host, when the browser sends one).

Everything here is fail-safe: tracking can never break a login or signup.
"""
import json
import logging
from urllib.parse import urlparse

COOKIE = 'wpl_src'
COOKIE_DAYS = 60
TRACKED_PATHS = ('/auth/register', '/auth/login', '/auth/google', '/slack/install')
OWN_HOSTS = {'wordplayleague.com', 'app.wordplayleague.com', 'staging.wordplayleague.com'}


def ensure_schema(cursor):
    cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS signup_source TEXT")
    cursor.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS signup_detail JSONB")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS signup_funnel_events (
            id SERIAL PRIMARY KEY,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            event VARCHAR(32) NOT NULL,
            page VARCHAR(64),
            source TEXT,
            cta TEXT,
            detail JSONB
        )
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_signup_funnel_events_created ON signup_funnel_events (created_at)")


def _host(url):
    try:
        h = (urlparse(url).hostname or '').lower()
    except Exception:
        return ''
    return h[4:] if h.startswith('www.') else h


def _source_label(d):
    if d.get('utm_source'):
        return d['utm_source'].strip().lower()[:64]
    ref = (d.get('ref') or '').strip().lower()
    if ref and ref != 'direct':
        return ref[:64]
    if d.get('slack_installed'):
        return 'slack_app_directory'
    return 'direct'


def describe_request(req):
    """What this auth-page request tells us about where the visitor came from."""
    a = req.args
    d = {k: a.get(k, '')[:200] for k in ('utm_source', 'utm_medium', 'utm_campaign') if a.get(k)}
    # An ad that links straight to the app: credit it by the platform's click
    # id when untagged (same rules as the marketing site's attribution.js).
    if not d.get('utm_source'):
        if a.get('gclid') or a.get('gbraid') or a.get('wbraid'):
            d.update(utm_source='google-ads', utm_medium='cpc')
        elif a.get('msclkid'):
            d.update(utm_source='bing-ads', utm_medium='cpc')
        elif a.get('fbclid'):
            d.update(utm_source='facebook', utm_medium='social')
    if a.get('wpl_ref'):
        d['ref'] = a.get('wpl_ref')[:100]
    else:
        # Not from our site's decorated links: use the browser's referrer if
        # it is someone else's site.
        h = _host(req.referrer or '')
        if h and h not in OWN_HOSTS:
            d['ref'] = h
    if a.get('wpl_land'):
        d['landing'] = a.get('wpl_land')[:200]
    if a.get('wpl_cta'):
        d['cta'] = a.get('wpl_cta')[:200]
    if a.get('slack_installed'):
        d['slack_installed'] = True
    d['source'] = _source_label(d)
    return d


def track_arrival(req, get_db_connection):
    """Log a GET of a tracked auth page. Returns the cookie value to set (first
    touch), or None when the visitor already has one."""
    try:
        if req.method != 'GET' or not req.path.startswith(TRACKED_PATHS):
            return None
        d = describe_request(req)
        existing = req.cookies.get(COOKIE)
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO signup_funnel_events (event, page, source, cta, detail)
                VALUES ('arrival', %s, %s, %s, %s)
            """, (req.path[:64], d['source'], d.get('cta'), json.dumps(d)))
            conn.commit()
            cur.close()
        finally:
            conn.close()
        if existing:
            return None
        return json.dumps(d, separators=(',', ':'))
    except Exception as e:
        logging.warning(f"signup arrival tracking skipped: {e}")
        return None


def set_cookie(response, value):
    try:
        response.set_cookie(COOKIE, value, max_age=COOKIE_DAYS * 24 * 3600,
                            httponly=True, secure=True, samesite='Lax')
    except Exception as e:
        logging.warning(f"signup source cookie not set: {e}")


def record_signup(req, get_db_connection, user_id=None, email=None, pending_cookie=None):
    """Stamp a just-created account with its source. Only touches an account
    created in the last hour that has no source yet, so calling this after a
    plain login of an old account does nothing."""
    try:
        raw = pending_cookie or req.cookies.get(COOKIE)
        d = json.loads(raw) if raw else describe_request(req)
        source = d.get('source') or _source_label(d)
        conn = get_db_connection()
        try:
            cur = conn.cursor()
            where, val = ('id = %s', user_id) if user_id else ('LOWER(email) = LOWER(%s)', email)
            cur.execute(f"""
                UPDATE users SET signup_source = %s, signup_detail = %s
                WHERE {where} AND signup_source IS NULL
                  AND created_at > (NOW() AT TIME ZONE 'UTC') - INTERVAL '1 hour'
                RETURNING id
            """, (source, json.dumps(d), val))
            stamped = cur.fetchone()
            if stamped:
                cur.execute("""
                    INSERT INTO signup_funnel_events (event, page, source, cta, detail)
                    VALUES ('signup', %s, %s, %s, %s)
                """, (req.path[:64], source, d.get('cta'), json.dumps(d)))
            conn.commit()
            cur.close()
        finally:
            conn.close()
    except Exception as e:
        logging.warning(f"signup source not recorded: {e}")
