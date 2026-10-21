# Where secrets have leaked: places only (track H.2)

Run on node2 on 22 October 2026 by `security-1` with
`support/security/leaks.py` (`python -m support.security.leaks`). It reads
every added line and commit message of the old repository's history (the
reference copy `/home/user/qnz3-ref`, 2,509 commits, plus the live old
folder's four newer commits), every saved session transcript under
`~/.claude/projects` (7.2 GB; 2,415,416 lines), the Claude settings files
on this box (`~/.claude.json`, `~/.claude/settings.json`, the main
checkout's and the live old folder's `.claude/`), the shell history
(`~/.bash_history`, `~/.python_history`), and both journals (system
8,459,537 lines, user 8,352,245 lines). Every line is run against the
shapes in `support/security/shapes.py`. It prints a place, a kind and a
liveness verdict, never a value: "current" below means the place matches
the value in force today, compared by hash against the value handed in
one variable at a time. Node1 was not searched (its card).

**Nothing found in the journals, the Claude settings files or the Python
history.** The settings files once carried a database password inside
allowed commands; they do not now. Everything found is in the old
project's transcript, the shell history, the old repository's examples,
and a few new-estate transcripts that quoted the old examples.

## Current values, by secret

| Secret | Places | Still live | Where |
| --- | --- | --- | --- |
| The deploy token for the public site (`CF_API_TOKEN`) | 6 | **Yes: the token in use today** | The old project's transcript `~/.claude/projects/-home-user-Git-Repos-QueryNZ-V3/d51f6658-8166-462e-8432-e293705be9b9.jsonl`, lines 2117811, 2117814, 2119800, 2126795, 2133440, 2142904: one pasted message, repeated in context. Eleven more places in the same file (lines 2113191 to 2118560) hold the two earlier tokens, which differ from today's |
| The database application role's password | 309 | **Yes** | The same transcript: 214 places as a connection string and 86 places as the topic of an example alarm address in a test fixture (the password is the same string as that fixture's topic; the old repository carries it at `tests/test_dsn_import_shape.py:325`, commit b91feac2990f). Also `~/.bash_history` lines 505, 507, 509; the main checkout's transcript `-home-user-querynzv4/dce143f7-ec2b-41cb-b0df-5b88a168382b.jsonl` line 3391; a companies subagent transcript (`-home-user-querynzv4-work-companies/.../subagents/agent-a739b1bbc533f4676.jsonl` line 26); an old-project subagent (`agent-a7083ad758d9fd210.jsonl`); and two lines of this session's own transcript (`-home-user-querynzv4-work-security/5e8f3b2c-2efd-4ae4-a7c2-d15a31290e40.jsonl`), where a documentation example was echoed in a context window before the shape was widened to catch it |
| The alarm address (`ALERT_NTFY_URL`) | 1 | **Yes** | An old-project subagent transcript, `.../d51f6658-8166-462e-8432-e293705be9b9/subagents/agent-aca4546c517166f29.jsonl` line 189 (the file's contents were printed) |

## Earlier or other values, by secret

| Secret | Places | Still live | Where |
| --- | --- | --- | --- |
| The two earlier deploy tokens | 11 | No (rolled 3 October; revoked per the record) | The old project's transcript, lines 2113191 to 2118560 |
| The NZBN key as it arrived (`NZBN_API_KEY`) | 50 | Differs from today's key | The old project's transcript (chat arrival, 26 August, repeated in context) and the old repository's `data-layer/nzbn_canonical/docs/delta-import.md:46` (commit d32f5361f1f8): a documentation example, not the key |
| The replication password of 24 August | 3 | No (rotated 5 September) | `~/.bash_history` lines 475, 479, 496 |
| The serving role's three connection strings | 3 | Not compared (the file could not be read in this session's mode); treat as current | `~/.bash_history` lines 621, 622, 623 (5 September, when the file was written) |
| The serving role's password at minting (`QNZ_SERVING_PASSWORD`) | 1 | Differs from the values given | The old project's transcript |
| Cloud model keys (`NOUS_API_KEY`, `LLM_API_KEY`) | 5 | Differ from today's | The old project's transcript and a subagent (hook test strings); the old repository's `ingestion/.env.example:2` (an example) |
| The LINZ key (`LINZ_API_KEY`) | 1 | Differs | An old-project subagent transcript (`agent-a7bd643b02c67b26e.jsonl` line 66), a shell fallback expression |
| An alarm topic of 4 September | 11 | Differs from today's | The old project's transcript and the old repository's `data-layer/docs/ARTHUR_RUNSHEET.md:847` (a prefix with a placeholder) |
| Storage key ids (`aws-key-id` shape) | 5 | Differ from today's | The old project's transcript |
| A web page's own auth token, a test's `[:x@evil` parser fixture, a daylog's password remark | 13 | Not ours, or differ | The old project's transcript; `data-layer/docs/ledger/2026-09-daylogs.md:755` and `issues-ledger.md:3522` (commits 09e20a252a46, 8432ebe14dde); `data-layer/modelgate/tests/test_client.py:125` |
| This session's own fixture (`support/security/tests/test_leaks.py`) | 42 | Synthetic, never secrets | This session's transcript |

## What follows

- Every current place is cleaned by rotation, not by editing: the deploy
  token (wave one, first), the alarm address (wave one), the application
  role (wave two). The card `leaked-places-outside-the-repository-wait-on-arthur-to-clean`
  says what Arthur removes afterwards and in what order.
- The old repository's history holds no current value and is not rewritten.
- Rerun after each rotation: the same command, and the matching places
  should all read "differs". The scan over the transcripts and journals
  takes about half an hour on node2.
