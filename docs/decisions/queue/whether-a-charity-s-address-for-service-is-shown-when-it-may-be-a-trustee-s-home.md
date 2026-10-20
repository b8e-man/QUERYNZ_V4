# Whether a charity's address for service is shown when it may be a trustee's home
default: Withhold it where the charity is not a body corporate (a trust or an unincorporated society); show it for incorporated charities, as a company's registered office is shown
blocks: The charities lane's publish (pub.charities carries address_for_service); nothing else
recommendation: The default. Hard limit 15 says a person's home address is never shown; a small trust's address for service is often a trustee's home, and the register's own field cannot tell a home from an office. Both builds show it today on the capture's legal position (question 4: the register publishes it under ss 24 and 25), which is lawful; the limit is ours and stricter
raised: 2026-10-21 by the integrator (charities-a and charities-b both asked)

The capture's position page (`docs/legal/positions/charities-register.md`)
treats the address for service as the organisation's address. Both builds
of the reading carry it in their `charities` table. The Charities Register
publishes it; copying it is lawful. Whether it is shown is a hard-limit
question: a company's registered office is shown by rule, and a charity's
address for service is the same kind of field, but for an unincorporated
trust the only address is often where a trustee lives. The default keeps
the field in the private schema for those charities and shows it for the
rest; a ruling the other way is one line in the kept build's publish.sql.
