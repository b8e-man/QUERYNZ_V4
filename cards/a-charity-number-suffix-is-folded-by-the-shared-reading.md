# keys.numbers.charity_number drops a register number's suffix
kind: finding
state: open
use-case: -
session: charities-b
opened: 2026-10-21

The Charities Register gives ten organisations a number with a suffix,
`CC12345-1` in shape (feed of 20 October 2026). `keys.numbers.charity_number`
matches `CC\s*0*(\d{1,6})\b` and returns `CC12345` for it: another charity's
number, or one nobody holds. None of the ten bases is held today, so nothing
collides yet, but a link on charity number would join or miss on a number the
register never gave. `registers/charities_b` keys on the number as filed and
does not use the shared reading for it. Proposed fix, in `keys/`: keep a
`-<digits>` suffix (and test the ten shapes); a fix session on `keys`.
