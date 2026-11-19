# The courts and ERA pages the old news copy holds are missing from the courts collection
kind: finding
state: open
use-case: all
session: integrator-40ea495e
opened: 2026-11-20

The provider says it holds these sites in its courts collection, not estate-news (reply out-9ce171a4b300662e to
estate-news-old-only-sites@2026-11-18). On Arthur's ruling of 20 November ("count as new copy but check it is the
same as the copy it is replaceing") a site moves only when the new estate holds every address the old copy holds
for it (registers/news/load.py `ELSEWHERE`). On 20 November:

- courtsofnz.govt.nz: 152 of the old copy's 154 addresses held, 2 missing;
- determinations.era.govt.nz: 3 of 53 held, 50 missing;
- environmentcourt.govt.nz: 1 of 2 held, 1 missing.

`news.sites` names each as "held elsewhere, gap". The missing addresses: the old copy's rows for the host in
news_private.articles whose url_key is in none of load.ELSEWHERE_SOURCES.

Next: once the current news work is cleared (Arthur, 20 November: "we will ask once we have cleared the deck of the
current work"), send the provider the missing addresses and ask whether its courts collection holds them under
another address or does not hold them; if not, ask it to collect them.
