# Amalgamations and the Registrar's rectifications under section ot are unread
kind: finding
state: closed
use-case: 3 banking director history; 2 legal counterparty and conflict check
session: gazette-4
opened: 2026-10-20
closed: 2026-10-20

gazette-4 read the restorations under ot (868 of 888). Of the 1,258 ot
notices still unread, by their opening words: about 487 are the
Registrar's notices of intention to rectify the register ("I intend to
rectify the New Zealand Register of Companies …"), naming companies and
often the director or shareholder whose record is corrected; about 250 are
amalgamation proposals (the amalgamating companies and the one that
continues); about 70 transfer a company's registration out of New Zealand;
19 a deed of company arrangement. A counterparty that amalgamated, or
whose officers the Registrar corrected, is what a banking or legal check
wants to see. Each is a list of companies the restoration reader's cut
nearly fits; a rectification names a person by initials and surname and
must keep any address out. Next gazette session, one profile each.

Closed 2026-10-20 by gazette-5: `registers/gazette/companyacts.py` reads
four kinds into `pub.gazette_company_notices`, each under its own proposed
profile, measured on every notice. Rectifications (`gazette-register-
rectification`): 486 of 503 notices, 2,877 company rows, 99.7% joined and
85.1% agreeing by name; what is corrected as fixed words, the people and a
person applicant by initials and surname only (a test enforces it; no
sentence, given name or address is held). Amalgamations: 369 notices,
1,000 rows, 73.1% joined, the continuing company marked on 163.
Transfers out: 167 notices, 95.8% joined, the place it goes. Deeds of
company arrangement: 21 notices, 89.7% joined. Two new columns, `role`
and `people_named`, last in the view. Check floors 97/80, 70, 92, 85%.
198 ot notices stay unread (charges, court applications, industrial and
provident societies).
