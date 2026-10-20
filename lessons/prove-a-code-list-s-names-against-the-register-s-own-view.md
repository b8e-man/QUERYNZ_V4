A build that resolves a code through a list must prove the names against the register's own view: the Opus charities build did and was right on all 46,121; the Fable build trusted the lists' ids, mis-sectored 42,771, and said all resolved.
area: step 4.1 charities, two builds of one lane, code lists, checks that pass while wrong, the models table (map.md "Measure it once")
paid-for-by: 2026-10-21, the integrator's comparison of charities_a (Fable) and charities_b (Opus), full loads in the sample database

The plan gave both models the same lane, the same capture and the same
outside measures (plan map.md, "Measure it once"). The integrator compared
the two full loads table by table on the register's own identifiers:

- Returns: 430,437 rows in each, every key shared, period, tier, income,
  expenditure, audit flag and opinion equal on all. Both builds read money
  the same way.
- Charities: 46,121 shared keys (3 only in the Fable build, 10 only in the
  Opus build: the nine numbers held by two rows and the five blank rows,
  handled differently and both documented). Status, dates and legal
  structure equal on all. Main sector differs on 42,771, main activity on
  33,729, main beneficiary on 37,755. The register's view page
  (`vOrganisations`) for CC10001 names the Opus build's reading; the Opus
  build's check compares every charity with the view, the Fable build's
  check never reads the view and reported "main codes resolved 46,124 of
  46,124".
- Officers: 589,104 shared identifiers. The Fable build flagged 4,252
  officers disqualified against the Opus build's 521; of the Fable build's
  extra 3,747, 3,076 are officers the register lists as Past or Qualified
  whose `IsNotDisqualified` boolean is false, and 525 have status "Not
  Qualified". The Opus build takes the register's own status
  ("Disqualified", "Removed as Disqualified") and keeps the boolean aside
  unpublished; the Fable build missed the 16 "Removed as Disqualified". A
  wrongly published disqualification is a harm to a named person.
- Names and roles: the Fable build kept the feed's doubled spaces and line
  breaks in 252 names and 680 roles ("Committee  Member"); the Opus build
  collapsed them. 452 organisation names differ the same way.

Kept: the Opus build (charities_b). The models table stands: a register
lane with a brief, a table shape and tests goes to Opus. The Fable build's
two lessons on name fields (dates and addresses inside them) and on
reading a page by its shapes stand on their own and are kept in the index.
