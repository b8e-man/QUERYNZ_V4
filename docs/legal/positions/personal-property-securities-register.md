# The Personal Property Securities Register (position, hard limit 9)

hosts: ppsr.companiesoffice.govt.nz, www.ppsr.govt.nz

Class: the Companies Office's register of security interests in personal property (Personal Property Securities Act 1999): who
has registered a financing statement against a debtor organisation or person, over what collateral, and when. Surveyed 2
November 2026 by step 8.4 (its help pages only: the fee schedule and the debtor organisation search guide). No lane is built.

1. **Is the page open?** No. Every search needs an online services account (RealMe, or a social login for an individual
   account), a declaration before each search that it is made for a legitimate reason, and a fee: $2.30 a search on the
   website, $1.15 a search through the API (the fee schedule, read 2 November 2026). There is no bulk file and no search
   without paying. A search by organisation takes its name, or its incorporation number and NZBN.
2. **Is storing it lawful copying?** Not reached: nothing is fetched behind the account.
3. **What terms did we accept?** None. An account, its terms and a payment method are Arthur's to set up in the estate's name.
4. **What does privacy law, or the statute, limit?** The Act's permitted purposes for a search (the declaration above); a
   debtor person's search is by first and last name and needs the same declaration. A person's address is never published
   (hard limit 15).

What a lane could be, on Arthur's word: not a copy of the register, which cannot be had, but an on-demand search of a
debtor organisation by NZBN through the API, asked by a product when a report needs it (products rule 2: the lane does the
fetch), each answer landed by hash, each search's fee counted against a budget Arthur sets.

Floor: 5 s between requests, one at a time.
