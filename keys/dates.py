"""The one reading of a filed date (contract: docs/contracts/dates.md).

- A date as filed is read DAY FIRST in every shape the forms arrive in:
  07/09/2026, 21/1/26, 10 Mar 2026, 10 March 2026, 2026-09-07. A US-order or
  mangled date (45/08/2014) is not a date and returns None.
- A year read from pixels is checked against the Commission's own file name
  (`…_16_May_2023.pdf`): when the day and month agree and the year does not,
  the file name's year wins, and the basis says so. A future year is not a
  date.
- An ended role carries the day it ended as the file states it, never the
  day the file was imported: that is a rule on the row contract
  (`support/rowcontract`), and `filed_date` is what a lane uses to read it.
"""
import datetime as dt
import re

_MONTHS = {m: i for i, m in enumerate(("jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"), 1)}
_NUMERIC = re.compile(r"(?<!\d)(\d{1,2})\s*[/.-]\s*(\d{1,2})\s*[/.-]\s*(\d{2,4})(?!\d)")
_ISO = re.compile(r"(?<!\d)((?:19|20)\d{2})-(\d{2})-(\d{2})(?!\d)")
_PRINTED = re.compile(r"(?<!\d)(\d{1,2})\s+([A-Za-z]{3,9})\.?,?\s+((?:19|20)\d{2})(?!\d)")
_FILE_DATE = re.compile(r"[_-](\d{1,2})[_-]([A-Za-z]{3,9})[_-]((?:19|20)\d{2})", re.I)
FAR_FUTURE_YEARS = 1


def _year(y: str):
    y = int(y)
    if y < 100:
        y += 2000 if y < 70 else 1900
    return y


def _make(y: int, m: int, d: int):
    try:
        return dt.date(y, m, d)
    except ValueError:
        return None


def filed_date(text):
    """The date in `text`, day first, as a `date`; None when there is none
    or it is not a real day."""
    s = (text or "").strip()
    if not s:
        return None
    m = _ISO.search(s)
    if m:
        return _make(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    m = _PRINTED.search(s)
    if m and m.group(2).lower()[:3] in _MONTHS:
        return _make(int(m.group(3)), _MONTHS[m.group(2).lower()[:3]], int(m.group(1)))
    m = _NUMERIC.search(s)
    if m:
        return _make(_year(m.group(3)), int(m.group(2)), int(m.group(1)))
    return None


def file_name_date(name: str):
    m = _FILE_DATE.search(name or "")
    if not m or m.group(2).lower()[:3] not in _MONTHS:
        return None
    return _make(int(m.group(3)), _MONTHS[m.group(2).lower()[:3]], int(m.group(1)))


def year_from(date_text, file_name: str = "", today: dt.date = None):
    """(year | None, basis). The read date first; the file name's year when
    the read year is impossible or disagrees on the year alone; 'undated'
    when nothing gives a year."""
    today = today or dt.date.today()
    read = filed_date(date_text)
    named = file_name_date(file_name)
    if read and read.year <= today.year + FAR_FUTURE_YEARS:
        if named and (read.day, read.month) == (named.day, named.month) and read.year != named.year:
            return named.year, "source_file (read year corrected)"
        return read.year, "date_received"
    if named:
        return named.year, "source_file" if not read else "source_file (read year corrected)"
    m = re.search(r"(?<!\d)((?:19|20)\d{2})(?!\d)", date_text or "")
    if m and int(m.group(1)) <= today.year + FAR_FUTURE_YEARS:
        return int(m.group(1)), "date_received"
    return None, "undated"
