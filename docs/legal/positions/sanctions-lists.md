# Sanctions lists New Zealand law applies (draft position, ruling 61)

hosts: mfat.govt.nz, un.org, unsolprodfiles.blob.core.windows.net, police.govt.nz, legislation.govt.nz

Class: three published lists, each as its publisher issues it. MFAT's Russia
Sanctions Register (Russia Sanctions Act 2022); the UN Security Council
Consolidated List (given effect under the United Nations Act 1946); the
Police list of designated terrorist entities (Terrorism Suppression Act
2002). Lane: `registers/sanctions`. `unsolprodfiles.blob.core.windows.net`
is named for one document only: `scsanctions.un.org`'s XML redirects to a
signed copy there. `legislation.govt.nz` is named for statute text only.
Draft, held in the lane's folder; the integrator moves it to
`docs/legal/positions/`. Read 21 October 2026 by sanctions-1; the pages
cited are held by sha256 in the session's scratch folder and land with each
list's first authorised run.

**Finding: each list's terms bar the capture as briefed. All three are held**
until the line `authorised: <list> <date> <how>` is added below, by Arthur's
decision (queue items, no default). MFAT's register alone may come in now,
downloaded in a browser by a person, because its terms bar the robot and not
the copy.

1. **Is the page open?** MFAT: the register page answered 200; the
   workbook sits behind Incapsula (a bot wall). The one public crawler of it
   gets past that with a rented browser; we never do (hard limit 6), and our
   script has not asked for the workbook. UN: `scsanctions.un.org` answered
   200 with the XML; `main.un.org`, the list's HTML page, answered 202 with
   an empty body (a challenge), so it is not read. Police: every page and
   the workbook answered 200; its robots file asks a 10 s crawl delay, as
   does `www.un.org`'s; MFAT's states none.
2. **Is storing it lawful copying?** MFAT: Crown copyright, CC BY 4.0
   (`/en/copyright`, `20366d60…`): copy, distribute and adapt with
   attribution. UN: the terms of use (`c80c3472…`) grant download and copy
   "for the User's personal, non-commercial use, without any right to
   resell or redistribute them or to compile or create derivative works
   therefrom". Police: "You may save to disk and reprint ... for
   non-commercial private purposes only"; any other purpose "requires
   permission" (`fecda1a4…`). The designations themselves are law (the
   Russia Sanctions Regulations 2022's schedules; the Gazette notices of designations under the
   Terrorism Suppression Act), and Acts, regulations and Gazette
   notices of designation carry no copyright (Copyright Act 1994, s 27(1));
   the lawyer is asked whether the publishers' compilations can bind what
   the law itself publishes.
3. **What terms did we accept?** MFAT's terms of use (`a923c604…`): "You
   must not access or attempt to access our websites or online services
   through automated tools (including the use of scripts, web-crawlers,
   robots or screen-scrapers)". This session's script read four MFAT pages
   (the sanctions page, the register page, the copyright and terms pages)
   before the terms were read; no more is asked by script. UN: the terms
   above, accepted by use. Police: the copyright statement above.
4. **What does privacy law, or the statute, limit?** The lists name people
   because a government or the Security Council designated them; publishing
   that fact is the law's purpose. Read: names and aliases as published,
   titles, public positions, nationalities, birth dates and countries of
   birth (how a listed person is told apart from a namesake). Never read: an
   individual's address beyond the country the list names (hard limit 15),
   passport and identity numbers, and the lists' narrative comments, which
   name places and relatives. A listing is never joined to a register row by
   name alone (Privacy Act 2020, principle 8: accuracy). A revoked or expired
   listing is kept as such, with its date.

Crawl delay: Police and the UN site 10 s; MFAT none. Floor: one request at a
time, 10 s apart, off-peak, weekly; a 403, 429, 5xx or challenge stops the
run. Author: sanctions-1 (Opus), 21 October 2026.
