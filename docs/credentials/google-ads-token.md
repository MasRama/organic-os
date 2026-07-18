# Google Ads developer token setup (verified 2026)

This is the credential that turns on `hoo-keyword-intel`'s planner tier:
`GenerateKeywordIdeas`, `GenerateKeywordHistoricalMetrics`, and forecast
metrics. Every step below has been walked through against the current
(2026) Google Ads UI and API. Follow them in order.

## 1. Create or reuse a Google Ads Manager account

The developer token lives on a Manager (MCC) account, not on an individual
ads account. If you already advertise, you likely have one; if not, create
one at ads.google.com/home/tools/manager-accounts/. This is free and does
not require you to run any ads - a Manager account with zero linked spend
accounts is a normal, supported setup for API-only use.

## 2. Request the token in API Center

In the Manager account, go to Admin -> API Center, accept the Google Ads
API Terms of Service, and the developer token is issued immediately. New
tokens start at **Test Account access**: Google may auto-upgrade some
tokens to **Explorer** based on account signals, but do not count on it.
Note the token string; you will put it in an env file, never in the repo.

## 3. Create a Google Cloud project and enable the API

Create a project in the Google Cloud Console (or reuse one), then enable
the "Google Ads API" under APIs & Services -> Library. This project is
where the OAuth client that authenticates your API calls will live.

## 4. Configure the OAuth consent screen

Under APIs & Services -> OAuth consent screen, choose **External** user
type, add yourself as a test user, and add the scope
`https://www.googleapis.com/auth/adwords`. Publish the app (move it out of
Testing status) once you are done configuring it - apps left in Testing
mode issue refresh tokens that expire after 7 days, which silently breaks
any scheduled routine a week after you set it up.

## 5. Create a Desktop app OAuth client

Under Credentials -> Create Credentials -> OAuth client ID, choose
**Desktop app**. This gives you a client ID and client secret that support
the loopback redirect flow. Google retired the out-of-band (OOB, `urn:...`)
copy-paste flow in 2026; the loopback flow (a local HTTP listener on
localhost during the one-time auth) is now the only supported path for a
CLI-based install like this one.

## 6. Generate the refresh token

Install `google-ads-python` locally (`pip install google-ads`) and run its
bundled `examples/authentication/generate_user_credentials.py` script with
your client ID and client secret. It opens a browser, you sign in and
approve the `adwords` scope, and the script prints a refresh token. This
token does not expire (because you published the app in step 4) and is
what organic-os uses on every subsequent call - you do this once per
account.

## 7. Store the credentials

Write the five `GOOGLE_ADS_*` variables into the per-site env file:

```
mkdir -p ~/.config/organic-os
cat >> ~/.config/organic-os/<site-slug>.env <<'EOF'
GOOGLE_ADS_DEVELOPER_TOKEN=xxxxxxxxxxxxxxxxxxxxxx
GOOGLE_ADS_CLIENT_ID=xxxxxxxxxxxx.apps.googleusercontent.com
GOOGLE_ADS_CLIENT_SECRET=xxxxxxxxxxxxxxxxxxxx
GOOGLE_ADS_REFRESH_TOKEN=1//xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
GOOGLE_ADS_LOGIN_CUSTOMER_ID=1234567890
EOF
chmod 600 ~/.config/organic-os/<site-slug>.env
```

`GOOGLE_ADS_LOGIN_CUSTOMER_ID` is the Manager account ID (digits only, no
dashes); it is required whenever you are calling the API through a Manager
account rather than directly against a standalone ads account. Never commit
this file; it stays outside the brain repo entirely.

## 8. Verify at whatever tier you have

Before assuming anything is broken, confirm the credentials work at all:
call `ListAccessibleCustomers` and run one simple GAQL query (for example,
`SELECT customer.id FROM customer LIMIT 1`) against your own account. Both
work at every access tier, including Test Account and Explorer, so a
failure here means the credentials are wrong, not that you need a higher
tier.

## 9. Apply for Basic access

Basic access is required for keyword planning - Explorer blocks the
planner services outright (`GenerateKeywordIdeas` and
`GenerateKeywordHistoricalMetrics` both fail with a permission error at
Explorer). Apply from the same API Center page. Google's stated turnaround
is roughly 5 business days; the 2026 review backlog is acknowledged by
Google in their own status updates, so expect longer in practice, sometimes
several weeks. Strengthen your application: complete advertiser
verification first, and in the use-case text be specific rather than
generic - "keyword research and reporting for my own accounts", naming the
actual accounts, reads far better to a reviewer than a one-line business
description.

## 10. What each tier enables

| Tier | Planner (ideas, historical metrics, forecasts) | Reporting (GAQL over your own accounts) | Typical daily quota |
|---|---|---|---|
| Test Account | Blocked | Test accounts only, no real data | Minimal, test data only |
| Explorer | Blocked (`PERMISSION_DENIED`) | Full read access to accounts you manage | Small, rate-limited |
| Basic | Full: ideas, historical metrics (batches of 200-500), forecasts | Full | Standard operational quota |
| Standard | Full, same as Basic, higher volume | Full | Higher quota, for larger operations |

`hoo-keyword-intel` detects your tier by probing the planner with a real
one-seed request rather than trusting `google_ads.status` in the profile -
Google's own tier reporting lags the actual grant, so a probe is the only
reliable signal. Explorer-tier accounts still get full value from
`hoo-keyword-intel`'s GAQL-only mode: search-term mining and quality-score
review over your own account data, with an honest note that planner calls
are blocked until Basic comes through.

## No token, no problem

If you never request a token, or you are waiting on the Basic review,
`hoo-keyword-intel` falls back to GSC query mining (16 months of query data
via your Search Console connector) and CSV import (Keyword Planner UI
exports, Auction Insights exports). Every tier produces the same shape of
output - a ranked opportunity list with volume or a volume proxy, a
difficulty proxy, an intent guess, and a recommended action - so nothing
about the workflow changes while you wait.
