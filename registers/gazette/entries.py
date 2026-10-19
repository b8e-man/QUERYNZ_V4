"""What the company-notice readers give (removals.py, windingup.py,
receiverships.py): one Entry per company a notice names, and the notice's
own fields once in its Reading. read.py turns both into `company_notices`
rows; register.py joins each to the companies register.
"""
from dataclasses import dataclass, field


@dataclass
class Entry:
    ordinal: int
    name: str
    number: str = None
    event_on: str = None          # this company's own date, where the notice gives each its own
    event_at: str = None


@dataclass
class Reading:
    shape: str = None             # notice | list
    companies: list = field(default_factory=list)
    action: str = None            # the notice's own words: intention to remove, application to liquidate, …
    statute: str = None           # the first Act and section cited
    ground: str = None
    by_whom: str = None           # who gives notice or appointed: liquidator, Registrar, director, a creditor, …
    party: str = None             # the plaintiff (aw), as printed, never its address
    event_on: str = None          # the notice's date that matters: objections by, the hearing, the appointment
    event_at: str = None
    event_basis: str = None       # what event_on is
    filed_on: str = None
    court: str = None
    reference: str = None         # the court's file number: CIV-2014-404-1234
    dated_on: str = None
    corrigendum: bool = False
    people: list = field(default_factory=list)      # receivers or administrators: liquidations.Liquidator
    unread: list = field(default_factory=list)      # (place, why)
