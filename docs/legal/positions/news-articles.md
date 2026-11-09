# News articles, held as a corpus and searched (position, hard limit 9)

DRAFT for the lawyer's review (hard limit 9). Nothing in it is settled law
where it says "unsettled"; a lawyer reviews this page before anything is
sold and before any surface outside the local network shows an article.

Class: articles published by New Zealand news outlets (and others reporting
on New Zealand), as text with a headline, date, publisher, byline and the
publisher's address for the article. They reach the estate as corpora: the
old estate's news tables copied verbatim into the lane `news` (step 9.2),
and corpora handed over by the website-crawl provider or read from a keyed
API (ruling 156). The estate crawls no news host itself, so this page names
no host for the fetch gate: a keyed news API, if one is read, gets its own
page with its `hosts:` line. Use: an index on the boxes, searched with the
names and things in one report's register records (step 9.3); the report
shows hits, never the article (step 9.4). Papers Past is a separate class
(`papers-past.md`, hard limit 17). Written 10 November 2026 by stream D of
the step 9 integrator session, from the plan and the statute, not from any
past note on the news sources (ruling 152).

1. **Is the page open?** Not answerable for the class as a whole; it is
   answered per corpus, from each article's capture record. An article
   captured with no login, key, challenge or CAPTCHA passes hard limit 6;
   one behind a subscription wall read with a login that is not ours does
   not. The provider's records carry their capture provenance (as-received
   hash, fetch time, HTTP status). For each table of the old estate's copy,
   the copy records what its rows say about how they were fetched; where a
   table says nothing, the question stays open for that table and the
   report shows none of it until a person rules. A publisher's direct
   request to stop is honoured (hard limit 7).
2. **Is storing it lawful copying?** Unsettled; the main question for the
   lawyer. An article is a literary work (Copyright Act 1994, s 14), and
   "copying" includes storing a work in any material form, digital included
   (s 2), so holding an article whole is a restricted act (ss 16 and 29)
   unless an exception covers it. Facts in an article are not protected;
   its words are.
   - **No text-and-data-mining exception.** New Zealand has none. The
     Ministry of Business, Innovation and Employment's review of the Act
     raised one; none had been enacted at this writing (lawyer to confirm).
   - **Fair dealing for research or private study (s 43).** The nearest
     ground for holding and searching a corpus. The court weighs the
     purpose, the work's nature, whether a copy could be bought in a
     reasonable time at an ordinary price, the effect on the work's market,
     and the amount taken (s 43(3)). New Zealand's s 43 does not exclude
     commercial research in its words, but no case settles whether a whole
     corpus held for a product meant for sale is "research"; copying whole
     works weighs against it. Unsettled.
   - **Fair dealing for criticism, review and news reporting (s 42).**
     Requires the purpose and, for criticism or review, sufficient
     acknowledgement; the news reporting ground does not extend to
     photographs. A report that lists articles is not obviously criticism,
     review or reporting of current events. Weak ground for the corpus;
     better for a short quoted excerpt with its source named.
   - **Transient copies (s 43A)** cover incidental copies in a technical
     process, not a stored corpus.
   - **What is shown.** Copyright is infringed by copying a substantial
     part, judged by quality as much as quantity (s 29(2)). A headline may
     be too short to be a work in itself, which New Zealand courts have not
     settled. A short excerpt around the searched word, with the publisher
     and date named and a link to the publisher's page, is the narrowest
     showing; showing the article to a reader is communication to the
     public (s 33) and is never done. There is no separate database right.
   - **Moral rights.** An author's right to be identified (s 94) applies
     where asserted; the report names the publisher and the byline beside
     every excerpt.
   - Holding whole articles for search is kept, the class's risk named
     here (ruling 142: every source whole); the safer alternatives for the
     lawyer to weigh are a licence from the publishers, or holding only an
     index and the publisher's address.
3. **What terms did we accept?** None by the estate: it fetches no news
   page and clicks through nothing. Publishers' website terms commonly bar
   automated copying and commercial reuse; terms bind whoever accepted them,
   and whether terms shown but never clicked bind a reader at all is
   unsettled in New Zealand. The provider's terms with the publishers, and
   any keyed API's licence, are landed beside each corpus on arrival and go
   to the lawyer with this page; until a corpus's terms are on file, the
   report shows nothing from it.
4. **What does privacy law, or a statute, limit?**
   - **Privacy Act 2020.** Articles name people and print personal
     information. A published article is a "publicly available
     publication" (s 7), which lets collection, use and disclosure proceed
     only where, in the circumstances, it is not unfair or unreasonable
     (IPPs 2, 10 and 11). The news-entity exemption (s 8) covers the
     publishers' news activities, not the estate. IPP 8 requires reasonable
     steps to check accuracy before use: an old or corrected article is
     shown with its date, and a name match is never stated as the person
     (step 9.4). IPPs 5, 6, 7 and 9 (security, access, correction,
     retention) apply to what the estate holds.
   - **Suppression.** A court's suppression order (Criminal Procedure Act
     2011 ss 200 to 211; Family Court Act 1980 ss 11B to 11D; Oranga
     Tamariki Act 1989 s 438) can postdate an article, and some articles
     breach one. Publishing in breach is an offence. Every name the estate
     holds as suppressed is suppressed in every excerpt (hard limit 16); a
     suppressed name is never a search term. The Administration of Justice
     (Reform of Contempt of Court) Act 2019 limits publishing what risks a
     fair trial: an article about a live case is shown only as a hit, never
     reworded into a claim.
   - **Defamation** (Defamation Act 1992): tying a person to an article
     wrongly can defame. The rule of step 9.4 is the guard: a hit is "an
     article that mentions this name"; it is a connection only when the
     article also names something from the subject's own records.
   - **Hard limit 15.** Articles can print a home address. Every excerpt is
     tested by the address shape (`products/report/rules.address_shaped`)
     and a flagged excerpt is not shown.
   - **Hard limit 14.** A connection found in an article is made in the
     report on request, not stored as a link, and goes on no public surface
     without Arthur's word.
   - **Hard limit 17.** Papers Past items are searched and shown as results;
     nothing built here mines them.

**What the report may show:** the headline, the publisher, the byline, the
date, a link to the publisher's own page, and a short excerpt around the
searched word (at most 320 characters, at most two excerpts an article),
with the grade and its evidence. **What it may not show:** the article
whole, its photographs, its text past the excerpts, any export of the text,
or an excerpt carrying a suppressed name or an address-shaped span.

**Crawl delay:** none applies; the estate fetches no news page. **Floor:**
the provider's crawls are the provider's; any keyed API is read under its
own page's floor.
