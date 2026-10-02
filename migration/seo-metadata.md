# Titles & meta descriptions to port to Cloudflare

Captured 2026-09-26 from the live Wix site (Screaming Frog exports, plus two
pages fetched by hand that the crawl could not reach). These are good as
written — every title is 31-57 characters and every description 90-145, so
nothing truncates in results. **Port them verbatim; don't rewrite.**

The Wix dashboard is the only place these live, and they do not come with the
domain. This file is the backup.

---

## Pages that carry over

### `/`
- **Title:** Wordle League for Your Group Chat | WordPlayLeague
- **Description:** Your group already texts Wordle scores. WordPlayLeague reads them automatically — weekly winners, season standings, and a real title race.

### `/rules`
- **Title:** How Wordle League Scoring Works | WordPlayLeague
- **Description:** How scoring works in a WordPlayLeague group: daily results, weekly winners, season length, promotion and relegation, and how ties are broken.

### `/leagues`
- **Title:** Live Wordle Leaderboards & Standings | WordPlayLeague
- **Description:** Browse active WordPlayLeague groups — weekly winners, season standings, best averages and most perfect games, updated as scores land.

### `/slack-app`
- **Title:** Wordle League for Slack — Track Scores in Your Channel
- **Description:** Run a daily Wordle league inside Slack. Players post results in your channel and WordPlayLeague scores them automatically. Full setup guide.
- Landing page URL on the live Slack Marketplace submission. Must not break.

### `/message-board`
- **Title:** Community Board — Questions & Updates | WordPlayLeague
- **Description:** Ask questions, share feedback, and read product updates from the WordPlayLeague community.

### `/privacy-policy`
- **Title:** Privacy Policy | WordPlayLeague
- **Description:** How WordPlayLeague collects, uses, and protects your data, including puzzle scores, phone numbers, and connected chat accounts.
- Cited by both A2P campaigns, by live SMS, and by the Slack submission.

### `/terms-of-service`
- **Title:** Terms of Service | WordPlayLeague
- **Description:** The terms governing use of WordPlayLeague, including accounts, subscriptions, acceptable use, and limitations of liability.

### `/sms-terms`
- **Title:** SMS Terms & Messaging Policy | WordPlayLeague
- **Description:** Message frequency, rates, opt-in and opt-out instructions for WordPlayLeague SMS leagues. Reply STOP to unsubscribe at any time.
- Cited by both A2P campaigns, by live SMS, and by the Slack submission.
- **Orphaned today** — Screaming Frog never reached it because nothing on the
  site links to it. Its visitors arrive from SMS and the Slack listing. Put a
  footer link on the new site so it stops being invisible.

### `/register`
- **Title:** Start Your Own Wordle League — Free Setup | WordPlayLeague
- **Description:** Set up a Wordle league for your group chat, Slack workspace, or Discord server. Scores are read automatically — no app for players to install.
- **robots: noindex** — keep it that way.
- Named by the legacy A2P campaign as the declared web-form opt-in. Rebuild
  verbatim; do not redirect. See `_redirects` for the consent wording that has
  to survive word for word.

---

## Retired

`/blog` and its three posts are being 301'd, not rebuilt. Recorded only so the
redirect targets are a judgement call rather than a guess.

| URL | Title | Description |
|---|---|---|
| `/blog` | WordPlayLeague Blog — Product Updates & Feature News | New features and updates for WordPlayLeague: custom season lengths, minimum weekly scores, and more. |
| `/post/custom-season-wins` | Custom Season Wins | *(none)* |
| `/post/enhancing-user-engagement-with-a-minimum-weekly-score-feature` | 📊 New Minimum Weekly Score Feature!   { 3-7 } | *(none)* |
| `/post/exploring-the-new-rules-tab-and-its-impact-on-user-experience` | New Rules Tab, Exploring all the Available Features | *(none)* |

None of the three posts has a meta description, which is part of why retiring
them costs little.

---

## Not migrating

`/profile/mainuser/profile` and `/profile/wordplayleague45416/profile` are Wix
Members scaffolding — "Profile | Wordplayleague", no description, one of them
indexable. Left alone deliberately: the whole Wix site goes away at cutover, so
deleting them now buys nothing. The only piece of Members worth carrying over is
the nav's **Login/Register** link, which on the new site should point at
`app.wordplayleague.com/auth/login`.
