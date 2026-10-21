# openlaw: the board's pane

Held: nothing shows until OpenLaw NZ authorises copies (API terms 3.6(a);
the position, question 3). Then one pane, "Case law (OpenLaw NZ)":

- **Count:** cases held against the interface's own figure (check.py's
  outside line), the pass it came from and its date.
- **Suppression:** cases suppressed, by marker; party names withheld.
  Never a name, never a title of a suppressed case.
- **Parties:** cases by parties per case (0, 1, 2, 3+), and where the
  parties came from (the interface's table, the caption, none).
- **Graph:** citation rows, statute links, cited cases not held.
- **Catch log:** set-aside lines by stage and reason.

Every figure comes from `pub.court_cases`, `pub.court_case_parties`,
`pub.court_case_citations` and `pub.court_case_statutes`, or check.py.
