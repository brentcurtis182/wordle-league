"""Unit tests for inbound SMS consent keyword classification.

Pure tests — no clock, DB, Twilio, or Flask request context.

Regression origin (Alchemer / league 45, 2026-10-09): the manager texted STOP
into his own league's group thread while exploring the keywords in our
disclaimer. Twilio intercepted it at the Messaging Service layer, auto-replied
with an unsubscribe confirmation, and added his number to its opt-out list —
after which every send to him would be rejected with error 21610.

Our app only recognised the literal strings "OPT IN" and "OPT OUT", so it saw
STOP as ordinary chatter and left him `sms_opt_in_status = 'IN'`. He was an
apparently-active league member who could no longer receive anything, and
nothing anywhere flagged it.

The message does reach /webhook (it lands in the conversation, so onMessageAdded
fires), which is why this is fixable at all.
"""
from twilio_webhook_app import (classify_opt_keyword,
                                CARRIER_OPT_IN_KEYWORDS,
                                CARRIER_OPT_OUT_KEYWORDS)


# --- our own explicit keywords still behave as before ---

def test_opt_in_is_recognised():
    assert classify_opt_keyword('OPT IN') == ('OPT IN', False)


def test_opt_out_is_recognised():
    assert classify_opt_keyword('OPT OUT') == ('OPT OUT', False)


def test_case_hyphen_and_whitespace_variants_all_work():
    for variant in ('opt in', 'Opt In', 'Opt-in', 'OPT-IN', 'opt  in', '  Opt in  '):
        assert classify_opt_keyword(variant) == ('OPT IN', False), variant


def test_our_keywords_are_not_flagged_as_carrier():
    """We must still send our own confirmation for these."""
    for kw in ('OPT IN', 'OPT OUT'):
        _, is_carrier = classify_opt_keyword(kw)
        assert is_carrier is False


# --- the bug: carrier keywords ---

def test_stop_is_an_opt_out():
    assert classify_opt_keyword('STOP') == ('OPT OUT', True)


def test_stop_is_case_insensitive():
    for variant in ('stop', 'Stop', 'StOp', ' STOP '):
        assert classify_opt_keyword(variant) == ('OPT OUT', True), variant


def test_every_carrier_opt_out_keyword_maps_to_opt_out():
    for kw in CARRIER_OPT_OUT_KEYWORDS:
        assert classify_opt_keyword(kw) == ('OPT OUT', True), kw


def test_every_carrier_opt_in_keyword_maps_to_opt_in():
    for kw in CARRIER_OPT_IN_KEYWORDS:
        assert classify_opt_keyword(kw) == ('OPT IN', True), kw


def test_carrier_keywords_are_flagged_so_we_stay_quiet():
    """Twilio already replied; a second message from us is noise, and on an
    opt-out it would be rejected with 21610."""
    for kw in ('STOP', 'START', 'UNSUBSCRIBE', 'UNSTOP'):
        _, is_carrier = classify_opt_keyword(kw)
        assert is_carrier is True, kw


# --- consent safety ---

def test_yes_is_not_a_consent_keyword():
    """Twilio treats YES as a resubscribe, but in a group thread "yes" is
    ordinary conversation. Honouring it could opt in someone who never agreed."""
    assert classify_opt_keyword('YES') == (None, False)
    assert 'YES' not in CARRIER_OPT_IN_KEYWORDS


# --- things that must NOT be mistaken for consent ---

def test_ordinary_chatter_is_ignored():
    for msg in ('Nice work Barry!', 'I mean, five is a shitty score. But.....',
                'What did you do chantal?', 'stop it you two', 'can you stop',
                'I opt in', 'Opting in', 'optin', ''):
        intent, is_carrier = classify_opt_keyword(msg)
        assert intent is None, f"{msg!r} was read as {intent}"
        assert is_carrier is False


def test_a_wordle_score_is_never_consent():
    assert classify_opt_keyword('Wordle 1,938 4/6\n\nXXXXX') == (None, False)


def test_none_body_is_safe():
    """Twilio can deliver an empty body (e.g. a media-only MMS)."""
    assert classify_opt_keyword(None) == (None, False)


def test_passphrase_cannot_collide_with_a_keyword():
    """Activation passphrases are two lowercase words; no keyword is two words,
    so the two features cannot shadow each other."""
    assert classify_opt_keyword('gleaming thunderclap') == (None, False)
    for kw in CARRIER_OPT_OUT_KEYWORDS | CARRIER_OPT_IN_KEYWORDS:
        assert ' ' not in kw, kw
