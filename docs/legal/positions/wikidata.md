# Wikidata's query service, for Papers Past's newspaper titles (position, hard limit 9)

hosts: query.wikidata.org

Class: Wikidata, the Wikimedia Foundation's open knowledge base, read
through its public SPARQL query service. Used for catalogue facts about
newspapers only: the item that carries a Papers Past title code, its place
of publication (P291) and the region that place is in (P131). Lane:
`registers/papers_past`. Written 5 November 2026 by the integrator's board
fork, on Arthur's word (Papers Past's own list challenged the estate, and
DigitalNZ carries no place: `papers-past.md`).

1. **Is the page open?** Yes. The service answers anonymous queries with no
   key and no login. A 403, 429, 5xx or a challenge is a failed read: the
   run stops, the gate holds the host, nothing is got around (hard limit 6).
2. **Is storing it lawful copying?** Wikidata's structured data is
   published under CC0 (a public-domain dedication). Each answer is stored
   once, by hash, as the document behind every row read from it, and each
   row cites its item's id (Q-number).
3. **What terms did we accept?** None were clicked through. The Wikimedia
   terms of use and the query service's User-Agent policy apply: the
   estate's one User-Agent names it and a contact. They go to the lawyer
   with this page.
4. **What does privacy law, or the statute, limit?** Only newspapers and
   places are asked for. No person is queried or stored. Papers Past is
   searched, never mined (hard limit 17): nothing read here feeds the links.

Floor: the gate's polite floor, one query at a time, a handful of queries,
asked again only on a person's word.

Asked 5 November 2026, two queries: the property is P8108 ("Papers Past
ID"), on 169 items; its value is Papers Past's title slug
(`newspapers/otago-daily-times`), not the paper code the archive's catalogue
keys by (`ODT`), so no item meets a catalogue paper without matching names,
which is not done. 30 of the 169 carry a place of publication (P291) and
none reached a region through P131 to a region of New Zealand. Too thin: no
papers table was built, and the two answers were not kept.
