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
| beehive | running: 50,500 of 66,571 at 23:58 | | |

## Scheduled

Commit 86cfc87, released 23:57. Each lane's load now queues its name pass. The courts pass queues the courts reader. A links build queues a rebuild of the forms, which queues every lane's pass; a whole scan under new forms removes that lane's sightings under the old forms.

Open: a name the readers find reaches pub.names only when links.rows refills, by hand or by a links build. No nightly refill is wired.

## Units and serving

Worker and model active at 23:58. Metrics logger alive.

Readers running: hansard (row 940), parliament (941), beehive (942).

## Faults and restarts

None so far.

Last updated 2026-10-31 23:59.
