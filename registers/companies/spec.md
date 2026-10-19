owns: schema `companies` (companies and the other entity types, directors, shareholders and registered addresses, from the Companies Office's monthly file, by file hash) and `companies_private` (a person's residential address where the file carries one; never published)
reads: the monthly file Arthur downloads by hand (find where the raw files are kept; if only the old estate's loaded tables in `nzbn_canonical` survive, export once by hash, as `registers/gazette/capture.py` did); fetches nothing; the monthly file is never raised as outstanding
publishes: `pub.companies`, `pub.directors`, `pub.shareholders`, `pub.company_addresses` (a company's registered address is shown; a person's home address never), each row with its citation
outside check: the Companies Office's own count of live companies on a date against the rows live on that date
jobs: a `qv4-companies-load` job on the scheduler once the lane reads; no capture job before the switch
