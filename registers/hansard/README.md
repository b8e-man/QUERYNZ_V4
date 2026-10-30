# registers/hansard — who spoke in Parliament

The old estate's Hansard register (held at 23 September 2026), exported
once by hash (ruling 96), with the MCP's `parliament-hansard-index` fields
joined by URL, the MCP's daily Hansard PDFs read as one text a sitting
day (`days`, 2003 on), and the MCP for updates. Built by `hansard-1` (the
export), `hansard-2` (the MCP) and `hansard-3` (the split and the names
reader): every day's text is cut into sections and speaker turns by the
deterministic rule of profile `hansard-day` (`split.py`; the two layouts,
final and draft, and the member from the old roster), so the days only the
MCP holds have speech turns in `pub.hansard_speeches`; the text reader
(`model_read.py`, Flash-Next, 40,000 characters a piece, the pieces joined
under the day's hash) reads the names the speeches mention into
`pub.hansard_people`, never a link. `python -m registers.hansard.split
--prove` compares the split with the old estate on the 137 days both hold.
