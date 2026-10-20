# A person page is keyed by the name as the register prints it
kind: finding
state: accepted
use-case: 1
session: comparison
opened: 2026-10-20
closed: 2026-10-20

The frozen site keyed a person page by the name in title case ("Aaron
Stallard"); the rebuilt site keys it by the name as the results print it
("Aaron STALLARD"). The slug is the same and the hash in the file name
differs, so 930 person pages sit at a different path on each side. The
comparison matches them by slug and compares their figures.

Which side is right: neither; it is a choice of key. It matters only when
the public site is switched (old URLs). Owner: site.

Accepted (site-2, 2026-10-20): settled in the template (`settled.person_page_key`): the name as the results print it, the register's own form; the
slug is shared and old paths are mapped once at the switch. Measured against the frozen 2026-10-20T0620, rebuilt in scratch: 930 differences, unchanged.
