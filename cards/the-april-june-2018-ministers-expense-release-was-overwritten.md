# The April to June 2018 ministers' expense release was overwritten in the old folder
kind: finding
state: open
use-case: 1
session: interests-expenses
opened: 2026-10-20

Internal Affairs published two quarters under one file name,
`Ministers-Expense-Return-2017-2018.xlsx` (January to March 2018 and April
to June 2018, two URLs). The old `minister-expenses-capture` job names
files after the publisher's name, so the second download replaced the
first: its manifest lists the April to June bytes (`edcc9da33409…`), and
the folder holds only January to March (`500a520cb2d3…`). The quarter is a
catch-log line twice in `expenses.set_aside` (capture: overwritten;
listing: listed, not held).

A fresh copy needs a fetch, which waits for the switch or Arthur's word;
the URL is in the line. The lesson for any capture job: name a file by its
hash or URL, never the publisher's file name (the store already does).
Blocks: nothing.
