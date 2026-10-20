# A lender's entry into possession of land or goods, printed in the Gazette, is unread
kind: finding
state: closed
use-case: 3 banking director history; 4 agriculture counterparty
session: gazette-4
opened: 2026-10-20
closed: 2026-10-20

Section gn holds 2,953 notices titled a notice of entry into possession
(Property Law Act 2007 s 119/121): a mortgagee, usually a bank or a
finance company, says it has taken possession of mortgaged land (about
1,200) or mortgaged goods (1,739, mostly vehicles and plant). A counterparty
whose lender has taken its land or stock is what the banking and
agriculture templates look for, and neither can see it: the lane types the
notices and does not read them.

Why it was not read in gazette-4: the property is printed by street address
and is often a home, and the mortgagor (the borrower) is sometimes named,
often a person. A reader needs its own profile and the gazette_private
treatment the bankruptcies have: the mortgagee and the mortgagor by name,
the property address and the goods' registration number in the private
schema only, the day of entry. Next gazette session, its own tranche.

Closed 2026-10-20 by gazette-5: `registers/gazette/possessions.py` reads
every `gn` notice of a mortgagee's entry into possession or receipt of
income under the proposed profile `gazette-mortgagee-possession` into
`pub.gazette_possessions`: 3,002 notices, 2,899 naming the lender, 2,951
the day of entry, 2,449 of 2,864 company lenders joined to the companies
register (85.5%), 339 company borrowers (306 joined). The property, the
goods' description and registration numbers, and every person's name are
in `gazette_private.possession_details` only; a title that names the
property is published cut before it. Check floors 95% named, 95% day,
82% joined; a published title with a number, or a person shown as a
borrower, fails. Pane paragraph written.
