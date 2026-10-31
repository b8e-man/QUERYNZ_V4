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

Names reach pub.names when their load publishes them (Arthur, 1 November; commit 1fe593c, released 00:25). Each of the 19 loads whose register feeds pub.names queues its own register's refill of links.rows; the other registers stand. A reader lane runs load, then names refill, then name pass, then (courts) the reader. The courts refill by hand took 16.7 s and 76 MB. Refills and the links build take one lock, so they run one at a time.

48,218 distinct name forms were sighted at least once.

## Units and serving

Worker and model active at 23:58. Metrics logger alive.

Readers running: hansard (row 940), parliament (941), beehive (942).

## Faults and restarts

None so far.

Last updated 2026-11-01 00:26.
