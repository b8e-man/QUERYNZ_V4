"""The one reading of an official number (contract: docs/contracts/keys.md).

A number from a register is the link for an organisation; it is read into
one canonical spelling and checked where a check exists. The old estate
never validated one; company shareholder rows carry an empty official
number on all 1.58 million rows, so a reader must expect None.

- NZBN: 13 digits with a GS1 check digit (an NZBN is a GLN). Spaces and
  dashes are dropped; a wrong check digit is None.
- Company number: the Companies Office's integer, digits only, no leading
  zeros kept.
- Charity number: `CC` followed by digits, upper case.
- Incorporated society number: digits.
"""
import re


def digits(raw: str) -> str:
    return re.sub(r"\D", "", raw or "")


def gs1_check_ok(number: str) -> bool:
    if not number.isdigit() or len(number) < 2:
        return False
    body, check = number[:-1], int(number[-1])
    total = 0
    for i, ch in enumerate(reversed(body)):
        total += int(ch) * (3 if i % 2 == 0 else 1)
    return (10 - total % 10) % 10 == check


def nzbn(raw: str):
    """The 13-digit NZBN, or None when it is not one."""
    d = digits(raw)
    if len(d) != 13 or not gs1_check_ok(d):
        return None
    return d


def company_number(raw: str):
    d = digits(raw).lstrip("0")
    return d or None


def charity_number(raw: str):
    m = re.search(r"\bCC\s*0*(\d{1,6})\b", (raw or "").upper())
    return f"CC{m.group(1)}" if m else None


def society_number(raw: str):
    d = digits(raw).lstrip("0")
    return d or None
