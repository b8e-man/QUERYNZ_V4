On a job-control line the safety hook reads every token after the verb as a unit, so name each unit literally: a shell variable or a redirection on that line is refused as not on the stop list, since the hook cannot see inside a variable.
area: hooks, job control, old estate, founding
paid-for-by: 2026-10-18, founding session, 1.4 batch 2

Two refusals before the nineteen stops went through: a `for u in …` loop
over the unit names, then the literal list with a redirection on the same
line. Write the names out; put any redirection on another line or drop it.
The read-only checks (`is-active`, `is-enabled`, `list-timers`) may loop.
The hook also reads prose: a lesson or card that quotes such a line with a
variable in it is refused the same way, so describe it in words.
