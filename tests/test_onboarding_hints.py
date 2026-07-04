"""
Onboarding help-tooltip ("?") chip tests.

A brand-new league surfaces orange state indicators (Inactive / Unlinked /
Waiting OPT-IN) before setup is complete. Each unfinished-state indicator has
a tappable "?" / ⓘ chip that opens one shared info modal (#infoModal)
explaining what's needed. These tests cover:
  - the Inactive chip is present on a fresh SMS league and opens/closes the modal
  - the Waiting OPT-IN chip lists the specific player(s) still needing to opt in

The Unlinked chip only renders when payment_required is enabled (off on
staging), so it is intentionally not covered here.
"""

import pytest
import time


# Unique suffix to avoid collisions with other test runs
_TS = str(int(time.time()))[-6:]
HINTS_SMS_LEAGUE_NAME = f"Hints SMS {_TS}"
HINTS_SMS_LEAGUE_SLUG = f"hints-sms-{_TS}"


@pytest.fixture(scope="module")
def hints_sms_context(browser_instance, base_url, test_email, test_password):
    """Create a fresh (unactivated) SMS league, yield its ID, then delete it."""
    ctx = browser_instance.new_context(
        viewport={"width": 1280, "height": 800},
        ignore_https_errors=True,
    )
    page = ctx.new_page()

    # Login
    page.goto(f"{base_url}/auth/login")
    page.fill('input[name="email"]', test_email)
    page.fill('input[name="password"]', test_password)
    page.click('button[type="submit"]')
    page.wait_for_url("**/dashboard**", timeout=10000)

    # Create SMS league
    page.goto(f"{base_url}/dashboard/create-league")
    page.wait_for_load_state("networkidle")
    page.fill('input[name="league_name"]', HINTS_SMS_LEAGUE_NAME)
    page.fill('input[name="slug"]', HINTS_SMS_LEAGUE_SLUG)
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
        link = page.locator(f'a[href*="/dashboard/league/"]:has-text("{HINTS_SMS_LEAGUE_NAME}")')
        if link.count() > 0:
            href = link.first.get_attribute("href")
            league_id = int(href.split("/dashboard/league/")[1].split("?")[0].split("/")[0])

    yield {"page": page, "league_id": league_id, "base_url": base_url}

    # Cleanup: delete the test league
    if league_id:
        page.goto(f"{base_url}/dashboard/league/{league_id}")
        page.wait_for_load_state("networkidle")
        delete_btn = page.locator('button:has-text("Delete League")')
        if delete_btn.count() > 0:
            delete_btn.click()
            confirm_input = page.locator('#deleteLeagueConfirmName')
            if confirm_input.count() > 0:
                confirm_input.fill(HINTS_SMS_LEAGUE_NAME)
                page.wait_for_timeout(300)
            confirm_btn = page.locator('#confirmDeleteBtn')
            if confirm_btn.count() > 0:
                confirm_btn.click()
                page.wait_for_load_state("networkidle")

    page.close()
    ctx.close()


class TestInactiveChip:
    """The Inactive-state '?' help chip on a fresh SMS league."""

    def test_inactive_chip_present(self, hints_sms_context):
        """A fresh (unactivated) SMS league shows the Inactive '?' help chip."""
        page = hints_sms_context["page"]
        base_url = hints_sms_context["base_url"]
        league_id = hints_sms_context["league_id"]
        assert league_id, "League was not created successfully"

        page.goto(f"{base_url}/dashboard/league/{league_id}")
        page.wait_for_load_state("networkidle")

        chip = page.locator("[onclick*=\"showInfoModal('inactive')\"]")
        assert chip.count() > 0, "Inactive '?' help chip should be present on a fresh SMS league"

    def test_inactive_chip_opens_and_closes_modal(self, hints_sms_context):
        """Clicking the Inactive chip opens the info modal with activation copy, and 'Got it' closes it."""
        page = hints_sms_context["page"]
        base_url = hints_sms_context["base_url"]
        league_id = hints_sms_context["league_id"]
        assert league_id

        page.goto(f"{base_url}/dashboard/league/{league_id}")
        page.wait_for_load_state("networkidle")

        page.locator("[onclick*=\"showInfoModal('inactive')\"]").first.click()
        page.wait_for_selector("#infoModal.active", timeout=3000)

        body = (page.locator("#infoModalBody").text_content() or "").lower()
        assert ("activate" in body or "passphrase" in body), \
            f"Inactive modal should explain activation, got: {body!r}"

        # Close it via "Got it" — a closed modal-overlay is display:none (hidden)
        page.locator("#infoModal button:has-text('Got it')").click()
        page.wait_for_selector("#infoModal", state="hidden", timeout=3000)


class TestOptInChip:
    """The Waiting OPT-IN chip lists the specific players still needing to opt in."""

    def test_optin_chip_lists_waiting_player(self, hints_sms_context):
        """After adding a player (defaults to WAITING), the OPT-IN chip opens a modal naming them."""
        page = hints_sms_context["page"]
        base_url = hints_sms_context["base_url"]
        league_id = hints_sms_context["league_id"]
        assert league_id

        page.goto(f"{base_url}/dashboard/league/{league_id}")
        page.wait_for_load_state("networkidle")

        # New SMS players default to sms_opt_in_status = 'WAITING'
        player_name = "OptInTester"
        page.fill('#addPlayerForm input[name="name"]', player_name)
        phone_input = page.locator('#phoneInput, #addPlayerForm input[name="identifier"]')
        phone_input.first.fill("(555) 222-3344")
        page.click('#addPlayerForm button[type="submit"]')
        # add-player redirects back to the league dashboard (running a slow HTML
        # publish first). Wait for the OPT-IN chip itself to appear on the final
        # page — locator.wait_for auto-retries through the redirect navigation,
        # and its presence is exactly what we're asserting.
        optin_chip = page.locator("[onclick*=\"showInfoModal('optin')\"]").first
        optin_chip.wait_for(state="visible", timeout=20000)

        optin_chip.click()
        page.wait_for_selector("#infoModal.active", timeout=3000)

        body = page.locator("#infoModalBody").text_content() or ""
        assert player_name in body, \
            f"OPT-IN modal should list the waiting player '{player_name}', got: {body!r}"
        assert "opt in" in body.lower(), f"OPT-IN modal should mention opting in, got: {body!r}"
