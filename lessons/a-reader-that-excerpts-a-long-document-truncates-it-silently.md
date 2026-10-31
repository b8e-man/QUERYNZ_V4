A reader that sends a model a long document's head and tail truncates it silently and the reading looks whole, so each profile carries the reader's budget and a split rule: over the budget is read in pieces or set aside, named.
area: document profiles, the text reader of any lane, support/profiles, registers/courts/pieces.py, ruling 130
paid-for-by: 2026-10-31, fix-registers-courts-2, ruling 130

The courts text reader of 30 October sent the model an excerpt when a
document was longer than its context: the first part and the last part,
the middle cut out. Nothing marked the reading. The stored row carried the
model, the prompt's hash and a list of names, the same as a reading of a
whole document, and the check held it to nothing, because the check never
knew how long the document was. Measured on the corpus as the pull of 31
October left it (6,411 records): 1,030 documents over the 34,000-character
budget, more than half the judgments among them; every name in their
middles was never read.

What the fix does. The text-reader profile serves 16,384 tokens a request
with 4,096 reserved for the answer; the model's text ran 3.3 to 4.6
characters a token on 5,679 calls, so 34,000 characters of document is the
budget at the worst ratio seen. Each courts profile now carries that budget
and a split rule in its `reading` field: whole (case pages, releases,
synopses), paragraphs (judgments and determinations: the caption first and
whole, then runs of numbered paragraphs), numbered (submissions: "1.",
"1.1" or a bare number two spaces before the text, indented up to 40
spaces), pages (transcripts: whole pages, a long page cut at its speaker
turns). One model call a piece, each answer stored as it comes so a job
stopped at its deadline resumes; the names joined under the one hash; the
summary made from the pieces' summaries in one more call. A document the
rule cannot split is set aside at read with the reason, and the check
prints the counts of documents by pieces needed. The profile test holds
every document to the rule on the sample and in the live check.

Two measurements worth keeping. The brief's size figure (a median of
75,281 characters) counted case pages' HTML bytes; the model receives a
case page's text of a few hundred characters. Measure what the model is
sent, not what the store holds. And a numbering shape is the lane's only
when it runs in sequence from 1: a bare number followed by text matches
page headers and tables of contents too, so the splitter cuts only where
the next number in sequence appears.
