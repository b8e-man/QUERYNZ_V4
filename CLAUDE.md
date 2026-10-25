# QueryNZV4

An estate of New Zealand public records. It copies public registers, builds
registers where none exists, links rows across them, answers questions from
them with a citation, and checks itself. The spine is the joined registers;
people, products and the board are views of it. The first product is Follow
the Money, rebuilt here and compared with the frozen site. Nothing goes on
the public site without Arthur's word.

The plan is the master. `docs/PLAN.md` is its index and names what each
session reads; `docs/plan/map.md` says where everything is and what the
words mean; `docs/plan/core.md` is how the work runs; `docs/plan/headings.md`
finds any heading or step number. Where this file and the plan differ, the
plan wins. The hard limits below are the one thing nothing overrides.

## Three weights of session

| Weight | Started with | Reads | May change |
| --- | --- | --- | --- |
| Question | `bin/ask` | This file, then only what the question needs | Nothing |
| Fix | `bin/fix <module>` | This file, the index, `core.md`, the one module's spec | That module |
| Build | `bin/start-session <name> <folders>` | The same, then its step or track file, `docs/status.md`, its own status file, the specs it touches | Its folders |

A founding or integrator session (`bin/start-session --main …`) sees the
whole repository. The scope file `.scope` in the working copy is the fence;
without one nothing may be written.

## A question session

You change nothing: the hooks refuse every edit inside the repository and
every command that commits, pushes, merges, installs or controls a job; your
only database login can read; you run in a throwaway copy. Answer from what
is published first: the published tables through `bin/q`, the board,
`docs/status.md`, `docs/board.md`, the module specs. Read code or a lane's
inner tables only when the question is about them. Never print a person's
home address or a suppressed name. A fault you find goes as a note into
`/home/user/querynzv4-work/inbox/cards/`. When a question turns into work,
give Arthur the one line that starts a fix or build session; do not do the
work. Write to Arthur in plain language, short, every term defined.

## Paths every session needs

- Main checkout: `/home/user/querynzv4`. Working copies: `/home/user/querynzv4-work/<name>`.
- The live old folder, not to be touched: `/home/user/Git Repos/QueryNZ_V3` (the frozen product runs from it).
- The reference copy of the old repository, for reading old code: `/home/user/qnz3-ref`.
- The inbox: `/home/user/querynzv4-work/inbox/` (`merge-requests/`, `cards/`).
- Where things stand: `docs/status.md`. The card board: `docs/board.md`. Decisions: `docs/decisions/`.
- Credentials: `~/.querynz/*.env` and nowhere else.

## Hard limits

These are never traded for convenience, speed or a passing test. If a step in this plan seems to require breaking one, stop that piece of work and put it in the decision queue marked "no default".

**Secrets**

1. **Credentials live in `~/.querynz/*.env` and nowhere else.** Never in the repository, a brief, a log, a card, a commit message or a chat reply. If you see one in a file or a transcript, do not repeat it; note where it is and tell Arthur.
2. **The deploy token for the daily release has been exposed in a transcript twice.** Replacing it is the first item of track H: Arthur issues the new one and puts it in place himself. Do not print, move, copy or re-create it. Nothing in the new estate uses it.
3. **Bypass-permissions mode is never used on the bare box.** Sessions run on a reviewed list of allowed commands, set up in step 1.

**What may be collected**

4. **Capture is judged on legality and politeness.** Four questions per source: is the page open without getting past a lock; is storing it lawful copying; what terms did we accept; what does privacy law or the register's own statute limit.
5. **A robots file is no longer a permission decision** (ruling 10: legality and politeness, "not inferred intent"). It is read for one thing, a stated crawl delay, which is honoured. The old fetch gate refuses on a robots file for most hosts; the new estate's copy replaces that refusal with the rules in this section.
6. **Never solve a challenge or CAPTCHA, never use a login that is not ours, never get around a block.** A headed browser that is shown no challenge may read a page; shown one, it stops. A challenged read is a failed read. Log it and move on.
7. **Be polite:** slow, low-concurrency, off-peak, cached so nothing is fetched twice. A publisher's direct request to stop is honoured.
8. **Two sources are out by name:** fyi.org.nz (old ruling 321) and every NZME masthead, the NZ Herald included (ruling 12). Neither is captured, indexed or read.
9. **Every new class of source gets a one-page legal position** from the four questions, written before the product that shows it (ruling 61: before product, not before capture; the capture is judged on the four questions as it goes). A lawyer reviews those pages before anything is sold.

**What may leave the boxes**

10. **No text leaves the boxes for a cloud model** (old ruling 172). Every model used by a job, for reading, embedding, review or answering questions, runs on the boxes.
11. **A session is the one exception that already exists, whatever its weight.** You read code, and samples of data, in order to build, to check, and to answer Arthur's questions. Keep it to samples. Never pass a register or the corpus through a session in bulk. Never print a person's home address or a suppressed name into a session, a card, a lesson or a log. The exact wording of this limit is in the decision queue.
12. **A web search by the review agent carries a name and a public role at most.** Never an address, and never anything from the sealed store.
13. **Nothing built here is opened to strangers or sold** until Arthur says so. Every product's surface listens on the local network only. Legal work comes after the build and before selling (ruling 2).
14. **No new connection about a named person goes on the public site** without Arthur's decision at that time.

**What may be shown**

15. **A person's home address is never shown or extractable.** No published table and no export carries one. A company's registered address is shown. One exception, ruling 88 (26 October 2026): the board, which listens on the local network only and is Arthur's own instrument, may open a captured document whole, the addresses it prints included; the board itself still publishes no table and no export, and a session still never prints one.
16. **A suppressed name is suppressed on every surface;** the row and the money stay.
17. **Papers Past is searched, not mined.** No people, claims or links are built from it. Its name index stays inside the history product and never feeds the links.

**What may be deleted**

| Class | Examples | Rule |
| --- | --- | --- |
| Cannot be regenerated | Captured documents, decisions, ledgers, corrections, document profiles, answer sets, anything a person typed | Never deleted. Withdrawn or quarantined |
| Can be regenerated | Registers, links, groups, indexes, scratch tables, build output | Deleted freely. A lane wiping and reloading its own tables is the design |
| Quarantined | Anything set aside | Kept for a fixed period, then removable on Arthur's word with a logged line |

18. **The old estate's data is deleted only when Arthur agrees the new estate has consumed it.**

**The frozen product**

19. **The old repository takes no commit after the freeze tag** except an emergency fix: the daily release is broken, or a published figure is wrong. That is Arthur's word each time.
20. **The daily release keeps running throughout.** Nothing in this plan pauses it.
21. **Nothing that feeds the public site is switched before the election on 7 November 2026.** Build beside it until then. This stands until Arthur rules otherwise.
22. **This plan authorises exactly three kinds of change to the old estate:** stopping old jobs that are outside the carve-out, with proof (step 1.4), and the freeze commits (step 1.5). Both may be done before the election, because the proof shows the site does not change. The third is rotating passwords and keys under track H, which changes credential files and restarts jobs but never the old repository; each sitting is on Arthur's word. Everything else that would touch the old estate's jobs, its database server settings or its files, including the off-site copy, takeover and any drill, is built and rehearsed beside it. It is applied to the live database server or the old jobs only on Arthur's word, and not before the election.
23. **Every job the new estate installs carries the prefix `qv4-`.** The installer never changes or removes a job without that prefix. A new build of the model server is installed beside the old one, never over the program the frozen product's two servers use.

**Machinery**

24. **The safety hook and the scope hook stay on** in every session.
25. **A graphics card holds one model profile at a time.** Jobs that share that profile may share its slots. Every swap is recorded.
26. **The review agent may search the web only for evidence that two rows are different people.** It never confirms a link from the web, because web presence favours the prominent.

