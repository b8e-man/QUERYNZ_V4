A failure inside a `python3 - <<'EOF'` block does not stop the commit, gate and push on the next line (two closes merged without their status edits): chain the git commands to the heredoc's exit, and read the status back before committing.
area: closing, status, shell, founding
paid-for-by: 2026-10-18, founding session 2, the 1.6 and 1.7 closes

A heredoc ends the command at `EOF`. `&&` on the next line is a new
statement, so a failed assertion in the python (an `old` string that no
longer matched the status file) was printed and ignored, and the branch was
committed, gated and merged without the status paragraph or the step's tick.
It was found only by reading `docs/status.md` back two closes later.

How to apply: after `EOF` write `[ $? -eq 0 ] && git add …`, or make the
edit with the Write or Edit tool and run only the git commands in the chain.
Read the status file back before the commit that claims a close.
