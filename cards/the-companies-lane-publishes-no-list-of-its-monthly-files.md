# The companies lane publishes no list of the monthly files it holds, or their cut dates
kind: finding
state: open
use-case: 5 business credit and monitoring; also 3
session: credit-1
opened: 2026-10-21

A change between monthly files is dated to the file that first shows it.
A product can learn which files exist only from the rows it reads, and its
rows cannot say: a company first shown in the later file has no row in the
earlier one, and a removed one none in the later (the credit checkpoint met
both). The credit template therefore carries the two files measured on
2026-10-21 (`FILES_MEASURED` in its rules) and adds any file a row names.
The file names give a month; the cut date of each file, which would date a
change between two days, is recorded nowhere (`companies.files` holds the
document, name, kind and status, measured 2026-10-21). For the companies
lane: `pub.company_files` (file, cut date where the source states one,
rows), and the report's catalogue to know it. The template then reads the files held and
dates a change "between <cut> and <cut>" (a fix in its folder).
