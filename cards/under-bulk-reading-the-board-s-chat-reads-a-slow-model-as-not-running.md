# Under bulk reading the board's chat reads a slow model as not running
kind: finding
state: open
use-case: board
session: integrator-9d788fb
opened: 2026-10-31

The board's outside check (`products/board/check.py`, the chat item) failed
the merge gate of integrate/fix-registers-courts-1 at 09:2x on 31 October:
"/chat asked 'which registers hold Rank Group Limited?' with the model up
answered 200 'the chat model is not running'". Radiance was up and serving
`qwen4exp`; both cards were at 100% on three build sessions' sample reads.
`products/board/chat.py` gives one model call 60 s (`CALL_S`) and turns ANY
exception, a timeout included, into `NOT_RUNNING`; the check then reads the
answer as the model being down. In a bulk ingest (Arthur, 31 October: every
MCP document read as quickly as possible) the model is saturated for weeks,
so the board's chat will say this often and every gate's outside check is
red on it by chance.

Owner: board. Next: the chat tells a timeout from a refused connection
("the chat model is busy; asked again in N s" against "not running"), the
check's chat item accepts a busy model as up, and the limit is measured
against the queue's depth rather than fixed at 60 s. Until then the gate is
rerun.
