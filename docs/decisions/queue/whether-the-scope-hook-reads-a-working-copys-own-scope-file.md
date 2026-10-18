# Whether the scope hook should judge by a working copy's own `.scope` when the command's folder has one, rather than the project folder's
default: No: the fence is the folder Claude was started in, and the fix is to start every session there. On 18 October the founding session started the offsite and windowed sessions as its own agents, so both were fenced as the main checkout: every write to their working copies was refused and the main checkout was open to them (neither wrote there). Both stopped rather than work around it. A hook that followed the command's folder would let any session widen its fence by changing folder.
blocks: Nothing. Both tracks restart from their working copies (`docs/briefs/next.md`).
recommendation: The default; and the founding session never again starts a build session as an agent of itself. The lesson is filed by the windowed session (in its tree).
raised: 2026-10-19 by founding, on the offsite and windowed sessions' requests
