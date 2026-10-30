# registers/courts — the courts' documents, from the MCP's corpus

Step 5.4, items 2 and 3; rulings 126 to 128 (30 October 2026). The lane's
one source is the ingest MCP's `courts` corpus as `support/mcpsource` lands
it: the records, and each record's file by hash (case pages, judgment PDFs,
media releases, hearing transcripts, counsel's submissions, case synopses).
Nothing is fetched from any court site; the old capture is retired.

Every file is recognised by shape before it is read (`read.recognise`), read
deterministically (the caption grammar in `caption.py` for a judgment; the
case page's court, name, dates and links; a sheet's citation and date), and
read once by the text reader (`model_read.py`, Flash-Next through the model
client) for every person and body it names with its role and a one-line
summary, stored by hash and replayed by every load. A page with no text
layer waits for the page reader. The suppression lever (`suppress.py`)
withholds a name on every surface, model-read names included, and is never
undone by a command. The research note on how legal documents are
structured is `docs/research/legal-documents.md`.

Built by `courts-1` (the caption grammar, the lever) and `courts-2` (the
corpus as the source, every kind, the text reader); `spec.md` says what it
owns, reads, publishes, checks and runs.
