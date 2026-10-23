"""Signup source labelling (signup_attribution.describe_request). DB-free.

Pins the precedence the Monday growth report relies on, especially for ad
spend: explicit utm tags win, then ad click ids (gclid / msclkid / fbclid),
then the referring site, then the Slack app directory, then direct.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from signup_attribution import describe_request  # noqa: E402


class FakeRequest:
    def __init__(self, args=None, referrer=None):
        self.args = args or {}
        self.referrer = referrer


def src(args=None, referrer=None):
    return describe_request(FakeRequest(args, referrer))['source']


def test_utm_source_wins_over_everything():
    assert src({'utm_source': 'Reddit', 'gclid': 'x', 'wpl_ref': 'google.com'}) == 'reddit'


def test_ad_click_ids_label_untagged_ads():
    assert src({'gclid': 'abc'}) == 'google-ads'
    assert src({'wbraid': 'abc'}) == 'google-ads'
    assert src({'msclkid': 'abc'}) == 'bing-ads'
    assert src({'fbclid': 'abc'}) == 'facebook'


def test_click_id_sets_medium_too():
    d = describe_request(FakeRequest({'gclid': 'abc'}))
    assert d['utm_medium'] == 'cpc'


def test_marketing_site_referrer_then_browser_referrer():
    assert src({'wpl_ref': 'news.ycombinator.com'}) == 'news.ycombinator.com'
    assert src({}, referrer='https://www.reddit.com/r/wordle/') == 'reddit.com'


def test_own_hosts_are_not_a_source():
    assert src({}, referrer='https://wordplayleague.com/pricing') == 'direct'
    assert src({}, referrer='https://app.wordplayleague.com/dashboard') == 'direct'


def test_slack_directory_and_direct():
    assert src({'slack_installed': '1'}) == 'slack_app_directory'
    assert src({'wpl_ref': 'direct'}) == 'direct'
    assert src({}) == 'direct'


def test_button_and_landing_are_kept():
    d = describe_request(FakeRequest({'wpl_ref': 'google.com', 'wpl_cta': '/#hero', 'wpl_land': '/wordle-stats'}))
    assert (d['cta'], d['landing']) == ('/#hero', '/wordle-stats')
