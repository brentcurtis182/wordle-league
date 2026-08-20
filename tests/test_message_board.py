"""
Community message board (/embed/message-board) tests.

The board is an iframed page on the marketing site, so it never shares the
dashboard's chrome -- and until now nothing in this suite touched /embed/ at
all. These tests cover the author path (create / edit / reply) and the
admin path (pin / FAQ / delete).

Two of them guard a specific bug fixed 2026-08-20:

  - a post whose body is empty could not be saved at all, because both the
    client and the server required a non-empty body. Posts that keep their
    content in the first reply were therefore stuck with their original
    subject forever.
  - the failure was invisible. Validation used a position:fixed toast, which
    renders off-screen inside a content-height iframe, so Save just looked
    like a dead button. Errors now render inline, and the tests assert on the
    inline element specifically -- a toast-only regression would fail here.

Every post created here is prefixed with PREFIX so the module teardown can
find and delete it. Deletion is admin-only, so the staging test account must
have role='admin' (promoted 2026-08-20).
"""

import re
import time

import pytest
from playwright.sync_api import expect

# Unique per run so parallel/repeat runs don't collide, and so teardown only
# ever deletes posts this run created.
_TS = str(int(time.time()))[-6:]
PREFIX = f"ZZTest {_TS}"

BOARD = "/embed/message-board"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _create_post(page, base_url, subject, body=""):
    """Create a post through the UI. Returns its post id."""
    page.goto(f"{base_url}{BOARD}")
    page.wait_for_load_state("networkidle")
    page.click(".new-post-btn")
    page.fill("#postSubject", subject)
    if body:
        page.fill("#postBody", body)
    page.click('#newPostForm button:has-text("Submit")')
    page.wait_for_url("**/embed/message-board/post/**", timeout=10000)
    return int(page.url.split("/post/")[1].split("?")[0].split("#")[0])


def _delete_post(page, base_url, post_id):
    """Delete a post via the admin control, accepting the confirm() dialog."""
    page.goto(f"{base_url}{BOARD}/post/{post_id}")
    page.wait_for_load_state("networkidle")
    btn = page.locator('.admin-btn:text-is("Delete")')
    if btn.count() == 0:
        return False
    page.once("dialog", lambda d: d.accept())
    btn.click()
    page.wait_for_url(f"**{BOARD}", timeout=10000)
    return True


def _open_post_edit(page):
    """Open the post edit form (the Edit button inside the post card)."""
    page.locator("#postView .edit-btn").click()
    page.wait_for_selector("#postEditForm", state="visible")


def _save_post_edit(page, expect_reload=True):
    """Save the post edit form.

    A successful save reloads the page, so the click has to be awaited as a
    navigation -- otherwise assertions race the reload and read stale text, and
    the next goto() gets cancelled with ERR_ABORTED. Validation failures do not
    navigate, hence expect_reload=False.
    """
    btn = page.locator('#postEditForm button:has-text("Save")')
    if expect_reload:
        with page.expect_navigation(wait_until="load", timeout=10000):
            btn.click()
    else:
        btn.click()


def _click_admin(page, label):
    """Click an admin control by exact label and wait out the reload."""
    with page.expect_navigation(wait_until="load", timeout=10000):
        page.locator(f'.admin-btn:text-is("{label}")').click()


def _submit_reply(page, text):
    """Post a reply; like saving, this reloads the page."""
    page.fill("#replyBody", text)
    with page.expect_navigation(wait_until="load", timeout=10000):
        page.click('button:has-text("Submit Reply")')


def _seed_replies(page, post_id, count, body_prefix="seed"):
    """Bulk-create replies through the reply API.

    Pagination needs 31 replies to show a second page; driving the textarea 31
    times would add ~30 page reloads to the run for no extra coverage. The UI
    being tested here is the pager, not the compose box.
    """
    return page.evaluate(
        """
        async ({postId, count, bodyPrefix}) => {
            const c = document.cookie.split('; ').find(r => r.startsWith('csrf_token='));
            const csrf = c ? c.split('=')[1] : '';
            let created = 0;
            for (let i = 0; i < count; i++) {
                const res = await fetch('/embed/message-board/api/reply', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json', 'X-CSRF-Token': csrf},
                    body: JSON.stringify({post_id: postId, body: bodyPrefix + ' ' + i}),
                    credentials: 'same-origin'
                });
                const data = await res.json();
                if (data && data.success) created++;
            }
            return created;
        }
        """,
        {"postId": post_id, "count": count, "bodyPrefix": body_prefix},
    )


def _reply_card_count(page):
    return page.locator('[id^="replyView"]').count()


def _first_reply_id(page):
    """Id of the first reply card, parsed from its element id."""
    el = page.locator('[id^="replyView"]').first
    return int(re.sub(r"\D", "", el.get_attribute("id")))


def _subject_text(page):
    return page.locator("#postView h1").inner_text().strip()


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def board_page(browser_instance, base_url, test_email, test_password):
    """Logged-in page for the whole module, then delete every post it made."""
    ctx = browser_instance.new_context(
        viewport={"width": 1280, "height": 800},
        ignore_https_errors=True,
    )
    page = ctx.new_page()

    page.goto(f"{base_url}/auth/login")
    page.fill('input[name="email"]', test_email)
    page.fill('input[name="password"]', test_password)
    page.click('button[type="submit"]')
    page.wait_for_url("**/dashboard**", timeout=10000)

    yield page

    # Teardown: sweep the board for anything this run created.
    try:
        page.goto(f"{base_url}{BOARD}")
        page.wait_for_load_state("networkidle")
        links = page.locator(f'a[href*="/post/"]:has-text("{PREFIX}")')
        ids = []
        for i in range(links.count()):
            href = links.nth(i).get_attribute("href") or ""
            if "/post/" in href:
                ids.append(int(href.split("/post/")[1].split("?")[0].split("#")[0]))
        for pid in set(ids):
            _delete_post(page, base_url, pid)
    finally:
        page.close()
        ctx.close()


@pytest.fixture(scope="module")
def empty_body_post(board_page, base_url):
    """A post with a subject and NO body -- the shape that used to be
    permanently uneditable."""
    return _create_post(board_page, base_url, f"{PREFIX} empty body")


# ---------------------------------------------------------------------------
# Create
# ---------------------------------------------------------------------------

def test_create_post_with_body(board_page, base_url):
    subject = f"{PREFIX} with body"
    pid = _create_post(board_page, base_url, subject, body="Details for the post.")
    assert _subject_text(board_page) == subject
    assert "Details for the post." in board_page.locator("#postView").inner_text()
    assert pid > 0


def test_create_post_without_body(board_page, base_url):
    """A body is optional -- this is how the stuck post got created."""
    subject = f"{PREFIX} no body"
    _create_post(board_page, base_url, subject)
    assert _subject_text(board_page) == subject


def test_create_post_requires_subject_inline_error(board_page, base_url):
    """Empty subject must surface INLINE, not in an off-screen toast."""
    board_page.goto(f"{base_url}{BOARD}")
    board_page.wait_for_load_state("networkidle")
    board_page.click(".new-post-btn")
    board_page.fill("#postSubject", "")
    board_page.click('#newPostForm button:has-text("Submit")')

    err = board_page.locator("#newPostError")
    err.wait_for(state="visible", timeout=5000)
    assert "subject" in err.inner_text().strip().lower()
    # Still on the board -- nothing was created.
    assert "/post/" not in board_page.url


# ---------------------------------------------------------------------------
# Edit -- the regression this module exists for
# ---------------------------------------------------------------------------

def test_edit_subject_on_empty_body_post(board_page, base_url, empty_body_post):
    """The actual bug: subject edits on a body-less post used to no-op."""
    new_subject = f"{PREFIX} empty body EDITED"
    board_page.goto(f"{base_url}{BOARD}/post/{empty_body_post}")
    board_page.wait_for_load_state("networkidle")

    _open_post_edit(board_page)
    board_page.fill("#editPostSubject", new_subject)
    _save_post_edit(board_page)
    board_page.wait_for_load_state("networkidle")

    assert _subject_text(board_page) == new_subject

    # And it survives a fresh load, i.e. it really persisted.
    board_page.goto(f"{base_url}{BOARD}/post/{empty_body_post}")
    board_page.wait_for_load_state("networkidle")
    assert _subject_text(board_page) == new_subject


def test_edit_post_body(board_page, base_url):
    pid = _create_post(board_page, base_url, f"{PREFIX} body edit", body="original body")
    _open_post_edit(board_page)
    board_page.fill("#editPostBody", "rewritten body")
    _save_post_edit(board_page)
    board_page.wait_for_load_state("networkidle")

    board_page.goto(f"{base_url}{BOARD}/post/{pid}")
    board_page.wait_for_load_state("networkidle")
    text = board_page.locator("#postView").inner_text()
    assert "rewritten body" in text
    assert "original body" not in text


def test_edit_requires_subject_inline_error(board_page, base_url, empty_body_post):
    """Clearing the subject must report inline rather than silently doing nothing."""
    board_page.goto(f"{base_url}{BOARD}/post/{empty_body_post}")
    board_page.wait_for_load_state("networkidle")
    _open_post_edit(board_page)
    board_page.fill("#editPostSubject", "")
    _save_post_edit(board_page, expect_reload=False)

    err = board_page.locator("#editPostError")
    err.wait_for(state="visible", timeout=5000)
    assert "subject" in err.inner_text().strip().lower()


def test_long_subject_wraps_instead_of_clipping(board_page, base_url, empty_body_post):
    """On a phone the subject field must grow, not scroll the text out of reach."""
    long_subject = (
        f"{PREFIX} a deliberately long subject line that will not fit on one "
        "row of a phone screen at all"
    )[:200]

    board_page.goto(f"{base_url}{BOARD}/post/{empty_body_post}")
    board_page.wait_for_load_state("networkidle")
    _open_post_edit(board_page)
    board_page.fill("#editPostSubject", long_subject)

    board_page.set_viewport_size({"width": 390, "height": 844})
    metrics = board_page.evaluate(
        """() => {
            const el = document.getElementById('editPostSubject');
            el.style.height = 'auto';
            el.style.height = el.scrollHeight + 'px';
            return {
                tag: el.tagName,
                offset: el.offsetHeight,
                scroll: el.scrollHeight,
                fontSize: parseFloat(getComputedStyle(el).fontSize),
            };
        }"""
    )
    board_page.set_viewport_size({"width": 1280, "height": 800})

    assert metrics["tag"] == "TEXTAREA", "subject must wrap, not be a one-line input"
    # Nothing hidden above/below the visible box.
    assert metrics["scroll"] <= metrics["offset"] + 1, (
        f"subject clipped at phone width: scrollHeight={metrics['scroll']} "
        f"offsetHeight={metrics['offset']}"
    )
    # <16px makes iOS zoom the whole page on focus.
    assert metrics["fontSize"] >= 16


def test_subject_stays_single_line(board_page, base_url):
    """Newlines pasted into the wrapping field collapse to spaces on save."""
    pid = _create_post(board_page, base_url, f"{PREFIX} oneline", body="x")
    _open_post_edit(board_page)
    board_page.locator("#editPostSubject").fill(f"{PREFIX}  oneline\nsecond part")
    _save_post_edit(board_page)
    board_page.wait_for_load_state("networkidle")

    board_page.goto(f"{base_url}{BOARD}/post/{pid}")
    board_page.wait_for_load_state("networkidle")
    assert _subject_text(board_page) == f"{PREFIX} oneline second part"


# ---------------------------------------------------------------------------
# Replies
# ---------------------------------------------------------------------------

def test_create_and_edit_reply(board_page, base_url):
    pid = _create_post(board_page, base_url, f"{PREFIX} replies", body="post body")

    _submit_reply(board_page, "first reply text")
    assert "first reply text" in board_page.locator("#repliesList").inner_text()

    rid = _first_reply_id(board_page)
    board_page.locator(f"#replyView{rid} .edit-btn").click()
    board_page.wait_for_selector(f"#replyEdit{rid}", state="visible")
    board_page.fill(f"#replyEditBody{rid}", "edited reply text")
    with board_page.expect_navigation(wait_until="load", timeout=10000):
        board_page.click(f'#replyEdit{rid} button:has-text("Save")')

    board_page.goto(f"{base_url}{BOARD}/post/{pid}")
    board_page.wait_for_load_state("networkidle")
    replies = board_page.locator("#repliesList").inner_text()
    assert "edited reply text" in replies
    assert "first reply text" not in replies


# ---------------------------------------------------------------------------
# Admin controls
# ---------------------------------------------------------------------------

def test_pin_and_unpin(board_page, base_url, empty_body_post):
    board_page.goto(f"{base_url}{BOARD}/post/{empty_body_post}")
    board_page.wait_for_load_state("networkidle")

    _click_admin(board_page, "Pin")
    assert "Pinned" in board_page.locator("#postView").inner_text()
    assert board_page.locator('.admin-btn:text-is("Unpin")').count() == 1

    _click_admin(board_page, "Unpin")
    assert "Pinned" not in board_page.locator("#postView").inner_text()


def test_mark_and_remove_faq(board_page, base_url, empty_body_post):
    board_page.goto(f"{base_url}{BOARD}/post/{empty_body_post}")
    board_page.wait_for_load_state("networkidle")

    _click_admin(board_page, "Mark as FAQ")
    assert "FAQ" in board_page.locator("#postView").inner_text()

    _click_admin(board_page, "Remove FAQ")
    assert board_page.locator('.admin-btn:text-is("Mark as FAQ")').count() == 1


def test_delete_post_removes_it_and_its_replies(board_page, base_url):
    pid = _create_post(board_page, base_url, f"{PREFIX} to delete", body="doomed")
    _submit_reply(board_page, "doomed reply")

    assert _delete_post(board_page, base_url, pid), "Delete control not available"

    board_page.goto(f"{base_url}{BOARD}")
    board_page.wait_for_load_state("networkidle")
    assert f"{PREFIX} to delete" not in board_page.locator("body").inner_text()

    # The post itself is gone, so its replies went with it (ON DELETE CASCADE).
    board_page.goto(f"{base_url}{BOARD}/post/{pid}")
    board_page.wait_for_load_state("networkidle")
    assert "doomed reply" not in board_page.locator("body").inner_text()


# ---------------------------------------------------------------------------
# Likes
# ---------------------------------------------------------------------------

def test_like_and_unlike_post(board_page, base_url):
    """Likes update in place -- no reload -- so assert with retrying matchers."""
    _create_post(board_page, base_url, f"{PREFIX} post likes", body="like me")

    btn = board_page.locator("#postView .like-btn")
    expect(btn.locator(".like-count")).to_have_text("0")

    btn.click()
    expect(btn.locator(".like-count")).to_have_text("1")
    expect(btn).to_have_class(re.compile(r"\bliked\b"))

    btn.click()
    expect(btn.locator(".like-count")).to_have_text("0")
    expect(btn).not_to_have_class(re.compile(r"\bliked\b"))


def test_like_persists_across_reload(board_page, base_url):
    pid = _create_post(board_page, base_url, f"{PREFIX} like persist", body="like me")

    btn = board_page.locator("#postView .like-btn")
    btn.click()
    expect(btn.locator(".like-count")).to_have_text("1")

    board_page.goto(f"{base_url}{BOARD}/post/{pid}")
    board_page.wait_for_load_state("networkidle")
    reloaded = board_page.locator("#postView .like-btn")
    expect(reloaded.locator(".like-count")).to_have_text("1")
    # Still shown as liked *by me*, not just counted.
    expect(reloaded).to_have_class(re.compile(r"\bliked\b"))


def test_like_reply(board_page, base_url):
    _create_post(board_page, base_url, f"{PREFIX} reply likes", body="post body")
    _submit_reply(board_page, "likeable reply")

    rid = _first_reply_id(board_page)
    btn = board_page.locator(f"#replyView{rid} .like-btn")
    expect(btn.locator(".like-count")).to_have_text("0")

    btn.click()
    expect(btn.locator(".like-count")).to_have_text("1")
    expect(btn).to_have_class(re.compile(r"\bliked\b"))


# ---------------------------------------------------------------------------
# Pagination
# ---------------------------------------------------------------------------

def test_no_pager_when_replies_fit_one_page(board_page, base_url):
    _create_post(board_page, base_url, f"{PREFIX} short thread", body="body")
    _submit_reply(board_page, "only reply")
    assert board_page.locator(".page-btn").count() == 0


def test_reply_pagination(board_page, base_url):
    """31 replies -> 30 on page 1, 1 on page 2, with correct pager states."""
    pid = _create_post(board_page, base_url, f"{PREFIX} long thread", body="body")

    created = _seed_replies(board_page, pid, 31)
    assert created == 31, f"seeding failed, only {created} replies created"

    # Page 1
    board_page.goto(f"{base_url}{BOARD}/post/{pid}")
    board_page.wait_for_load_state("networkidle")
    assert _reply_card_count(board_page) == 30
    assert "Page 1 of 2" in board_page.locator("body").inner_text()
    # Previous is inert on the first page; Next is a real link.
    assert board_page.locator('span.page-btn.disabled:has-text("Previous")').count() == 1
    assert board_page.locator('a.page-btn:has-text("Next")').count() == 1

    # Page 2
    board_page.locator('a.page-btn:has-text("Next")').first.click()
    board_page.wait_for_load_state("networkidle")
    assert _reply_card_count(board_page) == 1
    assert "Page 2 of 2" in board_page.locator("body").inner_text()
    assert board_page.locator('a.page-btn:has-text("Previous")').count() == 1
    assert board_page.locator('span.page-btn.disabled:has-text("Next")').count() == 1

    # And back again.
    board_page.locator('a.page-btn:has-text("Previous")').first.click()
    board_page.wait_for_load_state("networkidle")
    assert _reply_card_count(board_page) == 30


# ---------------------------------------------------------------------------
# Logged-out visitors
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def public_post(board_page, base_url):
    """A post that anonymous tests can look at."""
    pid = _create_post(board_page, base_url, f"{PREFIX} public view", body="public body")
    _submit_reply(board_page, "public reply")
    return pid


def test_logged_out_can_read_board(page, base_url, public_post):
    page.goto(f"{base_url}{BOARD}/post/{public_post}")
    page.wait_for_load_state("networkidle")
    body = page.locator("body").inner_text()
    assert f"{PREFIX} public view" in body
    assert "public body" in body
    assert "public reply" in body


def test_logged_out_is_prompted_to_sign_in_to_reply(page, base_url, public_post):
    page.goto(f"{base_url}{BOARD}/post/{public_post}")
    page.wait_for_load_state("networkidle")

    assert page.locator("#replyBody").count() == 0, "compose box shown to anonymous user"
    link = page.locator('a:has-text("Sign in to reply")')
    assert link.count() == 1
    # Sends them back to this post after login.
    assert f"next={BOARD}/post/{public_post}" in (link.get_attribute("href") or "")


def test_logged_out_has_no_edit_or_admin_controls(page, base_url, public_post):
    page.goto(f"{base_url}{BOARD}/post/{public_post}")
    page.wait_for_load_state("networkidle")
    assert page.locator(".edit-btn").count() == 0
    assert page.locator(".admin-btn").count() == 0


def test_logged_out_sees_sign_in_instead_of_new_post(page, base_url):
    page.goto(f"{base_url}{BOARD}")
    page.wait_for_load_state("networkidle")
    assert page.locator("button.new-post-btn").count() == 0
    assert page.locator("#newPostForm").count() == 0
    assert page.locator('a:has-text("Sign in to post")').count() == 1


def _csrf_token(page, base_url):
    """Anonymous visitors still get a csrf_token cookie; return it."""
    page.goto(f"{base_url}{BOARD}")
    page.wait_for_load_state("networkidle")
    for c in page.context.cookies(base_url):
        if c["name"] == "csrf_token":
            return c["value"]
    raise AssertionError("no csrf_token cookie issued")


def test_state_changing_post_without_csrf_is_blocked(page, base_url, public_post):
    """First line of defence: the global before_request guard (403)."""
    resp = page.request.post(
        f"{base_url}{BOARD}/api/like",
        data={"post_id": public_post},
    )
    assert resp.status == 403


def test_logged_out_cannot_like(page, base_url, public_post):
    """Second line: with CSRF satisfied, auth must still refuse (401)."""
    token = _csrf_token(page, base_url)
    resp = page.request.post(
        f"{base_url}{BOARD}/api/like",
        data={"post_id": public_post},
        headers={"X-CSRF-Token": token},
    )
    assert resp.status == 401


def test_logged_out_cannot_edit(page, base_url, public_post):
    token = _csrf_token(page, base_url)
    resp = page.request.post(
        f"{base_url}{BOARD}/api/edit",
        data={"post_id": public_post, "subject": "hijacked", "body": "hijacked"},
        headers={"X-CSRF-Token": token},
    )
    assert resp.status == 401

    # And the post really is untouched, not just reported as refused.
    page.goto(f"{base_url}{BOARD}/post/{public_post}")
    page.wait_for_load_state("networkidle")
    body = page.locator("body").inner_text()
    assert f"{PREFIX} public view" in body
    assert "hijacked" not in body
