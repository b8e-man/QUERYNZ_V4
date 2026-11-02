# The building practitioners register's sub-tables and its lapsed practitioners are not read
kind: finding
state: open
use-case: 6 insurance, 7 construction and phoenix, 12 property developer; step 5.3
session: building-practitioners-register
opened: 2026-11-02

Two parts of the register the copy of 2 November 2026 (ruling 132) does not reach. (a) A practitioner's page loads
five sub-tables (companies, qualifications, licence classes with their dates and status, suspension history,
disciplinary history) by a POST to `/_services/entity-subgrid-data.json` with an anti-forgery token; the fetch gate
makes GETs only, so none is read, and `licence_classes` carries the class and area from the searches with no dates.
(b) A class or area search lists current holders only ("include not currently licensed" changed nothing for
Foundations), so a practitioner with no current class is not reached and `status` is `licensed` for every row read
from a current pass. Reaching (a) needs a POST in `support/fetchgate` (a support change); (b) needs a search by name
or town with the box ticked, which is not a whole-register enumeration. Neither blocks the lane.
