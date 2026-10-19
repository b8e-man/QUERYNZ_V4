Join a reading to the register it names before trusting its own counts: the liquidation reader reconciled every notice and still cut "(2019)" out of company names, which only the companies register showed.
area: Gazette notices, liquidations, insolvency, company names, outside checks, registers
paid-for-by: 2026-10-20, gazette session 3, step 4.1

Gazette 2 closed with every `al` notice taken and reconciled. Joining its
60,711 company rows to `pub.companies` showed 286 printed numbers whose
register name differed, and the sample was all one fault: the title cleaner
removed every bracket, the name's own included, so FISHERIES (2019) LIMITED
became FISHERIES LIMITED, a different company. The same join then found the
list reader cutting "ABLE TRUSTEES LIMITED" into ABLE TRUST and EES LIMITED,
and numbered companies ("6306902 LIMITED") read as the number of the name
before. Each fix moved the join rate (98.0 to 98.2% for al, 89 to 96.7% for
ds). What held: strip only brackets that are a status, a former name or a
defined term; a suffix ends a name only as a whole word; a list's numbers
are numbers only where most rows print one. A row the register does not
hold stays a catch-log line, never the nearest name.
