# recruitment-2: template 08 takes the flag and the common rules from the contract
branch: session/recruitment-2 (pushed; f1be57b)
session: recruitment-2 (fix in the recruitment template's folder)
raised: 2026-10-20
claims: products/templates/08-recruitment/rules.py, template.toml (0.1 → 0.2), README.md, limits.md, checkpoint.list (new), tests/test_recruitment_template.py, tests/test_recruitment_real.py; lesson `a-checkpoint-keeps-its-subjects-keys-in-git`; docs/status/recruitment.md

**Changed.** `rules.py` no longer carries its own `flag`, `items`,
`section` or `_all`, nor its `identity` (a copy of group-standing) and
`replaced_rows` (a copy of replaced-return). One line takes `flag`,
`items`, `section` and `all_items` from the `contract` the shape binds
before the file runs; no import, so the one-way test is unchanged and
green. The builder's three common rules (group-standing, hubs-met,
replaced-return) run for the template; its own eleven flags stay as they
were, `subject-hub` among them (the subject itself a hub, not the hubs met).

**Tests.** The fixture loader binds `contract` from
`products/report/contract.py`, read by path, as the shape's loader does. The
test that checked `identity` now checks that no rule here carries a common
rule's name or `identity`, that `template.toml` keeps the common rules, and
that `flag` and the helpers are the contract's own. The slow tests (memos
through `python -m products.report render`) require each common flag
exactly once in every memo and no `identity`. 21 fast and 3 slow green;
`bin/fast products/templates/08-recruitment` green in 24.9 s;
`python -m products.report check` green; `templates` lists recruitment
0.2 with 11 rules.

**Measured on the checkpoint's twelve real subjects,** before and after,
through the CLI (keys now in `checkpoint.list`; they were only in the
`recruitment` scratch folder): all twelve print, none refused, 0.1 to 5.1 s.
The diff, build time aside: the `identity` line gone and `replaced-return`
@0.1 → @0.2, in every memo, and nothing else. `group-standing` gives the
same status and severity `identity` gave on each (four fired amber,
eight clear). Each memo holds 14 flags.

**Card.** `a-template-cannot-reach-the-flag-contract-or-the-shapes-rules`
was already closed by report-2; this is the fix in this folder that it
named. Nothing new carded. `limits.md` now says the two refusal cards are
closed; it still lists `a-donation-row-start-has-no-group` and the Gazette
notice date as limits though those cards are closed too, not re-checked
here.

## Result (integrator, 2026-10-20 19:12 NZDT)

Merged to main at ad20978, gate green. `qv4-report` restarted on it
(template 08 at 0.2, 14 flags a memo). The two closed cards still listed on
`limits.md` as limits are the template's next session's to re-check.
Worktree and branch retired.
