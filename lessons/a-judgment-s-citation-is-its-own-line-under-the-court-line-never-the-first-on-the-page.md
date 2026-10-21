A judgment's neutral citation is its own line under the court line and the case numbers, never the first citation printed: a suppression banner above the court line cites other judgments; a caption's party count follows the role's number.
area: courts, legal documents, captions, suppression, reading by layout
paid-for-by: 2026-10-21, courts-1

The old estate's caption parser took the first `[year] NZxx n` in the first
20,000 characters; 7 of its 118 judgments carry another case's citation,
taken from a banner ("SEE [2021] NZHC 1426"). The file name carries the
citation too (`2026-NZSC-88.pdf`): all 148 held agree with the line under
the court line, so a disagreement is a note, not a guess. The same parser
split every caption line into a party: a singular role ("Appellant") is one
party however many lines it wraps over, a plural role lists several, a
block can hold several name/role pairs, and a list wraps mid-name. Measure
captions with names masked (capitals to X) so nothing suppressed is printed
into the session while the grammar is built.
