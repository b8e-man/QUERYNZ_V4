# The shape's not-held list has no key for the registers a health regulator keeps
kind: finding
state: open
use-case: 11 healthcare operator governance
session: healthcare-1
opened: 2026-10-21

Template 11 must name, each with its key, what it cannot see: the retirement
villages file and its statutory supervisors, the Health and Disability
Commissioner's decisions, certification audits, the Ministry of Health's
provider registers and the Aged Care Commissioner. `catalogue.NOT_HELD`
(report-3) has `courts` and nothing for these five, and a section naming a
key the catalogue lacks is refused when loaded. So the template names them
in its last section's text and in five blocked flags, and the memo's
not-held list does not carry them.

For the report lane, five entries for `catalogue.NOT_HELD`:

- `retirement_villages`: "The retirement villages file: each village's operator and statutory supervisor"
- `hdc`: "Health and Disability Commissioner decisions"
- `certification`: "Certification audits of rest homes and hospitals"
- `health_providers`: "The Ministry of Health's provider registers"
- `aged_care_commissioner`: "The Aged Care Commissioner's reports"

Then template 11 names them in `not_held` on its not-held section (and
`retirement_villages` on its standing section), a fix in its folder.
