# The subscriber logins (NBR, BusinessDesk, Newsroom): remove

**Why:** none of the three outlets is captured any more (BusinessDesk is
NZME's, hard limit 8; NBR and Newsroom are paywalled and not captured).
A login nobody uses is only a liability.

**Where:** the three accounts' own sites, if you want the passwords
changed there too (your call; the estate stops holding them either way).

**File and variables, node2 (and node1 if the file exists there):**
`~/.querynz/newsscrapers.env`: remove the lines `NBR_ACCOUNT_EMAIL=`,
`NBR_ACCOUNT_PASSWORD=`, `BUSINESSDESK_EMAIL=`, `BUSINESSDESK_PASSWORD=`,
`NEWSROOM_EMAIL=`, `NEWSROOM_PASSWORD=`, or remove the file. Remove
`~/.querynz/nbr_cookies.json` as well: it is a cached NBR session.

**Before removing the file:** the old units that name it
(`newsscrapers.service`, `newsscrapers-daily.service`) are on the stop
list, but their timers were still active on node2 on 22 October;
`courts-capture.service` names it as optional. With the file gone the two
news units fail at start, which is the intent, and the courts capture runs
without it. The session stops the two timers (they are on the stop list)
when you say "removed".

**Tell the session:** "removed".

**The session then proves, verdicts only, on node2:**

1. Each of the six variables is absent, and the cookie file is absent.
2. Nothing active reads them: `newsscrapers.timer` and
   `newsscrapers-daily.timer` inactive; `courts-capture.service`'s next run
   green.

**Inventory line:** the subscriber logins row struck through, "removed
<date>", kept for one release.
