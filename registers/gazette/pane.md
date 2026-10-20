# Gazette notices, on the board

One pane per notice: its number (the Gazette's own, `2025-go7375`), section and family, the format the lane recognised,
its status (read, read with a part set aside, set aside, not read), its date and title, and its gazette.govt.nz address as
the citation. The notice text is never shown: bankruptcy, prohibition and independent-celebrant notices print home
addresses.

A celebrant row opens to its notice: the surname and given names, the organisation where the list prints one, the
list's own action (appointment, removal, publication, annual list) and statute, the period where stated, and how the
name was cut (`delimited`, `last word`, `glue`). An address is never shown; a row from an address list says only that
its address is held privately. Every row says "taken from the old estate's tables; original not held".

A prohibition row opens to its notice: the person's name and any alias in brackets, the action (the Registrar's
prohibition, a court order, a banning order, a substitution or a variation), the Act and section, the term or
"permanent", its start and end, and the notice that later revoked, replaced or varied it. The address the notice
prints (`Of:`) is never shown. Where a later notice revoked it, the person is not shown either: one notice was revoked
because it named the wrong person.

A liquidation row opens to its notice: the company as printed, its number where the notice prints one, who appointed
the liquidator (shareholders, board, court, creditors) and under which section, the date and time of the appointment
(or, for the Official Assignee's lists, the list's date, said so), and the liquidators the notice names, each with how
they were read (signed, or named in the operative sentence). No address, telephone or email is shown or held.

A company notice row opens to its notice: the company as printed, its number where the notice prints one, the kind
(removal, winding-up application, receivership, notice to creditors, administration, overseas company, restoration,
dissolution) and the notice's own action (an intention to remove, a restoration, an application to put into
liquidation, a receiver's appointment or ceasing to act, a meeting, a call to prove claims, a dividend, an overseas
company ceasing to carry on business in New Zealand or applying for removal from the overseas register, the
Registrar's intention to restore a company to the register, an incorporated society or charitable trust board
dissolved, its dissolution revoked, or its removal or restoration intended), the Act and section, the ground of a
removal, who gave notice, and for a winding-up application the plaintiff by name only, its court and reference. The
one date a notice turns on is shown with what it dates (`event_basis`: to be heard, objections by, appointed, ceased
to act, meeting, claims by, dividend, ceases, dissolved on: the day of the dissolution a revocation undoes); the
filing day and the publication day stand beside it; a notice that prints no such day leaves it blank and is dated by
its publication day alone (48,393 rows, 46,282 of them removals); a day whose kind the reader could not name is shown
as a bare "event on" (72 rows, administrations and notices to creditors). The row says which Companies Office entity
it was joined to and how (by number and name, or by the one name alive on the notice's date), or "not held"; a
society's or trust board's printed number is looked up among the societies and trust boards, never the companies. The
receivers and administrators the notice names are listed under it. A plaintiff's address for service is never read,
held or shown, and neither is the applicant a restoration names, nor the applicant's address: a restoration row is the
company alone. A restoration given under `ds` is a removal row whose action is "restoration" (5,155 rows); one under
`ot` is the kind "restoration".

Four more kinds come from the Registrar's other `ot` notices (gazette-5, measured on every notice 20 October 2026). A
rectification row (2,877 rows from 486 of 503 notices; 99.7% joined, 85.1% of printed numbers agreeing by name) is a
company the Registrar intends to correct the register for: its number, what is corrected as words from a fixed list in
`ground` (director 700, shareholding 532, liquidation 513, receivership, company name, annual return, address,
constitution, …, "other" 227), the people the correction names in `people_named` and an applicant who is a person in
`party`, by initials and surname only (867 rows name people; 467 applicants are people), and the day objections close.
The correction's sentence is never held or shown, so neither is a given name or an address it prints. An amalgamation
row (1,000 rows from 369 notices, 73.1% joined; the unjoined mostly 2000-2009 companies under names the register no
longer holds) is each company a proposal names, `role` saying which continues as the amalgamated company (163) and which
amalgamate into it; a proposal that forms a new company names none to continue. A transfer-out row (168 from 167
notices, 95.8% joined) is a company leaving the register to be incorporated elsewhere, the place in `ground` (the
British Virgin Islands 21, Australia, Delaware, …) and the day after which it applies. A deed of company arrangement row
(39 from 21 notices, 89.7% joined) is the company, the action (executed, varied, terminated) and its day; the deed
administrators are practitioner rows (20). 198 `ot` notices stay unread: extensions of time to register a charge,
court applications and industrial and provident society notices.

A practitioner row is a receiver or an administrator as the notice signs them: the name, the role as printed (Receiver
and Manager, Joint Administrators, Former Receiver, …), how the name was read (`full`: also named in full in the
notice's text above the signature; `surname`: only the surname there; `no`: only at the signature), and the companies
the same notice names, listed under it. No address, telephone or email is read or shown.

A bankruptcy row opens to its notice: the person's surname, given names and any alias, the occupation where the notice
prints one, the kind (an adjudication, a no-asset procedure, an annulment, a discharge, a meeting, other), the list or
single notice it came from, the day and time it happened where printed, the court and the Act. The address and the
"formerly of" address the notice prints are never shown: they are held only in `gazette_private`. A person a later
annulment names is withheld, the name and the occupation alike, on the annulment's own row and on every earlier row
naming them as bankrupt; the row stays, saying which annulment withheld it. A bankruptcy row is not joined to a person
anywhere else: two people of one name are two rows.

An appointment row opens to its notice: the appointee as printed (with any honorific), the body and the role, the Act
and section, who appointed (the Governor-General, a Minister, the Sovereign, a Chief Justice or Chief Judge), the
term's start and end where printed, and whether the notice is a corrigendum. Where an appointee lives (", of <town>")
is read past and never kept. A name on an appointment is not joined to a Member of Parliament or anyone else; the
check compares surnames only, as a measure of the reader.

A possession row (`pub.gazette_possessions`, one per notice under `gn` of a mortgagee's entry into possession, 3,002
notices from 2000 to 2026) opens to its notice: the lender by name as printed, with its company number where printed and
the companies register's entity; the borrower by name only where it is a company; whether the notice is about land
(1,191) or goods (1,777, mostly vehicles and plant; 34 do not say); whether the lender entered into possession, received
the property's income (8) or both (20); the Act and section; and the day of entry, saying where it came from: "with
effect from" (1,751), the sentence that enters (1,145), or the notice's first "on" or "as from" day (55); 51 print no day
the reader can find. Measured on every notice on 20 October 2026: 2,899 name their lender (2,827 shown by name; 35
lenders are people and 37 names may run on from the borrowers', so neither is shown); 2,449 of the 2,864 company lenders
are joined to the register, the rest mostly custodian companies renamed or removed since and building societies, which
the companies register does not hold; 339 borrowers are companies (330 shown, 306 joined), 136 are people and 2,441
notices name no borrower. The property's address, the goods' description and registration numbers, and every person's
name are never shown: they are held only in `gazette_private`, and a row says only that a description is held. A title
that names the property is shown cut before it. A lender printed without its "Limited" ("GE Custodians") is joined with
it added, and says so.
