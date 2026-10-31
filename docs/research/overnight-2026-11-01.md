# Overnight, 31 October to 1 November 2026

Arthur approved this night's work at 23:45 on 31 October. This report is updated each half hour; the last update time is at the foot.

## Arthur's approvals, 1 November, before bed

Asked and answered in chat:

1. Switch the text reader to Qwen 3.6 35B-A3B Q4_K_M, one copy on each card; Radiance (Flash-Next) stopped, not removed. The review agent moves to Qwen 3.6 too, thinking on.
2. If Qwen 3.6 measures worse on the same 20 documents per lane (warm speed, answers cut, names found), put Radiance back without asking and report the figures.
3. Keep the Flash-Next readings already made; Qwen 3.6 reads only unread documents.
4. Give each reader the names the name pass already found and ask the model only for new ones; the found names stay logged in links.sightings. Release once it passes the 20-document test per lane without losing names.

## The name pass

Every name in pub.names is looked for, by exact match, in each lane's documents before the model reads them (links/sightings.py). Found names go to links.sightings; pub.name_sightings is the published view.

Forms version 47bbeae00d63: 1,859,701 name forms (people 1,843,415; organisations 16,139; estates 147).

| Lane | Documents | Sightings | Seconds |
| --- | --- | --- | --- |
| parliament-questions | 683,270 | 1,680,829 | streamed |
| parliament-wayback | 23,052 | 1,816,108 | streamed |
| hansard | 1,862 | 1,759,082 | 748 |
| courts | 6,395 | 313,134 | 784 |
| beehive | 66,571 | 473,971 | finished 00:03 |

## Scheduled

Commit 86cfc87, released 23:57. Each lane's load now queues its name pass. The courts pass queues the courts reader. A links build queues a rebuild of the forms, which queues every lane's pass; a whole scan under new forms removes that lane's sightings under the old forms.

Names reach pub.names when their load publishes them (Arthur, 1 November; commit 1fe593c, released about 00:10). Each of the 19 loads whose register feeds pub.names queues its own register's refill of links.rows; the other registers stand. A reader lane runs load, then names refill, then name pass, then (courts) the reader. The courts refill by hand took 16.7 s and 76 MB. Refills and the links build take one lock, so they run one at a time.

48,218 distinct name forms were sighted at least once.

## Units and serving

Worker, model and metrics logger active at every check (00:12).

Warm window 23:52 to 00:14, from live/checks/serving-metrics.jsonl (the model was restarted at 23:40; the cold first minutes are left out):

| Measure | Value |
| --- | --- |
| Generated tokens a second | 130 |
| Prompt tokens a second | 865 |
| Requests a minute | 10.5 |
| Requests running, average | 13.5 of 16 |
| Requests waiting, average | 0.7 |

| Reader | Pieces done of total at 00:14 | Pieces a minute | Hours left at that rate |
| --- | --- | --- | --- |
| hansard (row 940; a piece is a day) | 89 of 1,857 | 0.5 | 59 |
| parliament (row 941) | 751 of 65,809 | 2.3 | 470 |
| beehive (row 942) | 1,555 of 66,399 | 3.3 | 330 |

## The switch to Qwen 3.6, and the night lost

- 00:56: Radiance stopped and disabled; the switch released (commit 3f5e722); the worker restarted.
- 00:56 to 07:16: NO reader ran. The old worker, seeing Radiance stop, wrote both cards into the scheduler as held for it; the new worker kept that hold because registration kept any existing reservation, and with Flash-Next gone from the profiles nothing cleared it. Qwen 3.6 never loaded. The half-hourly checks did not fire in that time, so nobody saw it. Six hours of reading lost.
- 07:16: fixed (commit 67d4839: a hold for a standing server no longer in the profiles is cleared at registration; any other reservation stands), released, worker restarted. Both cards loaded Qwen 3.6 in 10 s and 4 s; card use 98 to 99% (Radiance: 3%); card memory 87% and 80%.
- The nightly loads, names refills and name passes ran on time through the night (they need no model).

## Qwen 3.6 measured, and rolled back (08:52)

Same documents, Flash-Next's stored reading against Qwen 3.6 read now (live/checks/ab-2026-11-01/ab.jsonl):

| Lane | Documents | Names, Flash-Next | Names, Qwen 3.6 | Days cut at the token cap |
| --- | --- | --- | --- | --- |
| beehive | 20 | 118 | 99 | 0 and 0 |
| hansard | 15 | 5,127 | 4,873 | 2 and 7 |

The run stopped at its 50-minute limit before parliament and courts.

Speed, 08:09 to 08:15 with no comparison running: Qwen 3.6 generated 256 tokens a second on two cards (Flash-Next 130 on both), cards 96% busy, but its answers run longer, so documents came slower: beehive 1.9 a minute (Flash-Next 3.3), parliament 1.3 (2.3), hansard 0.48 days (0.5), courts 1.75. A short window, but it agrees with 07:27 to 07:45.

By the rule Arthur approved (fewer names, more answers cut), Flash-Next is back: commit 625a313, Radiance answering 08:52, the worker holding both cards for it, the night window restored. Kept: the worker's per-card fixes, the store's earlier-model rule, hansard's replay of days read under version 1, and the fix for a retired standing server's hold. The Qwen 3.6 readings made between 07:16 and 08:50 stay on disk; Flash-Next does not use them, so those documents are read again.

The name hint (option 3) was not built.

## Faults and restarts

- Standing, outside tonight's scope, failing on earlier nights too: qv4-charities-capture and qv4-tenancy-tribunal-capture, each "exit 1" with no message.
- qv4-mcp-pull failed at 01:58; qv4-full-tier failed at 05:00. Not yet looked at.
- qv4-sightings-courts peaked at 1,036 MB against 1,024 declared; the figure wants raising.
- The board's chat calls Radiance's address (:8060) and does not answer while Qwen 3.6 serves.

Last updated 2026-11-01 08:55.
