"""The one report's checks (step 9, ruling 157): one set of red, amber and clear checks, merged from the retired templates'
and the diagnostic's, each check once. The checks are written in products/report/checks_combined.py, where each names the
retired functions it carries (MERGED); the contract's common rules run first, as for every template."""
from products.report import checks_combined as _combined

RULES = _combined.CHECKS
