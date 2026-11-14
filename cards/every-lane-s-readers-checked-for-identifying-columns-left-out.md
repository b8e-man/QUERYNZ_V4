# Every lane's readers checked for identifying columns left out
kind: task
state: open
use-case: all
session: integrator-40ea495e
opened: 2026-11-15

Ruling 176 (Arthur, 15 November 2026): "we want to keep all identifying information except oia submitter requests
which we dont hold". Every lane keeps every identifying detail its source gives (names, contact people, addresses,
dates of birth, emails, phones, descriptions), verbatim, in its `_private` schema, with an address-shape flag where
ruling 102 asks for one.

Why a check: on 14 November the grants readers dropped Milestone's contact-person and applicant-description columns
on purpose (`never_read`), and the drop was shipped (12a6e29) before Arthur caught it; fixed in b54ee7f. Lanes built
before rulings 142 and 176 may do the same.

Next, lane by lane:
- grep each lane's readers, extract lists, model prompts and load for what is read and then dropped, or never read:
  columns used only to find an edge, fields skipped for privacy or suppression, a prompt told not to extract
  identifying details, a value stripped before landing, a row withheld;
- for each found: what the source prints, and how many rows it would add;
- keep it in the lane's `_private` schema, as grants_private.society_row_details does; a test that it is kept and
  never reaches a published column or view;
- the OIA requesters' details are the one exception (not held).

Owner: integrator; one lane a tranche, the lane's own tests and a real-data count each.
