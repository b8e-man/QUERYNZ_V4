# The alarm address (ntfy)

**Why:** the address is the whole secret: anyone who has it can read every
alarm and send false ones to your phone. It has been in one shell history
and in the old estate's records as a prefix.

**Where:** ntfy.sh (or your own ntfy). A topic is an address; make a new
one by choosing a new long random name, in the password manager. If the
topic is reserved under an ntfy account, reserve the new one and release
the old.

**Permissions:** none to grant. If reserved: read and write for your
account only, everyone else denied.

**File and variable, node2 (and node1 when it is back):**
`/home/user/Git Repos/QueryNZ_V3/ops/config/alert-channel.env` in the
live old folder, the line `ALERT_NTFY_URL=`. This is the one secret that
lives outside the credential directory; the plan's map accepts it, and
whether to move it into `~/.querynz/` is in the decision queue (default:
leave it; both estates read that path). Edit it at the box; the file is
ignored by git and is not a commit to the frozen repository.

**The phone:** subscribe the ntfy app to the new topic; unsubscribe the
old.

**Tell the session:** "rotated".

**The session then proves, verdicts only, on node2 in `/home/user/querynzv4`:**

1. A test alarm arrives: `python -c 'from support.alarm import send;
   print(send("qv4 node2: test alarm", "rotation proof"))'` prints True
   and the phone shows it. The session never prints the address.
2. The old topic is refused or silent: nothing more is sent to it; if it
   was reserved, its page refuses anonymous posts.

**Inventory line:** the alarm address row, "Last rotated: <date>".
