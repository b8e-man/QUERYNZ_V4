# May a minister's diary entry show a street address that names no place of business?
default: No. The location is held back (published empty, with the reason "a street address with no place of business named"), kept in ministers_diaries_private; 3,096 of 208,464 entries on 27 October. A location naming a home or residence (115) is held back either way
blocks: Nothing. The register is built on the default; the rule is one function (registers/ministers_diaries/read.py `place_of_business`), so a change is a re-read, not a rewrite
recommendation: The default. Most of these are offices and venues (a business with its street number), but the release gives no way to tell one from a home by shape, and hard limit 15 does not trade for coverage. The town is lost with the street; showing only the town after the street is a later refinement if the product wants it
raised: 2026-10-27 by diaries-2
