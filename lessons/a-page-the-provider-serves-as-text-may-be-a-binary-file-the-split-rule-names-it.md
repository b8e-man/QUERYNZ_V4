A text a provider serves as a page may be a binary file's bytes (a WAV header, 22,496 NULs): a names reader's split rule must set such a document aside by name, never cut it at a space or send it to the model.

Area: registers/parliament, every MCP names reader (model_read.py), support/profiles (a profile's split rule).

What happened. parliament-2 (31 October 2026) measured the archived parliament.nz pages for the text reader's budget: 21,989 pages, 3,554 over 24,000 characters, the largest 676,240. The provider's extraction keeps no newline and no heading tag, so a page's text is one line and the split falls to speaker turns where the text marks them, else sentence ends. The profile test (every landed document held to the budget or the split rule) then found one sample page with no sentence end in 46,917 characters: a WAV audio file served as a page (RIFF header, 2,728 letters among 22,496 NULs). On the live tables 11 of 21,989 pages are of that shape.

The rule. A split rule that falls back to "any space" would have cut the file into 24,000-character pieces and sent the model 11 documents of noise; a rule that raises `CannotSplit` sets them aside at stage `read`, named, the check counts them, and no job asks for them. Measure first (the sizes, then the boundaries), write the split rule to name what it cannot cut, and keep the unsplittable case in the sample.

Also learned. A reader store lookup per key called the profile ledger each time (budget → profile_of → read profiles.jsonl): 15.5 s per 10,000 keys, 18 minutes over the lane's 705,000 documents; cached once a process, 0.04 s. Anything a load calls per row is measured on 10,000 rows before the merge.
