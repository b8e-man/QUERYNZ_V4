# Overnight, 31 October to 1 November 2026

Arthur approved this night's work at 23:45 on 31 October. This report is updated each half hour; the last update time is at the foot.

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

## Faults and restarts

No unit stopped; nothing restarted.

Standing faults outside tonight's scope, failing the same way on earlier nights: qv4-charities-capture (rows 889, 974, last 23:30) and qv4-tenancy-tribunal-capture (rows 876, 958, last 22:36), each "exit 1" with no message in the run record.

Last updated 2026-11-01 00:16.
