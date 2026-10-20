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
(removal, winding-up application, receivership, notice to creditors, administration, overseas company, restoration)
and the notice's own action (an intention to remove, a restoration, an application to put into liquidation, a
receiver's appointment or ceasing to act, a meeting, a call to prove claims, a dividend, an overseas company ceasing
to carry on business in New Zealand or applying for removal from the overseas register, the Registrar's intention to
restore a company to the register), the Act and section, the ground of a removal, who gave notice, and for a
winding-up application the plaintiff by name only, its court and reference. The one date a notice turns on is shown
with what it dates (`event_basis`: to be heard, objections by, appointed, ceased to act, meeting, claims by, dividend,
ceases); the filing day and the publication day stand beside it; a notice that prints no such day leaves it blank and
is dated by its publication day alone (48,393 rows, 46,282 of them removals); a day whose kind the reader could not
name is shown as a bare "event on" (72 rows, administrations and notices to creditors). The row says which Companies
Office entity it was joined to and how (by number and name, or by the one name alive on the notice's date), or "not
held". The receivers and administrators the notice names are listed under it. A plaintiff's address for service is
never read, held or shown, and neither is the applicant a restoration names, nor the applicant's address: a
restoration row is the company alone. A restoration given under `ds` is a removal row whose action is "restoration"
(5,155 rows); one under `ot` is the kind "restoration".

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
