"""Player reviews.

Players do not have accounts — that is the whole product — so the form asks
for nothing but a first name and the review itself. Requiring a login to leave
one would contradict the thing being reviewed.

Everything lands hidden. Nothing is public until it is approved in the admin
panel, so there is no window where an unseen review is live. Approved reviews
are baked into the marketing site by a generator rather than fetched at
runtime, so a caching mistake cannot surface an unapproved one either.

Deliberately NOT doing: aggregate star-rating schema on our own pages. Google
treats self-serving review markup as a violation. The rating here is for our
own sorting.

Everything lives in a Blueprint so twilio_webhook_app.py needs two lines
rather than another 200 in a file that is already 12,600 long.
"""
import hashlib
import html
import logging
import os

from flask import Blueprint, request, redirect

reviews_bp = Blueprint('reviews', __name__)

MAX_BODY = 600
MAX_NAME = 40
RATE_LIMIT_PER_HOUR = 3

CYAN = "#00E8DA"


# ── storage ────────────────────────────────────────────────────────────────

def ensure_reviews_table(cursor):
    """Create the table if absent. Idempotent, and called at point of use
    rather than on boot — startup migrations in this app have a history of
    firing on every deploy and quietly undoing things."""
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reviews (
            id SERIAL PRIMARY KEY,
            league_id INTEGER REFERENCES leagues(id) ON DELETE SET NULL,
            display_name TEXT,
            body TEXT NOT NULL,
            rating SMALLINT,
            approved BOOLEAN NOT NULL DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            approved_at TIMESTAMP,
            submitter_hash TEXT
        )
    """)
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_reviews_approved
        ON reviews (approved, created_at DESC)
    """)


def _submitter_hash(remote_addr, user_agent):
    """Coarse identifier for rate limiting. Hashed rather than stored raw —
    there is no reason to keep a visitor's IP, and it only has to be stable
    for an hour."""
    salt = os.environ.get('REVIEW_SALT', 'wpl-reviews')
    raw = f"{remote_addr or ''}|{(user_agent or '')[:120]}|{salt}"
    return hashlib.sha256(raw.encode()).hexdigest()[:32]


def _clean(text, limit):
    return ' '.join(str(text or '').split())[:limit]


def fetch_for_admin(cursor, limit=200):
    ensure_reviews_table(cursor)
    cursor.execute("""
        SELECT r.id, r.display_name, r.body, r.rating, r.approved,
               r.created_at, COALESCE(l.display_name, l.name, '-')
        FROM reviews r
        LEFT JOIN leagues l ON l.id = r.league_id
        ORDER BY r.approved ASC, r.created_at DESC
        LIMIT %s
    """, (limit,))
    return cursor.fetchall()


# ── page chrome ────────────────────────────────────────────────────────────

def _page(title, inner):
    return f"""<!DOCTYPE html>
<html lang="en"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)} — WordPlayLeague</title>
<meta name="robots" content="noindex, nofollow">
<style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:'Segoe UI',system-ui,-apple-system,sans-serif;background:#06060e;color:#d7dadc;
 padding:28px 18px;min-height:100vh;display:flex;align-items:flex-start;justify-content:center;
 background-image:radial-gradient(ellipse 60% 40% at 10% -10%,rgba(0,232,218,0.07),transparent 70%),
 radial-gradient(ellipse 60% 40% at 90% 110%,rgba(168,85,247,0.06),transparent 70%)}}
.card{{width:100%;max-width:520px;background:rgba(16,16,36,0.72);border:1px solid rgba(255,255,255,0.09);
 border-radius:16px;padding:26px 24px;box-shadow:0 10px 40px rgba(0,0,0,.5)}}
h1{{font-size:1.45rem;letter-spacing:-.02em;margin-bottom:6px;color:#e9ecef}}
.sub{{color:#8a8aa5;font-size:.9rem;line-height:1.55;margin-bottom:20px}}
label{{display:block;font-size:.76rem;letter-spacing:.09em;text-transform:uppercase;
 color:#8a8aa5;margin:16px 0 6px;font-weight:600}}
input[type=text],textarea{{width:100%;background:#0d0d18;border:1px solid rgba(255,255,255,.12);
 border-radius:10px;padding:11px 13px;color:#e9ecef;font:inherit;font-size:.98rem}}
input[type=text]:focus,textarea:focus{{outline:none;border-color:{CYAN}}}
textarea{{min-height:130px;resize:vertical;line-height:1.55}}
.stars{{display:flex;gap:8px;margin-top:4px}}
.stars input{{position:absolute;opacity:0;width:0;height:0}}
.stars label{{margin:0;cursor:pointer;font-size:1.5rem;line-height:1;filter:grayscale(1);opacity:.45;
 transition:filter .12s,opacity .12s;text-transform:none;letter-spacing:0}}
.stars input:checked + label,.stars label:hover{{filter:none;opacity:1}}
button{{width:100%;margin-top:22px;padding:13px;border:0;border-radius:10px;background:{CYAN};
 color:#06060e;font:inherit;font-weight:800;font-size:1rem;cursor:pointer}}
button:hover{{opacity:.9}}
.hp{{position:absolute;left:-9999px;width:1px;height:1px;overflow:hidden}}
.note{{margin-top:16px;font-size:.78rem;color:#6f6f88;line-height:1.55}}
.err{{background:rgba(255,92,92,.12);border:1px solid rgba(255,92,92,.4);color:#ff9b9b;
 border-radius:9px;padding:10px 12px;font-size:.88rem;margin-bottom:16px}}
.ok{{font-size:2.6rem;margin-bottom:10px}}
a{{color:{CYAN}}}
</style></head><body><div class="card">{inner}</div></body></html>"""


def _form(slug, league_name, error=None, name='', body=''):
    err = f'<div class="err">{html.escape(error)}</div>' if error else ''
    where = f" in <b>{html.escape(league_name)}</b>" if league_name else ""
    stars = ''.join(
        f'<input type="radio" id="r{n}" name="rating" value="{n}">'
        f'<label for="r{n}" title="{n} out of 5">&#11088;</label>'
        for n in range(1, 6))
    return _page("Leave a review", f"""
<h1>How's your league going?</h1>
<p class="sub">You're playing{where}. Tell us what it's like — a sentence is plenty.
 No account needed, and we'll only put it on the site if you're happy for us to.</p>
{err}
<form method="post">
  <label for="name">Your first name <span style="text-transform:none;letter-spacing:0">(optional)</span></label>
  <input type="text" id="name" name="name" maxlength="{MAX_NAME}" value="{html.escape(name)}"
         autocomplete="given-name" placeholder="Dani">
  <label>How much do you like it?</label>
  <div class="stars">{stars}</div>
  <label for="body">Your review</label>
  <textarea id="body" name="body" maxlength="{MAX_BODY}" required
            placeholder="What it's actually like to play in the league.">{html.escape(body)}</textarea>
  <div class="hp" aria-hidden="true">
    <label for="website">Leave this empty</label>
    <input type="text" id="website" name="website" tabindex="-1" autocomplete="off">
  </div>
  <button type="submit">Send it</button>
</form>
<p class="note">We may show your review and first name on wordplayleague.com.
 Nothing else is collected — no email, no account.</p>
""")


# ── public routes ──────────────────────────────────────────────────────────

@reviews_bp.route('/review/<slug>', methods=['GET', 'POST'])
def leave_review(slug):
    from auth import get_db_connection

    conn = cursor = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, COALESCE(display_name, name) FROM leagues WHERE slug = %s",
            (slug,))
        row = cursor.fetchone()
        if not row:
            return _page("Not found", "<h1>League not found</h1>"
                         "<p class='sub'>Check the link and try again.</p>"), 404
        league_id, league_name = row

        if request.method == 'GET':
            return _page_or_form(slug, league_name)

        # Honeypot: a bot fills every field it finds. Accept and drop, so it
        # cannot tell the submission failed and retry differently.
        if _clean(request.form.get('website'), 40):
            logging.info(f"Review honeypot tripped for {slug}")
            return _thanks(league_name)

        body = _clean(request.form.get('body'), MAX_BODY)
        if len(body) < 10:
            return _form(slug, league_name,
                         "A few more words would help — at least a sentence.",
                         _clean(request.form.get('name'), MAX_NAME), body)

        ensure_reviews_table(cursor)
        who = _submitter_hash(request.headers.get('X-Forwarded-For', request.remote_addr),
                              request.headers.get('User-Agent'))
        cursor.execute("""
            SELECT COUNT(*) FROM reviews
            WHERE submitter_hash = %s AND created_at > now() - interval '1 hour'
        """, (who,))
        if (cursor.fetchone() or [0])[0] >= RATE_LIMIT_PER_HOUR:
            return _form(slug, league_name,
                         "That's a few reviews in a row — try again a bit later.")

        rating = request.form.get('rating')
        rating = int(rating) if (rating or '').isdigit() and 1 <= int(rating) <= 5 else None

        cursor.execute("""
            INSERT INTO reviews (league_id, display_name, body, rating, submitter_hash)
            VALUES (%s, %s, %s, %s, %s) RETURNING id
        """, (league_id, _clean(request.form.get('name'), MAX_NAME) or None,
              body, rating, who))
        new_id = cursor.fetchone()[0]
        conn.commit()
        logging.info(f"Review #{new_id} submitted for league {league_id} ({slug})")
        return _thanks(league_name)

    except Exception as e:
        if conn:
            conn.rollback()
        logging.error(f"Review submission failed for {slug}: {e}", exc_info=True)
        return _page("Something went wrong",
                     "<h1>That didn't send</h1><p class='sub'>Sorry — try again in a moment.</p>"), 500
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()


def _page_or_form(slug, league_name):
    return _form(slug, league_name)


def _thanks(league_name):
    return _page("Thanks", """
<div class="ok">&#127881;</div>
<h1>Thanks — got it.</h1>
<p class="sub">We read every one. If we use it on the site it'll show with your
 first name and your league, nothing else.</p>
<p class="note"><a href="https://wordplayleague.com/">wordplayleague.com</a></p>
""")


# ── admin ──────────────────────────────────────────────────────────────────

@reviews_bp.route('/admin/reviews/<int:review_id>/<action>', methods=['POST'])
def admin_set_review(review_id, action):
    from auth import validate_session, get_db_connection

    user = validate_session(request.cookies.get('session_token'))
    if not user or user.get('role') != 'admin':
        return redirect('/auth/login')
    if action not in ('approve', 'hide', 'delete'):
        return redirect('/admin/dashboard#reviews')

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        ensure_reviews_table(cursor)
        if action == 'delete':
            cursor.execute("DELETE FROM reviews WHERE id = %s", (review_id,))
        else:
            approved = action == 'approve'
            cursor.execute("""
                UPDATE reviews
                SET approved = %s,
                    approved_at = CASE WHEN %s THEN CURRENT_TIMESTAMP ELSE NULL END
                WHERE id = %s
            """, (approved, approved, review_id))
        conn.commit()
        logging.info(f"Review {review_id}: {action} by admin {user.get('id')}")
    except Exception as e:
        conn.rollback()
        logging.error(f"Review {action} failed for {review_id}: {e}")
    finally:
        cursor.close()
        conn.close()
    return redirect('/admin/dashboard#reviews')


@reviews_bp.route('/admin/reviews.json')
def admin_reviews_json():
    """Approved reviews, for the marketing site generator to bake in."""
    from flask import jsonify
    from auth import validate_session, get_db_connection

    user = validate_session(request.cookies.get('session_token'))
    token = request.args.get('key')
    expected = os.environ.get('REVIEWS_EXPORT_KEY')
    authorised = (user and user.get('role') == 'admin') or (expected and token == expected)
    if not authorised:
        return jsonify({'error': 'unauthorised'}), 403

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        ensure_reviews_table(cursor)
        cursor.execute("""
            SELECT r.display_name, r.body, r.rating,
                   COALESCE(l.display_name, l.name), r.approved_at
            FROM reviews r LEFT JOIN leagues l ON l.id = r.league_id
            WHERE r.approved = TRUE
            ORDER BY r.approved_at DESC
        """)
        out = [{'name': n or 'A player', 'body': b, 'rating': rt,
                'league': lg or '', 'at': at.isoformat() if at else None}
               for n, b, rt, lg, at in cursor.fetchall()]
        return jsonify({'reviews': out})
    finally:
        cursor.close()
        conn.close()
