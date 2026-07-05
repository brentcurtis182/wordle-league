"""
Division Mode end-to-end test.

Would have caught the CSRF-on-dynamic-form bug (2026-07-05): "Confirm Division
Mode" submits via a form built with createElement, which the page-load CSRF
auto-injector never stamped — so the POST went out with no csrf_token and was
rejected (403 "CSRF validation failed"), blocking division setup entirely.

Flow: create an SMS league, add 6 players, enable Division Mode, then Confirm
it — asserting the confirm actually succeeds (no CSRF error, division becomes
confirmed).
"""

import pytest
import time


_TS = str(int(time.time()))[-6:]
DIV_LEAGUE_NAME = f"Div Mode {_TS}"
DIV_LEAGUE_SLUG = f"div-mode-{_TS}"


@pytest.fixture(scope="module")
def div_league_context(browser_instance, base_url, test_email, test_password):
    """Create an SMS league for the division-mode flow, then delete it."""
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

    page.goto(f"{base_url}/dashboard/create-league")
    page.wait_for_load_state("networkidle")
    page.fill('input[name="league_name"]', DIV_LEAGUE_NAME)
    page.fill('input[name="slug"]', DIV_LEAGUE_SLUG)
    sms_label = page.locator('label.platform-option:has(input[value="sms"])')
    if sms_label.count() > 0:
        sms_label.click()
    page.click('button[type="submit"]')
    page.wait_for_load_state("networkidle")

    url = page.url
    league_id = None
    if "/dashboard/league/" in url:
        league_id = int(url.split("/dashboard/league/")[1].split("?")[0].split("/")[0])
    else:
        page.goto(f"{base_url}/dashboard")
        page.wait_for_load_state("networkidle")
        link = page.locator(f'a[href*="/dashboard/league/"]:has-text("{DIV_LEAGUE_NAME}")')
        if link.count() > 0:
            href = link.first.get_attribute("href")
            league_id = int(href.split("/dashboard/league/")[1].split("?")[0].split("/")[0])

    yield {"page": page, "league_id": league_id, "base_url": base_url}

    if league_id:
        page.goto(f"{base_url}/dashboard/league/{league_id}")
        page.wait_for_load_state("networkidle")
        delete_btn = page.locator('button:has-text("Delete League")')
        if delete_btn.count() > 0:
            delete_btn.click()
            confirm_input = page.locator('#deleteLeagueConfirmName')
            if confirm_input.count() > 0:
                confirm_input.fill(DIV_LEAGUE_NAME)
                page.wait_for_timeout(300)
            cb = page.locator('#confirmDeleteBtn')
            if cb.count() > 0:
                cb.click()
                page.wait_for_load_state("networkidle")

    page.close()
    ctx.close()


class TestDivisionMode:
    """Enable + Confirm Division Mode end to end (CSRF dynamic-form regression)."""

    def test_add_players_enable_and_confirm_division(self, div_league_context):
        page = div_league_context["page"]
        base_url = div_league_context["base_url"]
        league_id = div_league_context["league_id"]
        assert league_id, "League was not created"

        page.goto(f"{base_url}/dashboard/league/{league_id}")
        page.wait_for_load_state("networkidle")

        # Add 6 players (two 3-player divisions). Each add redirects through a
        # slow publish, so wait for the player name to land before the next.
        for i in range(6):
            name = f"DivP{i+1}"
            page.fill('#addPlayerForm input[name="name"]', name)
            phone_input = page.locator('#phoneInput, #addPlayerForm input[name="identifier"]')
            phone_input.first.fill(f"(555) 20{i}-100{i}")
            page.click('#addPlayerForm button[type="submit"]')
            page.locator(f"text={name}").first.wait_for(state="visible", timeout=25000)

        # Fresh load so the Division Mode toggle reflects current state
        page.goto(f"{base_url}/dashboard/league/{league_id}")
        page.wait_for_load_state("networkidle")

        # --- Enable Division Mode (toggle -> Enable modal -> submit existing form) ---
        page.locator('.division-toggle').first.click()
        page.wait_for_selector("#resetModal.active", timeout=5000)
        with page.expect_navigation(timeout=30000):
            page.locator('#resetModalConfirmBtn').click()
        page.wait_for_load_state("networkidle")

        # Confirm Division Mode button should now be present (division unconfirmed)
        confirm_btn = page.locator("button:has-text('Confirm Division Mode')")
        confirm_btn.first.wait_for(state="visible", timeout=10000)

        # --- Confirm/Publish (this is the dynamic-form CSRF path that broke) ---
        confirm_btn.first.click()
        page.wait_for_selector("#resetModal.active", timeout=5000)
        with page.expect_navigation(timeout=30000):
            page.locator('#resetModalConfirmBtn').click()
        page.wait_for_load_state("networkidle")

        # Assertions: no CSRF failure, and division mode is now confirmed.
        body = page.content()
        assert "CSRF validation failed" not in body, \
            "Confirm Division Mode hit a CSRF failure (403) — dynamic form not stamped"
        assert page.locator("button:has-text('Confirm Division Mode')").count() == 0, \
            "Division Mode did not confirm (Confirm button still present)"
        assert page.locator("button:has-text('Reset Season')").count() > 0, \
            "Division Mode did not confirm (no Reset Season button — confirmed state missing)"
