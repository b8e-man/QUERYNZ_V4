# The Treaty settlement commitments are not held: Te Haeata is behind a login
kind: finding
state: open
use-case: 14
session: settlements-1
opened: 2026-10-22

Te Haeata (tehaeata.govt.nz, Te Puni Kōkiri) answers every records address
(`/settlements`, `/commitments`, `/resources`) with its login page (sha256
`ca096c67…`, 22 October 2026). Hard limit 6: a failed read, no account made.
Te Tari Whakatau's settlement pages are open but its terms bar data
collection, so they are not captured either. So template 3 has no
commitments: which agency owes what to which governance entity. What it does
have: the settlement Act or deed each post-settlement governance entity's
Te Kāhui Māngai entry names (`pub.iwi_directory_settlements`).

The way in is Arthur's: queue `whether-to-ask-for-the-settlement-commitments`.
The lane `registers/settlement_commitments` watches the wall weekly and goes
red the day it falls. Fate at the checkpoint: a line on template 3's
known-limits page ("commitments not held: behind a login") unless a letter
opens them.
