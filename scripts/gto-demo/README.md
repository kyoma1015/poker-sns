# Poker ID standalone research prototype

`node scripts/gto-demo/build.mjs` deterministically builds
`public/gto-demo/index.html` from existing8research ranges and refined model EVs.
The single HTML contains all script,style and data. No build tool,auth,Supabase,
account,key,cookie,storage,API,CDN or network connection is needed to use it.
CSP pins the exact script/style hashes and denies connections/forms/resources.

Open the HTML in a normal browser,or serve this DIRECTORY with any static server.
Never claim that a localhost URL is a publicly accessible demo. Managed browsers
may prohibit file URLs by administrator policy; do not disable that protection.
CI separately verifies actual offline file navigation in its isolated browser.

Four preflop stages × two continuation models =8contexts/1352hand rows.
Tap any169hand class,change stage/model,or use arrow keys. Frequencies are frozen;
EVs/99% intervals concern the stated model,not real-game GTO. Warning remains
visible in the page. The ablation model is not a newly validated GTO range.

Verification:
`node --test --test-isolation=none tests/gto-demo.test.mjs`
`node tests/gto-demo-browser.mjs` (existing pinned Playwright browser required).
CI uploads the HTML and a mobile screenshot as poker-id-gto-offline-demo for
3days. Artifact download can require GitHub login; this is NOT a public demo URL.
Opening the downloaded HTML does not require app login.

Publishing is a separate operation. Repository metadata currently says
has_pages=false. No new Pages/project/deploy/SSO settings were enabled. Existing
production/Preview protection remains unchanged. A public URL must be tested
without credentials before describing it as READY. This change prepares the
static artifact and CI only; no unverified hosting URL is advertised.
