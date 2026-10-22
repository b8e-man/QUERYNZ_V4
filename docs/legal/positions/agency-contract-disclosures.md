# Agencies' own disclosures of their contracts (draft position, ruling 61)

hosts: catalogue.data.govt.nz, acc.co.nz, nzta.govt.nz, healthnz.govt.nz, tewhatuora.govt.nz, education.govt.nz, kaingaora.govt.nz, nzdf.mil.nz, defence.govt.nz, msd.govt.nz, corrections.govt.nz, orangatamariki.govt.nz, ird.govt.nz, mpi.govt.nz, doc.govt.nz, justice.govt.nz, fireandemergency.nz, customs.govt.nz, mfat.govt.nz, health.govt.nz, publicservice.govt.nz, stats.govt.nz, treasury.govt.nz, dpmc.govt.nz, mfe.govt.nz, linz.govt.nz, nzqa.govt.nz, tec.govt.nz, worksafe.govt.nz, pharmac.govt.nz

Class: what agencies publish, beyond their award notices on GETS, about the
contracts they hold: lists of contracts awarded on their own sites, and
files of their contracts on the government data catalogue. Lane:
`registers/contract_disclosures`. Draft in the lane folder; the integrator
moves it. Surveyed 22 October 2026, 19:50 to 20:05 NZDT, through the fetch
gate, 5 s apart and the catalogue's 10 s (`survey.md`); one file fetched at
22:00. Outcome: **ACC's file captured and read; nothing else held.**

**First, the collected file.** The Government Procurement Rules send each
agency's contract award notice to GETS, and the ministry's open-data file of
them is held (`government-procurement-award-notices`). A search of the
catalogue found no other collected file of awards. No agency of the 24
surveyed by spend publishes its own list of awards as a structured page or
file.

1. **Is the page open?** The catalogue is. Nine agencies' sites answered
   HTTP 403 (Transport Agency, Corrections, Health, DPMC) or an Incapsula
   challenge (Kāinga Ora, ACC, MPI, Fire and Emergency, Environment): failed
   reads, logged, not retried. ACC's file is served by the catalogue itself
   and answered 200 with no challenge.
2. **Is storing it lawful copying?** The catalogue states the licence of
   ACC's package as `CC-BY-NZ-3.0` (`ad5219f9…`), Creative Commons
   Attribution 3.0 New Zealand: copying and commercial reuse with
   attribution. Every row and the view carry it: "Source: Accident
   Compensation Corporation, Health contract data (AR-3944), data.govt.nz,
   licensed under CC BY 3.0 NZ". MSD's contracted funding for 2019/20 states
   no licence (`139f0d22…`): Crown copyright with no licence to copy, so its
   file is not landed; its description is held as the record of why.
3. **What terms did we accept?** None by click. The workbook's own notes
   (`eef2490b…`) say "SUITABLE FOR EXTERNAL USE." and that it was prepared
   for data.govt.nz as an Official Information Act response. The terms of
   `www.data.govt.nz` sit behind a challenge and were not read (as for the
   award notices); lawyer to confirm.
4. **What does privacy law limit?** The file names no supplier, person or
   address: claims and costs by contract class, accident region and
   territorial authority. ACC suppressed small cells itself ("Cell
   suppression of claim counts fewer than 4 show as “<4” to ensure client
   privacy"); the lane keeps the mark as printed and never estimates
   behind it.

Crawl delay: 10 s stated by the catalogue, honoured. Floor: 10 s, one
request at a time, off-peak, each package's description once every 28 days
and a file only when the catalogue's date for it changes. Author:
procurement-1 session (Opus), 22 October 2026.
