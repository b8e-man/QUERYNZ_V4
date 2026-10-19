Mask a Gazette sample by vocabulary, not by case: masking capitals and digits still printed an email's local part (a person's given name) and lowercase web addresses; show only lowercase words common to thousands of notices of that type, and mask everything else.
area: Gazette notices, liquidators, insolvency, reading documents, masking samples, hard limit 11
paid-for-by: 2026-10-20, gazette session 2, step 4.1

Looking at liquidator notices with the celebrant lesson's mask (capitals
to X, digits to 9) printed two practitioners' business email addresses
and, where the capture had split an address across lines, one given name
on its own. The contact lines at the foot of every insolvency
notice are lowercase: emails, web addresses, "c/o" lines. What held: a
mask that keeps a lowercase word only if it appears in at least 2,000
notices of the type (the template's own words), replaces anything with
`@`, `www.` or a domain ending by `<web>`, and masks every other word.
Two more traps from the same notices: a signature printed in capitals
(`ANN EXAMPLE, Liquidator`) looks like a run of post-nominals to a test
for initialisms, so a post-nominal needs its stops or a fixed list; and
a stop inside a signature is an initial's (`J. M. Example`), so cutting
the names at ". " leaves only the surname.
