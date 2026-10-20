# The shareholders view carries no parcel, no issued shares and no allocation date
kind: finding
state: open
use-case: companies (4.1); 13 beneficial ownership and AML; 3 banking
session: ownership-1
opened: 2026-10-21

pub.shareholders gives one row per holder with `shares`, but no allocation
(parcel) identifier, no count of the company's issued shares and no date the
holding began: `allocation_status` is "active" on all 1,581,955 rows, and
the rows are dated only by the monthly files they were seen in. A parcel
held jointly is filed once per holder with the parcel's count, so summing
the rows double-counts: SAILPLANE SERVICES 2005 LIMITED
(`companies/9429034838242`) shows a trustee company and two people on 200
shares and the two people again on 300. The old chain page divided each
row by the rows' sum and so overstated joint holders. A compliance check
needs each holder's fraction (the 25% line) and the date it was acquired.
For the companies lane: publish the allocation identifier and the issued
shares from the bulk file where it carries them, and say in the pane if it
does not. The ownership template states the shares filed for each holding
and computes no fraction until then.
