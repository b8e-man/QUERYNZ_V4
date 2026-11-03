# Rulings 2 and 3: a shared email or phone, and a judgment's address against a company's office (4 November 2026)

Arthur said yes to both, research first, with the courts' registries and the law firms set apart. Measurement only:
no rule is built. Counts only; the tables are in `links/measurements.md` §15. The source is
`courts_private.identifiers` as the 04:40 load left it (6,531 emails, phones, addresses and PO Boxes on 2,230 court
documents), read privately in a read-only transaction; the text around each detail was read on its own page only.

## What the details are

- **Most are offices.** Of 304 phones, 232 sit under a registry heading, an agency's words or a law firm's, or are
  toll-free; 72 are not. Of 496 emails, 194 are a court's, an agency's or a law firm's.
- **A person's own contact barely recurs.** Personal webmail: 48 addresses, 2 printed in two documents. Phones with
  no office signal: 72, 8 in two documents.
- **Most addresses are nobody's office.** Of 3,301 street addresses, 1,833 match no registered office and sit under
  no court or law-firm heading (likely a person's); 334 match an office's street and town, 653 its street only.

## What a rule would yield

- **Ruling 2.** The emails and phones not an office's, printed in two or more documents, join 495 document pairs by
  email and 11 by phone. In 167 (email) and 5 (phone) of them a person's name is in both documents: the value
  corroborates a name link. In 328 and 6 the names differ: one contact, two names, a near link at most. Joining every
  name beside the value would make 41,417 name pairs, so the rule needs the value tied to one person (the model
  item's `person`, still empty).
- **Ruling 3.** 170 addresses match one company's office by street and town, in 167 documents; in 5 the judgment
  also names that company. 135 match an office of over five companies (a busy office) and are no evidence.

## The rules they would need

1. **`shared-contact@1` (ruling 2).** Same email or phone in two documents, not an office's, tied to the person;
   confirmed where the names agree, near where they differ; a company's email joins the company. Read privately or
   by a keyed hash, since the links lane reads `pub.*` only.
2. **`judgment-address-office@1` (ruling 3).** A judgment's street address, not a court's or law firm's, matched
   by street and town to exactly one company's registered office: near alone; confirmed only with the company's name
   among the judgment's parties. Never a busy office; never shown.

Next, by the links method (ruling 106): twenty pairs of each for Arthur, then his ruling, then a versioned rule.
