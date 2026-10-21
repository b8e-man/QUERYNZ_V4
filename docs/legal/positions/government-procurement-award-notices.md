# Government procurement award notices (draft position, ruling 61)

hosts: mbie.govt.nz, catalogue.data.govt.nz, data.govt.nz

Class: the Ministry of Business, Innovation and Employment's open data of
award notices from the Government Electronic Tenders Service (GETS): CSV
files of award notices, supplier data, region by tender and product
categories (current era July 2019 on, quarterly; historic era July 2014
to June 2019), with a schema workbook, as the files sit under
`www.mbie.govt.nz/assets/Data-Files/NZGPP-GETS-Open-Data/` and as the
government data catalogue describes them (`catalogue.data.govt.nz`,
package `new-zealand-government-procurement-award-notices`). Lane:
`registers/tenders`. The GETS site itself (`gets.govt.nz`) and its login
are not used.

Draft, in the lane folder because the fence keeps a build session out of
`docs/legal/positions/`; the integrator moves it. Ruling 61: before
product, not before capture. Read 21 October 2026 through the fetch gate.

1. **Is the page open?** The catalogue is: its description of the package
   answered with no login, key or challenge (`2ed62b08…`). The files are
   not, to us: on 21 October 2026 `www.mbie.govt.nz` answered HTTP 403 to
   both files asked with the estate's own User-Agent, and
   `www.data.govt.nz` answered with an Incapsula challenge page. Each is a
   failed read (hard limit 6): logged, not retried, not got around. The old
   estate's notes say the files answer a browser-like User-Agent and
   challenge a plain one; we do not change our User-Agent. The files held
   are the old estate's raw acquisition of 14 August 2026, copied by hash
   (plan 1.10, case 1); whether that copy is kept is on the queue. Robots:
   `www.mbie.govt.nz` gave no readable file; the catalogue states a crawl
   delay of 10 s, honoured.
2. **Is storing it lawful copying?** The catalogue states the licence:
   "Creative Commons Attribution 3.0 New Zealand" (`CC-BY-NZ-3.0`), Crown
   copyright, published by the ministry under NZGOAL. CC BY allows copying,
   adaptation and commercial use with attribution. Attribution is owed on
   every surface that shows the data, and every row and view carries it:
   "Source: Ministry of Business, Innovation and Employment, New Zealand
   Government procurement award notices, licensed under CC BY 3.0 NZ". The
   old estate recorded "CC-BY 4.0"; the catalogue's statement is the one
   on file. Lawyer to confirm, and to confirm that the ministry's own site
   terms, which we could not read, do not narrow it.
3. **What terms did we accept?** None by click. The site terms of
   `www.data.govt.nz` sit behind the challenge and were not read. The
   schema workbook (`ac1f4c17…`) states the fields' limits: business
   numbers and names "not validated", the supplier's address "not
   validated", "Not Awarded" sometimes marked in error.
4. **What does privacy law limit?** The files name agencies and suppliers.
   A supplier is mostly a company, sometimes a sole trader under their own
   name; the supplier file carries an address and a website for each. The
   lane never reads the address column or the website (hard limit 15): a
   sole trader's name is kept and nothing finer. The notices' free-text
   overview and comments, which can name a contact person, are not read.
   Privacy Act 2020: names published by a public agency for the purpose of
   showing who won public contracts; use must still be fair.

Crawl delay: 10 s stated by the catalogue; none readable for the ministry.
Floor: 10 s of rest after each answer, one request at a time, off-peak
(22:00 to 06:00 NZ), each file once a quarter. Author: tenders-1 session
(Opus), 21 October 2026.
