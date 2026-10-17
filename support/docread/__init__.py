"""docread — the document reader, carried from the old estate behind the
reader contract (plan 1.10; docs/contracts/reader.md). `read.py` is the
contract's door; `pages.py` the text layer; `pagereader.py` the page
reader through the model client; the rest (parse, rows, invariants,
arbitrate, gold, queue) is the old reader and its checks, carried with its
tests.

The old head:
reading a document IMAGE into rows we can defend.

Built 2026-09-23 after an overnight audit reported "554 documents, 3 with
disagreements" and the real basis was 26 documents: 528 of 554 (95.3%)
produced no parsed rows at all. The reading was not the failure — GLM-OCR
transcribes a page's characters accurately — the STRUCTURE was: the model
decides per page what counts as a table, and on one page of a document it
emitted the form's row numbers and on the next, identically laid out, it did
not.

The service exists because that class of failure is silent. This one
announced itself only because the return also failed its total.
"""
__all__ = ["invariants", "rows"]
