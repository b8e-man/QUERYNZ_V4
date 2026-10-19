To look at a page that holds people's addresses, count its field labels and print only those: stripping tags, masking digits or printing "tags only" still prints the values.
area: any lane reading a register page with contact lines (registers/party_finance promoters, registers/parties secretaries, candidate and officer registers); hard limits 11 and 15
paid-for-by: 2026-10-20, party-finance session, step 4.1

Inspecting the Commission's register of promoters to learn its shape, three
"safe" prints each leaked: a text dump around the first block with digits
masked still showed one promoter's street and suburb (the promoter was a
person, so the address may be a home); a regex meant to keep only tags,
`>[^<]+<` → `><`, left mailto attributes and a union's localities in
place. What worked: a counter of the bold labels per block
(`Email 32, Address 28, Authorised representative 28 …`), the block count,
and for a flagged value only its length, its booleans and a letter mask
(`xxx xxxxxx xxxxxx`). That was enough to write the reader and its tests,
which use made-up blocks.

Write the inspection as counts from the start; the reader that follows
sends every unrecognised label to the private schema, so the shape is all
the session needs to see.
