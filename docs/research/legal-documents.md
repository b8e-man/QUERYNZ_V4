# How New Zealand legal documents are structured

Step 5.4 item 3. Written in the courts lane's folder by `courts-1`, whose
fence did not reach `docs/research/`, and moved here unchanged by the
integrator at the merge (card `the-courts-lane-s-edits-outside-its-fence`).

Written 21 October 2026 by courts-1, before the reading was built further
(profiles before readers), from the documents the estate holds: the old
estate's listing of 359 legal documents (pinned, sha256 8285d006…), of
which 353 files were still on disk and hashed true: 148 judgments of the
Supreme Court, the Court of Appeal and the High Court (courtsofnz.govt.nz,
July to October 2026) and 205 Waitangi Tribunal documents. No District
Court judgment is held. Every figure below is counted on those documents'
text layers (`pdftotext -layout`, page by page), never on a sample; no
model read anything. The reading built on it is `registers/courts/`
(`caption.py` is the grammar); its profiles are in
`registers/courts/profile-proposed.jsonl` until the integrator appends them
to `support/profiles/profiles.jsonl`.

## One layout, four formats

The three senior courts print a judgment's first page the same way, and a
reading that knows it needs no model:

```
[banner, when a suppression applies]
IN THE <COURT> OF NEW ZEALAND
I TE KŌTI <te reo name> O AOTEAROA
[<PLACE> REGISTRY, and its te reo name: High Court only]
                                                   <case number(s)>
                                                   [<year>] <NZSC|NZCA|NZHC> <n>
   BETWEEN        <PARTY NAME, wrapped in a right-hand column>
                  <Role>
   AND            <PARTY NAME>
                  <Role>
Hearing:   <dates>
Court:     <judges>               (Supreme Court and Court of Appeal)
Counsel:   <names> for <Role>     (or Appearances:, mostly the High Court)
Judgment:  <date> [at <time>]
                  JUDGMENT OF THE COURT  |  JUDGMENT OF <NAME> J  |  SENTENCING NOTES OF <NAME> J
   A   The appeal is dismissed.   (the orders, lettered)
______________________________
                  REASONS
[1] …
```

The text layer keeps this layout when extracted with layout kept: labels
start at the left margin, party names sit in a column about 40 characters
in, a criminal caption is centred. That geometry is what lets a reader tell
a running head or a footnote (at the margin) from a caption line.

| Profile | Recognised by (measured) | Held |
| --- | --- | --- |
| `courts-nzsc-judgment` | file `<year>-NZSC-<n>.pdf`; court line SUPREME COURT (45 of 45); `SC <n>/<year>` (45); `Court:` label (45); JUDGMENT OF THE COURT (43); REASONS (42) | 45 |
| `courts-nzca-judgment` | file `-NZCA-`; COURT OF APPEAL (38 of 38); `CA<n>/<year>` (38); `Court:` (38); JUDGMENT OF THE COURT (37) | 38 |
| `courts-nzhc-civil-judgment` | file `-NZHC-`; HIGH COURT; `<PLACE> REGISTRY` (20 of 21); `CIV-<year>-<registry>-<n>`; BETWEEN (21); often UNDER or IN THE MATTER above it (17); `Appearances:` (16) | 21 |
| `courts-nzhc-criminal-judgment` | file `-NZHC-`; HIGH COURT; registry (44 of 44); `CRI-…`; THE KING / v / defendants (39; the other 5 are appeals from the District Court, BETWEEN/AND); SENTENCING NOTES or REMARKS (33) | 44 |
| `waitangi-tribunal-report` | the Tribunal's document service; WAITANGI TRIBUNAL (200 of 205); a report (201); ISBN (128); letter of transmittal (82); a Wai number in the first pages (79) | 205 |

Every senior-court document held has a text layer on page 1; 8 have some
later pages without one (left out of the paragraph index, counted in the
row's notes). Recognition never rests on a phrase alone: the host and the
citation in the file name are read without opening the document, and a
judgment with no text layer on page 1 is set aside for the page reader
(ruling 62) rather than misread.

## Neutral citations and case numbers

- **The neutral citation** is `[<year>] <court> <n>`: NZSC, NZCA, NZHC (and
  NZDC, NZFC, NZYC for the District, Family and Youth Courts, none held). It
  is printed on a line of its own under the case numbers, and it is in the
  file name (`2026-NZSC-88.pdf`). All 148 agree with their file names.
- **Take it from its line, never the first match.** A banner above the court
  line can cite another judgment ("SEE [2021] NZHC 1426"); the old estate's
  parser took the first citation on the page and gave 7 of its 118
  judgments another case's citation.
- **One citation can be two documents**: a judgment reissued or recalled is
  published again under the same citation (2 held). A document is its
  bytes, so each is its own row, keyed by its hash.
- **Case numbers** are per court: `SC 106/2022`, `CA274/2022`,
  `CIV-2026-404-000001`, `CRI-2024-044-003886` (year, registry number,
  serial). Several case numbers on one judgment mark a consolidated appeal
  or joined proceedings (7 held, up to seven numbers).

## Parties and roles

- **BETWEEN / AND.** Each block is a name in capitals and a role in title
  case under it: Appellant, Respondent, Applicant, Plaintiff, Defendant,
  Intervener, Interested Party, Referrer; with an ordinal ("Second
  Respondent", "First and Second Appellants"), a qualifier ("Intended",
  "Cross-"), a parenthesis ("First Defendant (Discontinued)") or a court
  reference ("Respondent in SC 12/2024"). One block can hold several
  name/role pairs (First Plaintiff, then Second Plaintiff, under one
  BETWEEN): the old parser stopped at the first role and lost the rest.
- **Singular and plural.** A role in the singular ("Appellant") holds one
  party however many lines its name wraps over; a plural role
  ("Respondents") holds several. Long names wrap at the column, so line
  breaks do not separate parties: a plural block either stacks one name to
  a line, or runs a list ("A B, C D AND E F") wrapped mid-name. The reading
  rejoins a wrapped name on its evidence (a line ending OF, AND, THE or an
  open bracket; a line starting LIMITED, TRUST, a bracket), splits a list
  at the commas and ANDs outside brackets, and marks the block low. Of 590
  parties read, 166 are low; the caption itself is the limit.
- **A capacity** in lower case ("as trustees of THE … TRUST") qualifies the
  names above it; it is kept with each, not read as a party.
- **The criminal caption** has no BETWEEN: THE KING above a lone "v", each
  defendant on a line of its own below. "A B &" over "C D" is two
  defendants. The counsel lines name each defendant ("for Defendant X");
  where they do, they agree with the defendants read (5 of 5).
- **IN THE MATTER OF / UNDER** name the statute or the subject. They are a
  party only when a role follows ("… REFERENCE (NO 1 OF 2024) / Referrer").
- **Anonymised parties** are printed by the court as an initial ("W"), an
  initial with a case number ("H (SC 60/2023)") or "MR N": 27 held. They
  are the court's decision and are kept exactly as printed, never expanded.
- **A check that can fail:** every role the counsel lines are "for" must be
  held by a party read. One judgment held fails it, and the caption is
  wrong, not the reading: it prints "Appellant" where the counsel line says
  "First and Second Appellants".

## Outcomes

- The Supreme Court and the Court of Appeal print the result first, as
  lettered orders under JUDGMENT OF THE COURT ("A The appeal is
  dismissed. B Costs are reserved."), then REASONS. The reading keeps a
  closed vocabulary from those orders ("appeal dismissed", "application
  granted", "conviction quashed"): 74 of 83 have one.
- High Court judgments put the result in their last paragraphs ("Result",
  "Orders", or in prose); sentencing notes end in a sentence. None is read
  deterministically yet: the outcome arm is the place a model would help,
  under review (the old ruling: allegations recited are not findings).
- The orders are never stored as text: an order can name a person it
  suppresses.

## Numbered paragraphs

Every judgment held numbers its paragraphs `[1]`, `[2]` … at the left
margin (19,990 paragraphs across the 148), continuously through separate
reasons. Three things look like a paragraph and are not: a citation at the
start of a footnote line (`[2011] NZSC 12 …`), a paragraph quoted from
another judgment (indented, its number out of sequence) and a banner's
reference to suppressed paragraphs. The reading takes paragraphs in
sequence only, with their page, and keeps no text, so a citation can read
"[2024] NZSC 161 at [45], page 12". This is the earlier pipeline's
evidence-by-paragraph idea, ported as an index.

## Suppression markers

- **The banner** above the court line: "NOTE: PUBLICATION OF NAME, ADDRESS,
  OCCUPATION OR IDENTIFYING PARTICULARS OF COMPLAINANT PROHIBITED BY S 203
  OF THE CRIMINAL PROCEDURE ACT 2011", "ORDER PROHIBITING PUBLICATION OF
  …", a Family Court Act notice (ss 11B to 11D), an embargo "UNTIL" a time,
  or a list of suppressed paragraphs. 49 of 148 carry one; their sections:
  s 203 (15), s 204 (9), s 202 (5), s 200 (3), s 199A (2); Family Court
  Act (3); time-limited (13); paragraphs (8).
- **An order in the text** without a banner ("an order suppressing the name
  of …", "interim name suppression", "I suppress the identity of …"): the
  reading flags those too; 60 of 148 judgments are flagged in all.
- **Whom it covers is not reliably printed.** A banner may name the
  complainant, a witness, "the appellant", the parties, or paragraphs; a
  name in the caption can identify a complainant even when the order names
  only the complainant. So the rule is coarse on purpose: in a flagged
  judgment, no party's name is published except the Crown's (and the
  public prosecutors') and an initial the court printed; the row and its
  role stay (hard limit 16). A flag on one document of a citation binds its
  other documents. A later order is recorded with the lever
  (`registers/courts/suppress.py`), which outlives every rebuild; nothing
  lifts one but a person. The judgment of another court in the same
  proceeding is not linked, so an order made in the High Court binds the
  Court of Appeal's judgment only where that judgment carries the banner.

## The Waitangi Tribunal

The 205 Tribunal documents are reports and decisions on claims, not
judgments between parties: no neutral citation (1 cites one), no BETWEEN
/ AND, claims identified by Wai number and claimants, decimal-numbered
paragraphs (`4.2.1`) in 120, and image pages in the first six pages of 80.
They are held and recognised (`waitangi-tribunal-report`) and not read
into judgment rows; a reading of claims (Wai number, claimants, inquiry
district, date) is its own design (card).

## What the formats share with tribunals and OpenLaw

The Ministry of Justice's tribunals (item 5) print the same BETWEEN/AND
caption under their own names and decision numbers, and the parsed
case-law interface (item 1) gives party and judge tables already parsed;
the roles, the anonymisation rule and the suppression rule above apply to
both. A tribunal profile is written when its documents are held.
