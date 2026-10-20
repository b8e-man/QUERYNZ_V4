# A section cannot put current roles before ended ones
kind: finding
state: open
use-case: 3 banking director history; also 8
session: banking-1
opened: 2026-10-20

Use case 3 reads a person's roles current first. The builder orders a
section by grade, then newest start first (`build._ordered`), and a
template cannot ask for another order; nor can a section nest the people
beside the person under the company they share, unless the company is in
the same section. Today it matters little (the file holds current roles,
and those that left it since July), and it will matter when past roles are
published (`the-companies-file-holds-no-past-directorships`). For the
report lane: an `order` setting per section (current first; by company).
