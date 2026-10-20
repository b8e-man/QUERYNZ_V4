# The walk reads the notices of twelve companies and lists forty, and a template cannot ask for more
kind: finding
state: open
use-case: 3 banking director history; also 5, 7, 13
session: banking-1
opened: 2026-10-20

`walk.py` caps the entities it lists at 40 and expands 12 (`LIMITS`);
past those a company's status shows but its Gazette notices and officers
are not read. A director history asks for every company, and a busy
director passes the cap: checkpoint subjects
`companies:companies/9429030013605/director/ad82cc5edcb4` (60
directorships: 28 listed unread, 20 not listed) and
`companies:companies/9429030014688/director/53de21bfaffe` (122 not listed).
The template says so (flag `walk-coverage`) and blocks the clears that
need them. For the report lane: let a template's `template.toml` raise
`entities` and `expand` within a ceiling the shape sets, with the build
time measured (the twelve here took 0.3 to 8.4 s over two runs).
