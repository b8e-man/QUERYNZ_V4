# The charities capture lands no answer for the register's count of registered charities
kind: finding
state: open
use-case: -
session: charities-b
opened: 2026-10-21

The capture stores the feed's own count of each set at the start of each pass
(`capture_passes.stated`), but the count of registered charities that the
lane's outside check needs is asked only by `capture.py --measure`, which
fetches it live and lands nothing. So a build checking itself against "the
register's count on the capture day" has only the figure written in
`docs/status/charities.md` (29,265 at about 07:30 NZDT on 20 October), and
`registers/charities_b/check.py` carries it as a constant. Proposed fix, in
`registers/charities`: on each full pass of Organisations, ask
`$inlinecount` for `RegistrationStatus eq 'Registered'` once through the gate,
land the answer by hash and store it on the pass, so the check reads a
document, not a note. One request a month.
