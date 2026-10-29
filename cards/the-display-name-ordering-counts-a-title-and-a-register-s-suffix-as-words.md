# The display name ordering counts a title and a register's suffix as words
kind: finding
state: open
use-case: board (4.9), dossier (ruling 110), scan, report, site
session: links-4
opened: 2026-10-30

Ruling 123 names the display name "the fullest filed name, then the
earliest row", and ruling 105's decision 1 (the board's `people.fullest`)
reads fullest as the most words, then the most letters. `pub.entities` is
built on that ordering. Sampled on live over five ministers' groups, it
chooses "Brown, Simeon (4)" (three words, the House's seat-count suffix)
over "Simeon Brown" and "BROWN, Simeon"; "Bishop, Chris (4)" and "Upston,
Louise (4)" likewise; and "Hon" counts as a word, so "Potaka, Hon Tama"
would beat "Tama Potaka" where no fuller form exists. The name shown is a
register's filing, never wrong, but a reader sees a suffix the register
uses to tell members apart.

Built as ruled, in one place every reader shares; the fix is one line in
`build.build_entities` and `pane.md` if Arthur rules that a title
(`rows.MEMBER_TITLES`) and a bracketed suffix are folded before the words
are counted. Not worked. Owner: links.
