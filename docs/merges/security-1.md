# security-1: track H.1 to H.3 (the inventory, the leak search, the runbooks)
branch: session/security (pushed; 1897e52)
session: security-1
raised: 2026-10-22
claims: lessons/a-secret-shaped-literal-never-enters-a-tracked-file-even-as-a-fixture.md; support/security/ (shapes.py, inventory.py, leaks.py, tests/, README.md); docs/security/ (inventory.md, leaks.md, runbooks/, README.md); docs/status/security.md; lessons/a-leak-finder-proves-liveness-by-hash-and-prints-places-only.md; cards/node1-was-not-walked-for-the-credential-inventory.md, cards/the-application-role-s-password-is-a-string-the-old-repository-carries.md, cards/leaked-places-outside-the-repository-wait-on-arthur-to-clean.md; docs/decisions/queue/two-credential-files-nothing-reads-sync-env-and-x-env.md, docs/decisions/queue/the-alarm-address-lives-outside-the-credential-directory.md

What it claims. H.1: the credential inventory, walked on node2 by
verdict-only presence checks (never a listing, never a value), with a
checker and a fast-tier test: every name the new estate's code or a
`qv4-` unit reads from a credential file is in the inventory, and no
value-shaped string sits under `docs/security/`. H.2: the leak finder,
run over the old repository's whole history, every saved transcript, the
Claude settings files, the shell history and both journals; places only;
liveness by hash from values handed in one variable at a time; tested on
a generated fixture. H.3: thirteen runbooks. No rotation was done, no
credential file was changed, no job was touched.

Verified: `support/security` tests green (11); `python -m
support.security.inventory` prints both "yes" verdicts; the finder's
summary names the lines scanned per source, so its empty results (the
journals, the settings files) are findings and not silence.

What the integrator must do:

1. Run the gate and merge. The security tests need no database, no
   network, no model.
2. Regenerate the card board, the lessons index and the decision queue.
3. Tell Arthur, in the end note, the three things that are current in
   transcripts (`docs/security/leaks.md`): the deploy token in use today,
   the application role's password, the alarm address. The deploy token's
   runbook is first.
4. Nothing to install: this branch adds no `qv4-` unit and no job.

Nothing new was learned that is not in the lesson.

## Result (integrator, )

Merged into main as 98d05cf (`merge integrate/security-1: gate green`). Branch `integrate/security-1` from `session/security`, main merged; board, lessons index and queue regenerated. Checked before the gate: no secret-shaped string under docs/security or support/security (the four long strings are the generated test fixture and a file path). Fast tier green in 577.4 s (target 300 missed, recorded); gate green, nothing to load, nothing installed. Ruling 79 (22 October): the sittings wait until after the build; the runbooks stand. Branches and the working copy retired.

Correction (integrator, 2026-10-22 08:25 NZDT): the merge above (98d05cf) was refused by GitHub's push protection on the test fixtures' planted literals (an AKIA-shaped key id and two 40-character tokens; the finder run on them against the live values says every one differs). Rebuilt as one commit on `integrate/security-1b` with the planted values built at run time, gate green again, merged into main as dfcae53 and pushed. Lesson `a-planted-secret-in-a-test-fixture-is-built-at-run-time-never-written-as-a-literal`. The remote branch `session/security` still carries the literals; a deleting push is refused by the safety hook.
