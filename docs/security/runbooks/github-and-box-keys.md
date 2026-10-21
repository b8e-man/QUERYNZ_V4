# The keys the boxes use for GitHub, and for each other

**Why:** a new repository (QUERYNZ_V4) was added on 18 October 2026 using
the key pair node2 has had since 30 July. A key per purpose, and a review
of what the old ones can reach, is due.

**What exists:** `~/.ssh/id_ed25519` on node2 (and node1's own pair).
Node2's public key is on the GitHub account and in node1's
`authorized_keys`; node1's is in node2's. The same key therefore reaches
GitHub, the mirror on node1, the residue and WAL mirrors and the
installer's credential copy.

**Where:** GitHub → the repository QUERYNZ_V4 → Settings → Deploy keys →
Add deploy key. Then QueryNZ_V3 → Settings → Deploy keys: review; the
frozen repository takes no push except an emergency fix, so its key may be
read-only. Your account's own SSH keys page: remove any key you do not
recognise.

**Permissions:** the new repository's deploy key: write access (sessions
push branches). The old repository's: read-only unless an emergency fix
is on. Nothing account-wide.

**At the box, node2:** a new pair for GitHub only, kept apart from the
box-to-box key:

```
ssh-keygen -t ed25519 -f ~/.ssh/id_github_qv4 -C node2-querynzv4
```

Paste the `.pub` into the deploy key page. In `~/.ssh/config` on node2:

```
Host github.com
  IdentityFile ~/.ssh/id_github_qv4
  IdentitiesOnly yes
```

The box-to-box key stays as it is until node1 is set up again; then
node1's new pair replaces its old one in node2's `authorized_keys`.

**Tell the session:** "keys done".

**The session then proves, verdicts only, on node2 in `/home/user/querynzv4`:**

1. A push works: `git push --dry-run origin session/<branch>` reports
   up to date or what it would push, with no prompt.
2. `ssh -T git@github.com` greets the account.
3. The old key, if removed from GitHub, is refused: the greeting names the
   new key only (GitHub shows which key authenticated under Settings → SSH
   keys → last used).

**Inventory line:** the GitHub keys row, "Last rotated: <date>; a deploy
key per repository".
