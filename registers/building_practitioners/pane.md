# Building practitioners, on the board

- **Board decisions** (`pub.building_practitioner_decisions`, kind decision, key `key`): title `citation` and
  `decision_kind`; `name` and `lbp_number` ("name withheld by the Board" where `suppressed`), `decided_on`, `region`
  (the area the list publishes, often none), `licence_classes`, `penalties`, `grounds`, `upheld`; `decision_url` and
  `pdf_url` open the Board's own page and decision (empty where suppressed: both carry the name). A decision older than
  three years is not on the view (the register's own window, the queue's default). The pane never says a practitioner
  "has no decisions": the list is the Board's published decisions, and a missing one is "none found".
- **Licensed building practitioners** (`pub.building_practitioners`): HELD. The pane says "not held: the register may
  be searched only for the purposes the Building Act 2004 (s 299) names" until Arthur's decision.
- **Citation** on every row: the list page's sha256 (`document`), `page`, `place` (`complaint=CB26816`), `reader`,
  `profile` and `profile_version`.

No address of any kind; a decision's summary is not shown (it can name a property or a complainant).
