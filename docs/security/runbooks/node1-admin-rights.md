# Admin rights on node1 (carried from H.7)

**What:** the admin-rights file (`sudoers`) on node1 was never redone
after node2's was, so commands that need no password on node2 still ask
on node1. Unattended jobs there that need one of those commands stall.
**Arthur's, at node1's own keyboard.** Not a secret, but a privileged
setup, so it is his.

**Where:** on node1, as root: `visudo -f /etc/sudoers.d/querynz`. The
reference text is the old repository's `ops/production/sudoers-querynz`
(read it from the reference copy on node2, `/home/user/qnz3-ref`, never
pasted from a session). It grants the user named command groups
(Postgres, storage, network, system) without a password and nothing
else; keep its shape.

**Permissions:** exactly the command aliases that file names; no
`ALL=(ALL) NOPASSWD: ALL`.

**File:** `/etc/sudoers.d/querynz` on node1, mode 0440. `visudo -c` must
say the file is OK before you leave.

**When:** with node1's setup card (ruling 57), not before. It does not
wait on the election; it changes nothing the public site stands on.

**Tell the session:** "node1 sudoers done".

**The session then proves, verdicts only, from node2 once it may log in
to node1:** one command from each alias group runs without a prompt
(`sudo -n true` and `sudo -n -u postgres true` print nothing and exit 0);
a command outside the groups still asks.

**Inventory line:** the admin-rights row, "redone <date>".
