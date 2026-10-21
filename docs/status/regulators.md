# regulators: where the three step 5.3 regulator lanes stand

Session regulators-1 (Opus), 21 October 2026, node2. Merge request `regulators-1`.

## The four questions (positions in each lane's `position/`, to move)

| Source | Open? | Lawful copy? | Terms | Statute, privacy | Outcome |
| --- | --- | --- | --- | --- | --- |
| Commerce Commission case register | yes, no robots delay | Crown copyright, CC BY 4.0 | none barring | names an individual rarely; "Withheld"; an investigation is not a finding | **captured** |
| FMA warnings and enforcement cases | yes (Cloudflare, no challenge; no robots file) | FMA copyright, CC BY 4.0 | none barring | address, phone, email, bank fields never read; a warning is not a finding | **captured** |
| WorkSafe court summaries and undertakings | yes, delay for Bingbot only | free reproduction, accurately, source acknowledged | none barring | a code ("2019-A") for an unnamed defendant; facts in brief never read | **captured** |

Nothing is held on terms.

## Done

- Three lanes, each built and proved on real pages through the gate (about 75 requests in all, 5 s apart, daytime):
  `registers/commerce_commission` (7 entries read, 26 tests, 13 mutants), `registers/fma` (12 warnings and cases,
  26 tests, 15 mutants), `registers/worksafe` (10 summaries and undertakings, 26 tests, 13 mutants). Fast tier
  green on all three. Passes resume from their next page (shown on the FMA and WorkSafe proofs).
- The regulators' own counts, 21 October 2026, against the old estate's (reference note): Commission 1,727 entries
  (old 112); FMA 726 warnings (old 16) and 99 enforcement cases (old none); WorkSafe 608 court summaries and 62
  undertakings (the note gives no figure). The Act and section are read on every entry that states one (the old
  estate had none of 128).

## Half-done

- No full pass yet: the first nights are the proposed jobs' (card `the-regulator-lanes-jobs-into-the-catalogue`).
  Every check is red until then, correctly.
- Known limits: parties the regulator does not separate stay one row as published; WorkSafe's "HSWA" is kept as
  stated, not expanded; old FMA warnings headed by a person's name alone are read as naming nobody.

## Waits on Arthur

- Queue, default applied: how long a regulator action naming an individual is shown (default: while the regulator
  shows it).
