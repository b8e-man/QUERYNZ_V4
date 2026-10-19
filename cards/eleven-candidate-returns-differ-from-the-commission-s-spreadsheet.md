# Eleven current candidate returns differ from the Commission's spreadsheet
kind: finding
state: open
use-case: 1
session: candidate-returns
opened: 2026-10-20

`check.py`: of 364 current returns read and joined to the Commission's
newest spreadsheet (2020: `2020-Candidate-Returns.xlsx`; 2023:
`2023-candidate-returns-updated-24092024`), 353 equal it to the cent and 11
differ. Each of the 11 reads under its own page's arithmetic (the parts sum
to the printed total), so these are differences between the filing and the
Commission's figure, not reading faults. The headline rule applies: the
Commission's figure, linked to its file, with ours beside it
(`pub.candidate_return_totals` carries both).

| Return | Election, electorate | Ours | Commission |
| --- | --- | --- | --- |
| `0e01e189ba2c` (amended Feb 2024) | 2023 Taieri | expenses 3,579.02 | 2,393.66 |
| `2fed6f4e8502` (amended Feb 2024) | 2023 Port Waikato | donations 0.00, expenses 2,160.76 | 1,754.52, 2,659.84 |
| `7cc1ef28b9d9` | 2023 Auckland Central | expenses 30,056.83 | 32,402.05 |
| `7b6d40587064` (amended Jun 2024) | 2023 Tāmaki Makaurau | expenses 8,961.42 | 8,961.41 |
| `ba6477b09414` | 2020 Bay of Plenty | expenses 3,131.66 | 3,685.92 |
| `405025782059` | 2020 Auckland Central | expenses 19,380.54 | 19,380.34 |
| `7614409b6449` | 2020 Nelson | expenses 5,969.84 | 5,969.48 |
| `a2d51b57fdc2` | 2020 Nelson | expenses 773.18 | 773.08 |
| `fc7020f5f8a6` | 2020 Rotorua | expenses 35.85 | 38.85 |
| `98161ad95f6d` | 2020 Tauranga | donations 500.00 (Part A, under the threshold) | nil |
| `ca579c46524e` | 2020 Rotorua | expenses 0.00 (a scanner's OCR layer: NIL) | 470.00 |

Five look like the Commission's typing (a transposed or single digit, a
cent); the three 2024 amendments may have a later amendment the Commission
summed and the listing does not link; `ca579c46524e`'s OCR layer likely
missed a handwritten figure (its page reading would settle it). To look at
each page with `python -m registers.candidate_returns.replay shape <hash> 1`.
