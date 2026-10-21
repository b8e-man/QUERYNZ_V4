# The NZBN interface has a change search and watchlists, which plan 5.5 says it lacks
kind: finding
state: open
use-case: 5
session: companies-2
opened: 2026-10-21

Plan 5.5 says "the interface has no change feed, so this is the deepest it
allows". The interface's own page (`portal.api.business.govt.nz/api/nzbn`,
read 21 October 2026) describes two things that are one:

- a "change event search": "a search of the NZBN register to return a list
  of NZBNs that have been updated in a specified time period" (the old
  estate's client called it as `GET /entities?lastModifiedAfter=…`);
- watchlists, which "send you an email or an API push notification when
  changes occur".

It also keeps an `ETag` per entity that changes whenever the entity does,
so an unchanged entity answers 304 with no body (the gate returns no
headers yet: card `the-fetch-gate-returns-no-response-headers`).

Not built: the monitor asks one entity at a time, as the brief says. Whether
a nightly change search (a listing, not covered by the position as written)
should pick which watched entities to ask, or replace the watch schedule, is
a design question for Arthur (step 5.5 names Fable for the monitoring design).
The change search would cut the calls a watch costs to the entities that
changed.
