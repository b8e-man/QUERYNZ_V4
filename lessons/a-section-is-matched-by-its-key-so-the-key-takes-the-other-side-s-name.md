A page section is matched by its key and place, so a rebuilt page takes the frozen page's key names and nesting before any count is read; prose bases go under the one key the comparison treats as prose.
area: published-site, comparison, templates
paid-for-by: site-2, 2026-10-20 (two rebuilds spent on 3,113 differences that were names)

Why: after the money sections were built the comparison still counted 3,113 whole-section differences and 1,551 sections "only on the new side". None was a figure: `industry_exposure` against the frozen's `exposure` (which it also had), `top_donors` at the top level where the frozen kept it under `party_window`, and nine `*_basis` strings the comparison's META list did not know. Renaming and nesting took the two counts to 266 and 209 without a figure moving.

How to apply: before the first comparison run of a new section, list the frozen page's top-level keys beside the new page's (a six-line script) and make the new keys the frozen ones, nested where the frozen nests them; put every basis or note under `basis` (a dict is fine) rather than a new `*_basis` key; a section only the new side can have goes on the template's `sections_added` list the day it is written. Then the count is of figures.
