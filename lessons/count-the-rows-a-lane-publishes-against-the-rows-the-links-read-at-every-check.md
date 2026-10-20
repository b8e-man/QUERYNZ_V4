Count every published view the links read against what the last gather read, at every check: a lane that loads rows after the links ran leaves them with no key and no link, and nothing else notices.
area: links, the outside check, a lane's load after a merge, qv4-links-build
paid-for-by: 2026-10-20, links-2, step 4.2 (site-3's card the-links-hold-a-donor-key-read-before-party-returns-5-fixed-the-row)

The links read the published tables once and hold what they read; a lane
that reloads or fixes a row afterwards (party-returns-5's name cell) leaves
the links folding by the old key, and the site found 54 of 58 twinned
donors had rows the links had never seen. The rows now keep a catch log
per view (`links.rows_catch`: read = written + set aside) and `check.py`
counts each view again and fails when the count has moved. The cure is the
job (`qv4-links-build` after each lane load); the check is what says the
job did not run.
