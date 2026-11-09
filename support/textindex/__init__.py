"""The keyword index over whole texts, on the boxes (step 9.3; docs/research/step-9-news-search.md, "What the estate already
has, reused"): tantivy, text indexed and never stored, a hit is a key read back by its owner. Moved here from the Papers Past
lane (registers/papers_past/index.py and search.py, 2 to 5 November 2026) so that a lane builds and searches its own index
and a product, which may import only support/, can search one too.

    write.Spec, write.build(docs, path, spec, ...)       the writer: built beside, moved into place whole
    read.opened(path), read.have(path, ...)              one index opened per process, under one lock
    read.search(path, query, fields, ...)                one page of keys, the whole count, filters, order, a facet
    read.phrase(path, words, fields, ...)                a folded phrase in any of the fields: its count and top keys
    read.words, read.snippet, read.fold, read.SNIPPET    the window of text around a word, and the folding

Nothing here finds a name, builds a person, a claim or a link, or writes to a database (hard limit 17 for Papers Past; hard
limit 14 for the news). Every read is a local file; no model and no network is reached (hard limit 10)."""
from support.textindex import read, write  # noqa: F401
