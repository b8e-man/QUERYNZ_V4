# QueryNZV4 Build Plan

Oct 11, 2026 · @arthur falls

This is the complete set of instructions for building QueryNZV4, written for a Fable agent that has not seen the discussion behind it. Follow the steps in order; each says what to do, why, how to know it is done, and what to hand Arthur.

### What to read, and how much

**Read only what your work needs.** Arthur's ruling 54 (12 October): "I want to be able to easily work on the new estate. It takes a long time to get an output from a prompt on the old estate." A session there read hundreds of kilobytes of doctrine, lessons and logs before it could answer. This document is itself about 200 KB, so it is split, and required reading has a limit.

**The first founding session reads this document whole, once.** In step 1.1 it splits the document into the files below. From then on no session reads all of it.

| File | Holds, by the headings of this document | Limit |
| --- | --- | --- |
| `CLAUDE.md`, at the top of the repository | Up to 3 KB of orientation written in step 1.1, then "Hard limits" whole. Claude Code loads it unasked | 10 KB |
| `docs/PLAN.md` | The index: this section, under the title lines that stand above "Read this first" | 5 KB |
| `docs/plan/core.md` | "Who you are", "Who Arthur is", "What you may decide, and what you may not", and "How the work runs" except its last three headings | 27 KB |
| `docs/plan/limits.md` | "Hard limits". Their one home; a check fails if the orientation file's copy differs | 7 KB |
| `docs/plan/step-0.md` to `step-7.md`, and `step-1b.md` | One step each, with its brief | 28 KB each |
| `docs/plan/tracks.md`, and `track-a.md` to `track-h.md` | The opening paragraph of "Tracks alongside", then one track each | 28 KB each |
| `docs/plan/design.md` | "What we are building" | None |
| `docs/plan/reuse.md` | "Reusing the old code" | None |
| `docs/plan/map.md` | "Where everything is", "Words used in this plan", "The order of work", "Which model does what", "Size, and what each step asks of Arthur" | None |
| `docs/plan/reference/` | The four reference sections, one file per third-level heading | None |
| `docs/plan/headings.md` | Written by the split: every heading and step number, with its file. Search it to follow a cross-reference such as "see step 1.10" | None |

**What each kind of session reads before it starts.** A kilobyte here is 1,000 bytes. "Three weights of session", in `core.md`, says what the weights are.

| Session | Reads | At most, about |
| --- | --- | --- |
| Question | The orientation file. Then only what the question needs | 10 KB |
| Fix | The orientation file, this index, `core.md`, and the spec of the one module it changes | 43 KB |
| Build | The same, then its step file (for a track, `tracks.md` and its track file), `docs/status.md`, its own status file, and the specs of the modules it touches | 77 KB |
| Integrator | The orientation file, this index, `core.md`, `docs/status.md`, and the requests waiting in the inbox | 45 KB and the requests |

`design.md` and `reuse.md` are read when a brief names them, or when the work is a new lane, link rule or product shape. `map.md` says where everything is and what the words mean: look there first when a path, a box or a term is unknown. Otherwise all three are looked up, not read through.

**A check holds the limits.** It runs in the fast tier and fails when a file passes its limit. So a rule added to `core.md` has to fit, which usually means another rule is cut, merged, or turned into a check a machine runs. Every ceremony on the old estate was added for a good reason and none was ever taken away. The limits are starting figures; change them by ruling once sessions have been timed.

