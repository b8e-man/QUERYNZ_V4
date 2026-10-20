Where a notice's sentences can name people and addresses (the Registrar's rectifications), keep only words from a fixed list and the people as initials and surname, never the sentence; and match a list's closing "Dated" case-sensitively, because "dated 3 October" sits inside the rows.
area: Gazette notices, Registrar of Companies, rectifications, people's names, hard limits 11 and 15, reading documents
paid-for-by: 2026-10-20, gazette session 5, step 5.3

Each rectification row says in prose what is corrected ("Remove the
particulars of director dated … that <full name> was appointed …; the
effect being <full name> remains the sole shareholder"), and the prose can
print an address. Holding a summary of the sentence would hold the names
and the address with it, so the reader keeps what is corrected as words
from a fixed list (director, shareholding, …) and each person only where a
set phrase frames them, reduced to initials and surname and dropped if it
does not reduce to that form; a test asserts no given name or address
word survives. The end marker for the list was `\bDated\b` under `re.I`,
which stopped the first row at "dated 3 October" and lost every row after
it; a unit test with the real phrasing caught it, the full measure did not.
The first measure joined 99.3% by number and agreed by name on 33%: the
capture glued each name's first word to the stop before it
("Register.CEMENT"), the agreement-share lesson's case again.
