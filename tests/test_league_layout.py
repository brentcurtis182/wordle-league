"""
Layout regression tests for the public league page.

These exist because a 25-character player name pushed the emoji grid off the
side of the screen on mobile, and nothing in the suite noticed. The bug had an
exact, stable signature — the page scrolled sideways — which is worth asserting
directly.

Deliberately NOT screenshot comparison. Scores change every day, so pixel
diffing would fail constantly for reasons that have nothing to do with layout.
Geometry assertions survive changing content and still catch "it runs off the
page".

Needs a league with real scores AND awkwardly long names; seed one with
seed_layout_fixture.py. Every test skips rather than fails when the fixture is
missing, so a fresh staging database does not turn the suite red.
"""
import pytest

TABS = [
    ("latest", "Latest Scores"),
    ("weekly", "Weekly Totals"),
    ("stats", "Season"),
    ("rules", "Rules"),
]

VIEWPORTS = [
    pytest.param({"width": 1280, "height": 800}, id="desktop"),
    pytest.param({"width": 390, "height": 844}, id="phone"),
]

# The name length that caused the original bug. A fixture with nothing longer
# than this is not exercising the thing these tests are for.
INTERESTING_NAME_LENGTH = 18


def _layout_slug(request):
    return request.config.getoption("--layout-slug", default=None) or "super-test"


def _open(page, base_url, slug, viewport):
    page.set_viewport_size(viewport)
    response = page.goto(f"{base_url}/leagues/{slug}")
    if response is None or response.status != 200:
        pytest.skip(f"league page /leagues/{slug} not available (status "
                    f"{response.status if response else 'none'})")
    page.wait_for_load_state("networkidle")


def _has_scores(page):
    return page.locator(".score-card").count() > 0


def _show_tab(page, tab_id):
    button = page.locator(f'button.tab-button[data-tab="{tab_id}"]')
    if button.count() == 0:
        pytest.skip(f"tab {tab_id} not present on this page")
    button.first.click()
    page.wait_for_timeout(150)


def _horizontal_overflow(page):
    """Pixels by which the document is wider than the window. 0 means fine."""
    return page.evaluate(
        "() => Math.max(0, document.documentElement.scrollWidth - window.innerWidth)"
    )


class TestLeaguePageLayout:
    """The page must never scroll sideways, on any tab, at any width."""

    @pytest.mark.parametrize("viewport", VIEWPORTS)
    @pytest.mark.parametrize("tab_id,tab_label", TABS)
    def test_no_horizontal_overflow(self, page, base_url, request, viewport, tab_id, tab_label):
        slug = _layout_slug(request)
        _open(page, base_url, slug, viewport)
        if not _has_scores(page):
            pytest.skip(f"{slug} has no scores — run seed_layout_fixture.py")

        _show_tab(page, tab_id)
        overflow = _horizontal_overflow(page)
        assert overflow == 0, (
            f"{tab_label} overflows horizontally by {overflow}px at "
            f"{viewport['width']}px wide. Something inside is refusing to shrink — "
            f"a long player name is the usual cause."
        )

    @pytest.mark.parametrize("viewport", VIEWPORTS)
    def test_latest_card_contents_stay_inside_the_card(self, page, base_url, request, viewport):
        """The name must not push the emoji grid past the card's edge."""
        slug = _layout_slug(request)
        _open(page, base_url, slug, viewport)
        if not _has_scores(page):
            pytest.skip(f"{slug} has no scores — run seed_layout_fixture.py")

        _show_tab(page, "latest")
        offenders = page.evaluate("""
            () => {
              const bad = [];
              document.querySelectorAll('.score-card').forEach(card => {
                const c = card.getBoundingClientRect();
                card.querySelectorAll('.player-name, .emoji-pattern, .player-score').forEach(el => {
                  const r = el.getBoundingClientRect();
                  // 1px of tolerance for sub-pixel rounding.
                  if (r.right > c.right + 1) {
                    bad.push({
                      cls: el.className,
                      text: (el.textContent || '').trim().slice(0, 30),
                      overhang: Math.round(r.right - c.right)
                    });
                  }
                });
              });
              return bad;
            }
        """)
        assert offenders == [], (
            f"content escapes its card at {viewport['width']}px wide: {offenders}"
        )

    @pytest.mark.parametrize("viewport", VIEWPORTS)
    def test_long_names_are_truncated_not_expanded(self, page, base_url, request, viewport):
        """
        A name too long for its slot should be clipped with an ellipsis, which
        shows up as the element's scrollWidth exceeding its clientWidth while the
        element itself stays within its declared width.
        """
        slug = _layout_slug(request)
        _open(page, base_url, slug, viewport)
        if not _has_scores(page):
            pytest.skip(f"{slug} has no scores — run seed_layout_fixture.py")

        longest = page.evaluate("""
            () => {
              let n = 0;
              document.querySelectorAll('.player-name, .name-cell, .sticky-column')
                .forEach(el => { n = Math.max(n, (el.textContent || '').trim().length); });
              return n;
            }
        """)
        if longest < INTERESTING_NAME_LENGTH:
            pytest.skip(
                f"longest name on {slug} is {longest} chars — too short to test "
                f"truncation; run seed_layout_fixture.py"
            )

        clipped_properly = page.evaluate("""
            () => {
              const out = [];
              document.querySelectorAll('.player-name, .name-cell, .sticky-column').forEach(el => {
                const s = getComputedStyle(el);
                out.push({
                  overflow: s.overflow,
                  ellipsis: s.textOverflow,
                  nowrap: s.whiteSpace,
                  text: (el.textContent || '').trim().slice(0, 30)
                });
              });
              return out;
            }
        """)
        wrong = [c for c in clipped_properly
                 if c["overflow"] != "hidden" or c["ellipsis"] != "ellipsis" or c["nowrap"] != "nowrap"]
        assert wrong == [], (
            f"name elements missing clipping rules, so long names will expand "
            f"their container instead of truncating: {wrong[:3]}"
        )
