An honorific after the comma ("Hipkins, Rt Hon Chris") survives keys.names.person_name and person_key, so strip it from the given part yourself before matching a roster name to pub.members.
area: keys, names, members, hansard, parliament, matching people
paid-for-by: 2026-10-26, hansard-1, ruling 96

The old Hansard roster files every member as `Surname, Hon Given` (Rt Hon, Hon, Dr, Hon Dr). `strip_honorifics` only
takes a leading honorific, so `person_key("Hipkins, Rt Hon Chris")` is `rt hon chris hipkins` and matches nobody:
56 of 128 speakers matched `pub.members` by key. With the honorifics taken from the given part (registers/hansard/
check.py `name_parts`), 111 matched by full given names and 7 more by the first given name; the 10 left are list
members who came in mid-term, which pub.members does not hold (card who-left-the-house-mid-term-is-not-in-the-results-files).
Measure the match by basis on the whole set before setting a floor; a surname alone was never needed.
