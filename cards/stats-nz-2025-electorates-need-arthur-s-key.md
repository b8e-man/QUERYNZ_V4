# Stats NZ's 2025 electorates need a key that is Arthur's to place
kind: finding
state: closed
use-case: 1
session: house
opened: 2026-10-20
closed: 2026-10-21

The 2026 election is fought on the 2025 boundaries: 71 electorates in the
Commission's workbook, ten of them names the 2020 set does not have (East
Cape, Glendene, Henderson, Kapiti, Kenepuru, Mt Maunganui, Waitākere,
Wellington Bays, Wellington North, Ōtāhuhu). Stats NZ publishes them as
layers 122741 (general) and 122742 (Māori) on its keyed service; the old
estate holds only the 2020 set (`var/staging/boundaries/`, fetched 7
September 2026 under its ruling 234). So `pub.electorates` publishes the
71 for 2026 with `join_basis` "boundary set not held", and none is joined
to a 2020 name even where the name is unchanged, because the boundaries
moved. The unlock: Arthur places a Stats NZ service key in the credential
folder (a credential, so his to place); a capture through track E's fetch
gate then takes the two layers once, and the lane joins by name and code.
Nothing is fetched until then.

Closed by ruling 74 (21 October): "not wanted". No Stats NZ key is placed; `pub.electorates` keeps the 71 electorates for 2026 with `join_basis` "boundary set not held".
