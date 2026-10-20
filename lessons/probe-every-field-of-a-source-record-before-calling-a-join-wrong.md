Probe every field of a source record (title as well as text) before calling a join wrong: a Gazette deed-of-arrangement notice names its companies in its title only, and a probe of the text alone reported a correct join as a mis-join.
area: checkpoints, reading against source, Gazette, gazette_company_notices, subject reports
paid-for-by: 2026-10-21, legal-1 session, step 5.2 checkpoint

The legal checkpoint read WAIKATO ICE SUPPLIES LIMITED's deed of company
arrangement (notice 2019-ot4535, company 3) against the Gazette source
file, probing only the record's `text` for the company's name: absent. The
row looked joined to the wrong company. The record's `title` names all
three companies the lane read; the text names only the first. Probing each
field for the tokens (never printing the text) showed it in seconds. A
reading's join is wrong only once every field the reader could have used
has been probed.
