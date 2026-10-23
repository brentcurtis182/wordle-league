#!/usr/bin/env python3
"""Monday growth & SEO report: search, indexing, site traffic, signups, revenue.

One email every Monday beside the fact-check and division audit, every number
shown as this week / last week / change. Three independent sections, each of
which degrades to a "not connected" note instead of failing the email:

  1. Google Search  - Search Console API (service account, read-only):
                      clicks, impressions, CTR, position overall / per query /
                      per page, the "wordle league" headline, every sitemap
                      URL's index status (vs last week's snapshot), sitemaps.
                      GSC lags ~2-3 days, so its "week" is the latest 7 days
                      Google has, not Mon-Sun.
  2. Site traffic   - Cloudflare Web Analytics (GraphQL, read-only token):
                      visits, page views, pages, referrers, countries, devices.
  3. Product        - our own database: accounts, leagues, players, scores,
                      trials, subscriptions. Mon-Sun Pacific weeks.

Point-in-time values (index status, paying count) are compared against the
previous run's snapshot in growth_report_snapshots.

Environment (each optional; its section says "not connected" without it):
    GSC_SERVICE_ACCOUNT_JSON   the service account key JSON (whole file contents)
    GSC_SITE_URL               default sc-domain:wordplayleague.com
    CF_API_TOKEN               Cloudflare token with Account Analytics: Read
    CF_ACCOUNT_ID              Cloudflare account id
    CF_WEB_ANALYTICS_SITE_TAG  the Web Analytics site tag for wordplayleague.com

Usage:
    python growth_report.py            # build and email
    python growth_report.py --dry-run  # print instead of emailing
    python growth_report.py --html out.html --dry-run   # also write the email HTML
"""
import os
import re
import sys
import json
import logging
import argparse
from datetime import datetime, timedelta, timezone, date

import pytz
import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from league_data_adapter import get_db_connection

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

REPORT_EMAILS = ['brentcurtis182@gmail.com']
PACIFIC = pytz.timezone('America/Los_Angeles')
SITE = 'https://wordplayleague.com'
SITEMAP_URL = f'{SITE}/sitemap.xml'
HEAD_TERM = 'wordle league'
LEGACY_LEAGUE_IDS = (1, 3, 4, 7, 8, 19)  # free forever - mirrors billing.LEGACY_LEAGUE_IDS


# ---------------------------------------------------------------------------
# small helpers
# ---------------------------------------------------------------------------

def last_full_week(today=None):
    """(this_start, this_end, prev_start, prev_end) as Pacific dates: the
    Mon-Sun week that just ended and the one before it."""
    today = today or datetime.now(PACIFIC).date()
    this_start = today - timedelta(days=today.weekday() + 7)
    return this_start, this_start + timedelta(days=6), this_start - timedelta(days=7), this_start - timedelta(days=1)


def delta(cur, prev, lower_is_better=False, fmt='{:+,}'):
    """('+3', 'up'|'down'|'flat'|None) - colour sense flips for position."""
    if cur is None or prev is None:
        return '', None
    d = cur - prev
    if abs(d) < 1e-9:
        return '0', 'flat'
    good = (d < 0) if lower_is_better else (d > 0)
    if isinstance(d, float):
        txt = f'{d:+.1f}'
    else:
        txt = fmt.format(d)
    return txt, 'up' if good else 'down'


# ---------------------------------------------------------------------------
# snapshots (point-in-time values, week over week)
# ---------------------------------------------------------------------------

def _snapshots_table(cur):
    cur.execute("""
        CREATE TABLE IF NOT EXISTS growth_report_snapshots (
            id SERIAL PRIMARY KEY,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            week_start DATE NOT NULL,
            data JSONB NOT NULL
        )
    """)


def load_previous_snapshot(conn, week_start):
    cur = conn.cursor()
    _snapshots_table(cur)
    conn.commit()
    cur.execute("""
        SELECT data FROM growth_report_snapshots
        WHERE week_start < %s ORDER BY week_start DESC, id DESC LIMIT 1
    """, (week_start,))
    row = cur.fetchone()
    return row[0] if row else None


def save_snapshot(conn, week_start, data):
    cur = conn.cursor()
    _snapshots_table(cur)
    cur.execute("DELETE FROM growth_report_snapshots WHERE week_start = %s", (week_start,))
    cur.execute("INSERT INTO growth_report_snapshots (week_start, data) VALUES (%s, %s)",
                (week_start, json.dumps(data, default=str)))
    conn.commit()


# ---------------------------------------------------------------------------
# 1. Google Search Console
# ---------------------------------------------------------------------------

GSC_SCOPE = 'https://www.googleapis.com/auth/webmasters.readonly'


def _gsc_session():
    raw = os.environ.get('GSC_SERVICE_ACCOUNT_JSON')
    if not raw:
        return None
    from google.oauth2 import service_account
    from google.auth.transport.requests import AuthorizedSession
    creds = service_account.Credentials.from_service_account_info(json.loads(raw), scopes=[GSC_SCOPE])
    return AuthorizedSession(creds)


def _gsc_query(sess, site, start, end, dimensions=None, row_limit=250):
    url = f'https://searchconsole.googleapis.com/webmasters/v3/sites/{requests.utils.quote(site, safe="")}/searchAnalytics/query'
    body = {'startDate': str(start), 'endDate': str(end), 'rowLimit': row_limit}
    if dimensions:
        body['dimensions'] = dimensions
    r = sess.post(url, json=body, timeout=60)
    r.raise_for_status()
    return r.json().get('rows', [])


def _gsc_inspect(sess, site, page):
    r = sess.post('https://searchconsole.googleapis.com/v1/urlInspection/index:inspect',
                  json={'inspectionUrl': page, 'siteUrl': site}, timeout=60)
    r.raise_for_status()
    st = r.json().get('inspectionResult', {}).get('indexStatusResult', {})
    return {'verdict': st.get('verdict'), 'coverage': st.get('coverageState'),
            'last_crawl': st.get('lastCrawlTime'), 'google_canonical': st.get('googleCanonical')}


def _sitemap_urls():
    r = requests.get(SITEMAP_URL, timeout=30)
    r.raise_for_status()
    return re.findall(r'<loc>\s*([^<\s]+)\s*</loc>', r.text)


def gather_gsc(prev_snapshot):
    site = os.environ.get('GSC_SITE_URL', 'sc-domain:wordplayleague.com')
    sess = _gsc_session()
    if not sess:
        return {'connected': False}
    out = {'connected': True, 'site': site}

    # The latest day Google has data for; the "week" is the 7 days ending there.
    today = datetime.now(timezone.utc).date()
    days = _gsc_query(sess, site, today - timedelta(days=20), today, ['date'], 50)
    last = max((date.fromisoformat(r['keys'][0]) for r in days), default=today - timedelta(days=3))
    this = (last - timedelta(days=6), last)
    prev = (last - timedelta(days=13), last - timedelta(days=7))
    out['this_range'], out['prev_range'] = this, prev

    def totals(rng):
        rows = _gsc_query(sess, site, rng[0], rng[1])
        r = rows[0] if rows else {}
        return {'clicks': r.get('clicks', 0), 'impressions': r.get('impressions', 0),
                'ctr': r.get('ctr', 0.0), 'position': r.get('position')}

    out['totals'] = {'this': totals(this), 'prev': totals(prev)}

    def by(dim, rng):
        return {r['keys'][0]: r for r in _gsc_query(sess, site, rng[0], rng[1], [dim], 250)}

    for dim in ('query', 'page', 'device', 'country'):
        cur_rows, prev_rows = by(dim, this), by(dim, prev)
        merged = []
        for key in set(cur_rows) | set(prev_rows):
            c, p = cur_rows.get(key, {}), prev_rows.get(key, {})
            merged.append({'key': key,
                           'clicks': c.get('clicks', 0), 'clicks_prev': p.get('clicks', 0),
                           'impressions': c.get('impressions', 0), 'impressions_prev': p.get('impressions', 0),
                           'position': c.get('position'), 'position_prev': p.get('position'),
                           'new': key in cur_rows and key not in prev_rows,
                           'gone': key in prev_rows and key not in cur_rows})
        merged.sort(key=lambda m: (-m['impressions'], -m['impressions_prev']))
        out[dim] = merged

    # Index status of every sitemap URL, compared with last week's snapshot.
    prev_index = (prev_snapshot or {}).get('index', {})
    index = {}
    for u in _sitemap_urls()[:80]:
        try:
            index[u] = _gsc_inspect(sess, site, u)
        except Exception as e:
            index[u] = {'verdict': 'ERROR', 'coverage': str(e)[:120]}
    out['index'] = index
    out['index_prev'] = prev_index

    try:
        r = sess.get(f'https://searchconsole.googleapis.com/webmasters/v3/sites/{requests.utils.quote(site, safe="")}/sitemaps', timeout=60)
        r.raise_for_status()
        out['sitemaps'] = r.json().get('sitemap', [])
    except Exception as e:
        out['sitemaps_error'] = str(e)
    return out


# ---------------------------------------------------------------------------
# 2. Cloudflare Web Analytics
# ---------------------------------------------------------------------------

CF_QUERY = """
query($account: String!, $filter: AccountRumPageloadEventsAdaptiveGroupsFilter_InputObject!) {
  viewer { accounts(filter: {accountTag: $account}) {
    total: rumPageloadEventsAdaptiveGroups(limit: 1, filter: $filter) { count sum { visits } }
    pages: rumPageloadEventsAdaptiveGroups(limit: 40, filter: $filter, orderBy: [count_DESC]) { count sum { visits } dimensions { requestPath } }
    refs: rumPageloadEventsAdaptiveGroups(limit: 25, filter: $filter, orderBy: [count_DESC]) { count sum { visits } dimensions { refererHost } }
    countries: rumPageloadEventsAdaptiveGroups(limit: 10, filter: $filter, orderBy: [count_DESC]) { count sum { visits } dimensions { countryName } }
    devices: rumPageloadEventsAdaptiveGroups(limit: 5, filter: $filter, orderBy: [count_DESC]) { count sum { visits } dimensions { deviceType } }
  } }
}"""


def _cf_week(token, account, site_tag, start, end):
    t0 = PACIFIC.localize(datetime.combine(start, datetime.min.time())).astimezone(timezone.utc)
    t1 = PACIFIC.localize(datetime.combine(end + timedelta(days=1), datetime.min.time())).astimezone(timezone.utc)
    flt = {'siteTag': site_tag, 'datetime_geq': t0.strftime('%Y-%m-%dT%H:%M:%SZ'),
           'datetime_lt': t1.strftime('%Y-%m-%dT%H:%M:%SZ'), 'bot': 0}
    r = requests.post('https://api.cloudflare.com/client/v4/graphql',
                      headers={'Authorization': f'Bearer {token}'},
                      json={'query': CF_QUERY, 'variables': {'account': account, 'filter': flt}}, timeout=60)
    r.raise_for_status()
    body = r.json()
    if body.get('errors'):
        raise RuntimeError('; '.join(e.get('message', '?') for e in body['errors']))
    acct = body['data']['viewer']['accounts'][0]

    def rows(name, dim):
        return {(g['dimensions'][dim] or '(none)'): {'views': g['count'], 'visits': g['sum']['visits']}
                for g in acct[name]}

    tot = acct['total'][0] if acct['total'] else {'count': 0, 'sum': {'visits': 0}}
    return {'views': tot['count'], 'visits': tot['sum']['visits'],
            'pages': rows('pages', 'requestPath'), 'refs': rows('refs', 'refererHost'),
            'countries': rows('countries', 'countryName'), 'devices': rows('devices', 'deviceType')}


def gather_cloudflare(week):
    token, account, site_tag = (os.environ.get(k) for k in ('CF_API_TOKEN', 'CF_ACCOUNT_ID', 'CF_WEB_ANALYTICS_SITE_TAG'))
    if not (token and account and site_tag):
        return {'connected': False}
    this_start, this_end, prev_start, prev_end = week
    return {'connected': True,
            'this': _cf_week(token, account, site_tag, this_start, this_end),
            'prev': _cf_week(token, account, site_tag, prev_start, prev_end)}


# ---------------------------------------------------------------------------
# 3. Product (our database)
# ---------------------------------------------------------------------------

def gather_product(conn, week):
    this_start, this_end, prev_start, prev_end = week
    cur = conn.cursor()

    def utc_bounds(s, e):
        a = PACIFIC.localize(datetime.combine(s, datetime.min.time())).astimezone(timezone.utc).replace(tzinfo=None)
        b = PACIFIC.localize(datetime.combine(e + timedelta(days=1), datetime.min.time())).astimezone(timezone.utc).replace(tzinfo=None)
        return a, b

    def one(sql, params):
        cur.execute(sql, params)
        r = cur.fetchone()
        return r[0] if r and r[0] is not None else 0

    def windowed(s, e):
        a, b = utc_bounds(s, e)
        return {
            'accounts': one("SELECT COUNT(*) FROM users WHERE created_at >= %s AND created_at < %s", (a, b)),
            'leagues_created': one("SELECT COUNT(DISTINCT league_id) FROM user_leagues WHERE created_at >= %s AND created_at < %s", (a, b)),
            'players_added': one("SELECT COUNT(*) FROM players WHERE created_at >= %s AND created_at < %s", (a, b)),
            'scores': one("SELECT COUNT(*) FROM scores WHERE date >= %s AND date <= %s", (s, e)),
            'active_leagues': one("SELECT COUNT(DISTINCT p.league_id) FROM scores s JOIN players p ON p.id = s.player_id "
                                  "WHERE s.date >= %s AND s.date <= %s", (s, e)),
            'active_paid_side': one("SELECT COUNT(DISTINCT p.league_id) FROM scores s JOIN players p ON p.id = s.player_id "
                                    "WHERE s.date >= %s AND s.date <= %s AND p.league_id NOT IN %s", (s, e, LEGACY_LEAGUE_IDS)),
            'active_players': one("SELECT COUNT(DISTINCT s.player_id) FROM scores s WHERE s.date >= %s AND s.date <= %s", (s, e)),
            'subs_started': one("SELECT COUNT(*) FROM subscriptions WHERE created_at >= %s AND created_at < %s", (a, b)),
            'subs_canceled': one("SELECT COUNT(*) FROM subscriptions WHERE status = 'canceled' "
                                 "AND updated_at >= %s AND updated_at < %s", (a, b)),
        }

    a, b = utc_bounds(this_start, this_end)
    cur.execute("""
        SELECT u.created_at, COALESCE(NULLIF(TRIM(COALESCE(u.first_name,'') || ' ' || COALESCE(u.last_name,'')), ''), u.email),
               (SELECT COUNT(*) FROM user_leagues ul WHERE ul.user_id = u.id),
               (SELECT COUNT(*) FROM subscriptions s WHERE s.user_id = u.id)
        FROM users u WHERE u.created_at >= %s AND u.created_at < %s ORDER BY u.created_at
    """, (a, b))
    new_accounts = [{'when': r[0], 'who': r[1], 'leagues': r[2], 'subs': r[3]} for r in cur.fetchall()]

    cur.execute("SELECT status, COUNT(*) FROM subscriptions GROUP BY status")
    subs_now = dict(cur.fetchall())
    connected = one("""SELECT COUNT(*) FROM leagues WHERE twilio_conversation_sid IS NOT NULL
                       OR slack_channel_id IS NOT NULL OR discord_channel_id IS NOT NULL""", ())
    return {'this': windowed(this_start, this_end), 'prev': windowed(prev_start, prev_end),
            'new_accounts': new_accounts,
            'now': {'accounts_total': one("SELECT COUNT(*) FROM users", ()),
                    'leagues_connected': connected,
                    'paying': subs_now.get('active', 0), 'trialing': subs_now.get('trialing', 0),
                    'past_due': subs_now.get('past_due', 0)}}


# ---------------------------------------------------------------------------
# build + render
# ---------------------------------------------------------------------------

def build(dry_run=False):
    week = last_full_week()
    conn = get_db_connection()
    prev_snap = load_previous_snapshot(conn, week[0])
    report = {'week': week, 'prev_snapshot_week': (prev_snap or {}).get('week_start')}
    for name, fn in (('product', lambda: gather_product(conn, week)),
                     ('gsc', lambda: gather_gsc(prev_snap)),
                     ('cf', lambda: gather_cloudflare(week))):
        try:
            report[name] = fn()
        except Exception as e:
            logging.exception(f"growth report section {name} failed")
            conn.rollback()
            report[name] = {'connected': True, 'error': f'{type(e).__name__}: {e}'[:400]}
    report['prev_now'] = (prev_snap or {}).get('product_now')
    if not dry_run:
        save_snapshot(conn, week[0], {
            'week_start': str(week[0]),
            'index': (report.get('gsc') or {}).get('index', {}),
            'product_now': (report.get('product') or {}).get('now'),
            'head_term_position': _head_term(report).get('position'),
        })
    conn.close()
    return report


def _head_term(report):
    for q in (report.get('gsc') or {}).get('query', []):
        if q['key'].strip().lower() == HEAD_TERM:
            return q
    return {}


def _indexed(st):
    return (st or {}).get('verdict') == 'PASS'


def summary_lines(report):
    out = []
    g, cf, p = report.get('gsc') or {}, report.get('cf') or {}, report.get('product') or {}
    h = _head_term(report)
    if h.get('position'):
        prev = h.get('position_prev')
        move = f"from {prev:.1f} " if prev else ''
        out.append(f'"{HEAD_TERM}" average position {move}to {h["position"]:.1f} ({h["impressions"]} impressions).')
    elif g.get('connected') and not g.get('error'):
        out.append(f'No impressions for "{HEAD_TERM}" in the latest 7 days of Search Console data.')
    if g.get('totals'):
        t, pv = g['totals']['this'], g['totals']['prev']
        out.append(f"Google: {t['clicks']} clicks ({delta(t['clicks'], pv['clicks'])[0]}), "
                   f"{t['impressions']} impressions ({delta(t['impressions'], pv['impressions'])[0]}).")
    if g.get('index'):
        now_idx = sum(1 for s in g['index'].values() if _indexed(s))
        newly = [u for u, s in g['index'].items() if _indexed(s) and g['index_prev'] and not _indexed(g['index_prev'].get(u))]
        dropped = [u for u, s in g['index'].items() if not _indexed(s) and _indexed(g['index_prev'].get(u))]
        line = f"{now_idx} of {len(g['index'])} sitemap pages indexed."
        if newly:
            line += f" Newly indexed: {', '.join(_short(u) for u in newly)}."
        if dropped:
            line += f" DROPPED: {', '.join(_short(u) for u in dropped)}."
        out.append(line)
    if cf.get('this'):
        t, pv = cf['this'], cf['prev']
        top_ref = next((k for k in t['refs'] if k not in ('(none)', 'wordplayleague.com')), None)
        out.append(f"Site: {t['visits']} visits ({delta(t['visits'], pv['visits'])[0]}), {t['views']} page views"
                   + (f"; top outside referrer {top_ref}." if top_ref else '.'))
    if p.get('this'):
        t = p['this']
        out.append(f"{t['accounts']} new account{'s' if t['accounts'] != 1 else ''}, {t['leagues_created']} league"
                   f"{'s' if t['leagues_created'] != 1 else ''} created, {t['subs_started']} subscription"
                   f"{'s' if t['subs_started'] != 1 else ''} started.")
    return out


def _short(u):
    return u.replace('https://wordplayleague.com', '') or '/'


def _esc(s):
    return str(s).replace('&', '&amp;').replace('<', '&lt;')


def render_html(report):
    ok_c, bad_c, mute, txt = '#2ecc71', '#e74c3c', '#9a9ab0', '#e8e8f0'
    colours = {'up': ok_c, 'down': bad_c, 'flat': mute, None: mute}
    this_start, this_end, prev_start, prev_end = report['week']
    h = [f'<div style="font-family:system-ui,-apple-system,sans-serif;max-width:760px;margin:0 auto;padding:24px;background:#12121c;color:{txt};">']
    h.append('<h1 style="margin:0 0 4px;font-size:22px;">Growth &amp; SEO Report</h1>')
    h.append(f'<div style="color:{mute};font-size:13px;margin-bottom:20px;">Week of {this_start:%b %d}&ndash;{this_end:%b %d} vs {prev_start:%b %d}&ndash;{prev_end:%b %d}</div>')

    def section(title, sub=None):
        h.append(f'<div style="font-size:12px;color:{mute};text-transform:uppercase;letter-spacing:.06em;margin:26px 0 8px;">{_esc(title)}</div>')
        if sub:
            h.append(f'<div style="font-size:12px;color:#6a6a80;margin:-4px 0 8px;">{sub}</div>')

    def note(text, colour=mute):
        h.append(f'<div style="font-size:13px;color:{colour};margin:4px 0 8px;">{text}</div>')

    def tiles(items):
        h.append('<table style="width:100%;border-collapse:separate;border-spacing:6px;margin:0 -6px;"><tr>')
        for label, cur, prev, lower in items:
            d, sense = delta(cur, prev, lower)
            shown = f'{cur:.1f}' if isinstance(cur, float) else (f'{cur:,}' if cur is not None else '&ndash;')
            h.append(f'<td style="background:#1b1b28;border-radius:8px;padding:12px;vertical-align:top;">'
                     f'<div style="font-size:11px;color:{mute};text-transform:uppercase;letter-spacing:.05em;">{_esc(label)}</div>'
                     f'<div style="font-size:22px;font-weight:700;margin:4px 0;color:{txt};">{shown}</div>'
                     f'<div style="font-size:12px;color:{colours[sense]};">{d or "&nbsp;"}'
                     f'{" vs " + (f"{prev:.1f}" if isinstance(prev, float) else f"{prev:,}") if prev is not None else ""}</div></td>')
        h.append('</tr></table>')

    def table(headers, rows):
        h.append('<table style="width:100%;border-collapse:collapse;font-size:13px;margin-bottom:8px;">')
        h.append('<tr>' + ''.join(f'<th style="text-align:{"left" if i == 0 else "right"};color:{mute};font-weight:500;padding:5px 6px;border-bottom:1px solid #26263a;">{_esc(x)}</th>'
                                  for i, x in enumerate(headers)) + '</tr>')
        for row in rows:
            h.append('<tr>' + ''.join(
                f'<td style="text-align:{"left" if i == 0 else "right"};padding:5px 6px;border-bottom:1px solid #1f1f2e;'
                f'color:{colours.get(c[1], txt) if isinstance(c, tuple) else txt};{"word-break:break-all;" if i == 0 else "white-space:nowrap;"}">'
                f'{c[0] if isinstance(c, tuple) else c}</td>' for i, c in enumerate(row)) + '</tr>')
        h.append('</table>')

    # summary
    lines = summary_lines(report)
    h.append('<div style="background:#1b1b28;border-left:4px solid #00E8DA;border-radius:6px;padding:14px 16px;font-size:14px;line-height:1.7;">'
             + ('<br>'.join(_esc(l) for l in lines) or 'Nothing to summarise yet.') + '</div>')

    # --- Google Search ---
    g = report.get('gsc') or {}
    section('Google Search',
            f"Search Console, {g['this_range'][0]:%b %d}&ndash;{g['this_range'][1]:%b %d} vs "
            f"{g['prev_range'][0]:%b %d}&ndash;{g['prev_range'][1]:%b %d} (Google's data runs ~2&ndash;3 days behind)"
            if g.get('this_range') else None)
    if not g.get('connected'):
        note('Not connected yet: needs GSC_SERVICE_ACCOUNT_JSON on the cron service.', '#f39c12')
    elif g.get('error'):
        note(f'Search Console failed: {_esc(g["error"])}', bad_c)
    else:
        t, pv = g['totals']['this'], g['totals']['prev']
        tiles([('Clicks', t['clicks'], pv['clicks'], False), ('Impressions', t['impressions'], pv['impressions'], False),
               ('CTR %', round(t['ctr'] * 100, 1), round(pv['ctr'] * 100, 1), False),
               ('Avg position', round(t['position'], 1) if t['position'] else None,
                round(pv['position'], 1) if pv['position'] else None, True)])

        def qrow(q):
            pos = f"{q['position']:.1f}" if q['position'] else '&ndash;'
            pd, ps = delta(q['position'], q['position_prev'], True)
            tag = ' <span style="color:#00E8DA;font-size:11px;">NEW</span>' if q['new'] else (
                ' <span style="color:#6a6a80;font-size:11px;">gone</span>' if q['gone'] else '')
            name = _esc(_short(q['key'])) + tag
            if q['key'].strip().lower() == HEAD_TERM:
                name = f'<strong style="color:#00E8DA;">{name}</strong>'
            idd, ids = delta(q['impressions'], q['impressions_prev'])
            return [name, q['clicks'], (f"{q['impressions']} <span style='font-size:11px'>{idd}</span>", ids), (f"{pos} <span style='font-size:11px'>{pd}</span>", ps)]

        section('Queries', 'Position: lower is better. Green = improved.')
        table(['Query', 'Clicks', 'Impr.', 'Position'], [qrow(q) for q in g['query'][:30]])
        section('Pages in Google')
        table(['Page', 'Clicks', 'Impr.', 'Position'], [qrow(q) for q in g['page'][:25]])
        dev = ', '.join(f"{d['key'].lower()} {d['impressions']}" for d in g['device'] if d['impressions'])
        ctry = ', '.join(f"{d['key'].upper()} {d['impressions']}" for d in g['country'][:6] if d['impressions'])
        note(f'Impressions by device: {dev or "none"}. Top countries: {ctry or "none"}.')

        section('Indexing', 'Every URL in the sitemap, inspected live. Compared with last week where a snapshot exists.')
        rows = []
        for u, st in sorted(g['index'].items(), key=lambda kv: (_indexed(kv[1]), kv[0])):
            was = g['index_prev'].get(u)
            change = ''
            if was is not None and _indexed(was) != _indexed(st):
                change = ('newly indexed', 'up') if _indexed(st) else ('DROPPED', 'down')
            crawl = (st.get('last_crawl') or '')[:10] or '&ndash;'
            rows.append([_esc(_short(u)), ((st.get('coverage') or st.get('verdict') or '?'), 'up' if _indexed(st) else 'down'),
                         crawl, change])
        table(['URL', 'Status', 'Last crawl', 'Change'], rows)
        for sm in g.get('sitemaps', []):
            note(f"Sitemap {_esc(sm.get('path'))}: last read {(sm.get('lastDownloaded') or '?')[:10]}, "
                 f"{sm.get('errors', 0)} errors, {sm.get('warnings', 0)} warnings.")

    # --- Site traffic ---
    cf = report.get('cf') or {}
    section('Website traffic', 'Cloudflare Web Analytics: real visitors (no bots, no cookies), Mon&ndash;Sun Pacific.')
    if not cf.get('connected'):
        note('Not connected yet: needs CF_API_TOKEN, CF_ACCOUNT_ID and CF_WEB_ANALYTICS_SITE_TAG on the cron service.', '#f39c12')
    elif cf.get('error'):
        note(f'Cloudflare failed: {_esc(cf["error"])}', bad_c)
    else:
        t, pv = cf['this'], cf['prev']
        tiles([('Visits', t['visits'], pv['visits'], False), ('Page views', t['views'], pv['views'], False)])

        def merged(key, n):
            names = sorted(set(t[key]) | set(pv[key]), key=lambda k: -t[key].get(k, {}).get('views', 0))[:n]
            out = []
            for k in names:
                c, p = t[key].get(k, {}).get('views', 0), pv[key].get(k, {}).get('views', 0)
                d, s = delta(c, p)
                out.append([_esc(k), c, (d, s)])
            return out

        section('Top pages')
        table(['Page', 'Views', 'Change'], merged('pages', 20))
        section('Where visitors came from')
        table(['Referrer', 'Views', 'Change'], merged('refs', 15))
        section('Countries / devices')
        table(['Country', 'Views', 'Change'], merged('countries', 8))
        table(['Device', 'Views', 'Change'], merged('devices', 4))

    # --- Product ---
    p = report.get('product') or {}
    section('Signups & revenue', 'Our database, Mon&ndash;Sun Pacific.')
    if p.get('error'):
        note(f'Database section failed: {_esc(p["error"])}', bad_c)
    elif p.get('this'):
        t, pv = p['this'], p['prev']
        tiles([('New accounts', t['accounts'], pv['accounts'], False),
               ('Leagues created', t['leagues_created'], pv['leagues_created'], False),
               ('Subs started', t['subs_started'], pv['subs_started'], False),
               ('Subs canceled', t['subs_canceled'], pv['subs_canceled'], True)])
        tiles([('Active leagues', t['active_leagues'], pv['active_leagues'], False),
               ('…non-legacy', t['active_paid_side'], pv['active_paid_side'], False),
               ('Active players', t['active_players'], pv['active_players'], False),
               ('Scores posted', t['scores'], pv['scores'], False)])
        now, was = p['now'], report.get('prev_now') or {}
        tiles([('Paying', now['paying'], was.get('paying'), False), ('Trialing', now['trialing'], was.get('trialing'), False),
               ('Connected leagues', now['leagues_connected'], was.get('leagues_connected'), False),
               ('Accounts (total)', now['accounts_total'], was.get('accounts_total'), False)])
        if p['new_accounts']:
            section('New accounts this week')
            table(['Who', 'Signed up (Pacific)', 'Leagues', 'Subs'],
                  [[_esc(a['who']), pytz.utc.localize(a['when']).astimezone(PACIFIC).strftime('%a %b %d %I:%M %p'),
                    a['leagues'], a['subs']] for a in p['new_accounts']])
        if not report.get('prev_now'):
            note('Paying / trialing / connected / total compare against last week’s snapshot, starting next week.')

    h.append(f'<div style="color:#6a6a80;font-size:11px;margin-top:28px;">Generated {datetime.now(timezone.utc):%Y-%m-%d %H:%M UTC} '
             '&middot; Search Console API, Cloudflare Web Analytics, WordPlayLeague database.</div></div>')
    return ''.join(h).encode('ascii', 'xmlcharrefreplace').decode('ascii')


def send(report, dry_run=False, html_path=None):
    this_start = report['week'][0]
    h = _head_term(report)
    pos = f' · "{HEAD_TERM}" {h["position"]:.1f}' if h.get('position') else ''
    subject = f"[WordPlayLeague] Growth & SEO — week of {this_start:%b %d}{pos}"
    html = render_html(report)
    if html_path:
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html)
    if dry_run:
        print(f"\nSUBJECT: {subject}\n")
        for line in summary_lines(report):
            print(' -', line)
        for name in ('gsc', 'cf', 'product'):
            sec = report.get(name) or {}
            state = 'error: ' + sec['error'] if sec.get('error') else ('connected' if sec.get('connected', True) else 'NOT CONNECTED')
            print(f"   [{name}] {state}")
        print("\n(dry run — no email sent, no snapshot saved)")
        return
    try:
        from email_utils import _send_email_sync
        for addr in REPORT_EMAILS:
            _send_email_sync(addr, subject, html)
            logging.info(f"Growth report emailed to {addr}")
    except Exception as e:
        logging.error(f"Failed to send growth report: {e}")


def run_report(dry_run=False, html_path=None):
    report = build(dry_run=dry_run)
    send(report, dry_run=dry_run, html_path=html_path)
    return report


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true', help='print instead of emailing; no snapshot saved')
    ap.add_argument('--html', help='also write the email HTML to this path')
    args = ap.parse_args()
    run_report(dry_run=args.dry_run, html_path=args.html)


if __name__ == '__main__':
    main()
