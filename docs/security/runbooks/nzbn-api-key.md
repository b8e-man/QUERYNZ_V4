# The business-number interface key (NZBN)

**Why:** the key passed through chat when it arrived (26 August 2026). It
reaches an outside service: anyone holding it can query the register in
our name and spend our quota.

**Where:** the MBIE API developer portal (api.business.govt.nz) → your
application for the NZBN API → Subscriptions. Regenerate the subscription
key (the portal offers a primary and a secondary key; regenerate the one
in use, or switch to the other and regenerate the first after the proof).

**Permissions:** the same NZBN API product subscription as now; nothing
else.

**File and variable, both boxes:** `~/.querynz/nzbn.env`, the line
`NZBN_API_KEY=`. Node2 first. Node1 when it is set up again (the new
installer copies the credential files box to box; until then, copy it at
node1's own keyboard, never through a session).

**Tell the session:** "rotated".

**The session then proves, verdicts only, on node2 in
`/home/user/querynzv4`:**

1. One lookup works: `registers/limited_partnerships/capture.py --fetch
   <one business number> --anytime --database querynz_v4_sample` (a handful,
   to prove the path), or the companies monitor's probe. Prints "works" or
   the refusal.
2. The old key is refused: the session never held it, so the proof is the
   portal showing the regenerated key only. If both keys are kept at the
   portal, regenerate the other too, so no old value is accepted.
3. The nightly `qv4-companies-monitor` run after the change is green.

**Inventory line:** the NZBN row, "Last rotated: <date>".
