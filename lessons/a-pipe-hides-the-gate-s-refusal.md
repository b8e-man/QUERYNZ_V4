A pipe after the merge gate (`… | tail -1`) returns tail's exit, not the gate's, so a refused branch reads as green to the `&&` that follows; run the gate alone and read its exit, or write its output to a file and tail that.
area: merge gate, shell, closing, founding
paid-for-by: 2026-10-18, founding session, the close of 1.4 batch 2

The gate refused a branch for a status file 39 bytes over its limit; the
pipe swallowed the refusal, the chain went on, and a later command made a
doc-only commit straight onto main. Same family as the heredoc lesson: a
chain only stops on the exit of its LAST command in a pipeline. The fix
is the same shape: no pipe on the command whose exit matters.
