# The cloud model keys: revoke and remove

**Why:** no job may use a cloud model (hard limit 10), so these keys
should not exist on the boxes. The new estate reads none of them; the old
jobs that did (`querynz-research`, `querynz-sweep`) are stopped.

**Where:** the Nous account's API keys page: revoke the key behind
`NOUS_API_KEY`. The account behind `LLM_API_KEY` (the provider named in
the old `llm.env`'s comment, or the password manager entry "QueryNZ — LLM /
research API keys"): revoke that key too.

**Permissions:** none remain.

**Files and variables, both boxes:** remove the lines, or the files, at
the box:

- `~/.querynz/llm.env`: `LLM_API_KEY=`
- `~/.querynz/api.env`: `NOUS_API_KEY=` (the file's other lines, model
  overrides, may stay)
- `~/.querynz/remedial.env`: `NOUS_API_KEY=`

**Tell the session:** "revoked and removed".

**The session then proves, verdicts only, on node2 in `/home/user/querynzv4`:**

1. The model client's tests that no lane can call out
   (`support/modelclient/tests`: a cloud address is refused before any
   bytes leave) pass in the fast tier.
2. Each variable is absent: one presence check per name, "absent".
3. Nothing installed reads them: no `qv4-` unit names `llm.env`,
   `api.env` or `remedial.env` (the inventory test), and the old units that
   did are inactive.

**Inventory line:** the cloud model keys row struck through, "revoked and
removed <date>", kept for one release.
