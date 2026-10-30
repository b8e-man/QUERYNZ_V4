# registers/parliament — Parliament's written questions, bills, committee papers and archived pages

From the ingest MCP's parliament corpora (rulings 78, 94, 96): written
questions, bills (current and historical), select committee submissions
and reports, supplementary order papers, and archived parliament.nz pages,
the API's own fields as columns. Captured off-estate; the estate fetches
nothing from parliament.nz. Built by `parliament-1`. `parliament-2` added the text
reader (`model_read.py`): the names an archived page or a written question
and its reply carry, into `pub.parliament_people`, read by Flash-Next one
document at a time (several short questions in one request), never a link.
