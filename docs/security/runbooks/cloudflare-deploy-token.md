# The deploy token for followthemoney.nz

**Arthur issues and places it himself. No session reads, moves, copies or
re-creates the old one** (hard limit 2). It has reached a transcript twice
(the first publish on 2 October 2026; the roll of 3 October). Whoever holds
it can change what the public site serves, during an election. First in
wave one.

**Where:** the Cloudflare dashboard → My Profile → API Tokens → Create
Token → Custom token.

**Permissions, exactly these three and nothing else** (the narrowing is
what the check proves): Account · Workers Scripts · Edit; Account ·
Workers KV Storage · Edit; Account · Account Settings · Read. Account
resource: this account only. No zone permissions, no user permissions, no
expiry shorter than a year unless you want a diary entry.

**File and variable, node2:** `~/.querynz/cloudflare.env`, the line
`CF_API_TOKEN=`. `CF_ACCOUNT_ID=` beside it stays. Copy the token from the
dashboard's one-time view straight into the file at the box. Then, in the
dashboard, **revoke (delete) the previous token.** Both are needed: a
revoked token is the "refused" proof.

**Timing:** not within an hour of 06:19, when `ftm-release.timer` deploys.

**Tell the session:** "rotated".

**The session then proves, verdicts only, on node2 from the reference
copy `/home/user/qnz3-ref` (never the live old folder):**

1. `ops/cloudflare_token_check.py` with the token read one variable at a
   time: works, and narrow (the user, token-list, DNS and zone calls all
   refused).
2. `ops/pi_cloudflare.py --deployments`: lists the deployments.
3. The integrator runs `ops/pi_release.py --dry-run` (a founding-weight
   session is the only one the hooks let do this), then the next 06:19
   release is green.
4. "Refused" is the dashboard's token list showing one token: the old
   one is gone. The session never held it, so it cannot try it, and must not.

**Inventory line:** `docs/security/inventory.md`, the deploy token row,
"Last rotated: <date>, by the no-chat path; both proofs green".
