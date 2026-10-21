"""A party's annual financial statements: its headline figures, read
(contract: the reader; profile `ec-party-financial-statements`).

Statements are free-form accounts, not a form. The reader takes six
headline figures, each from a line that is its label and then figures and
nothing else, the reported year's column first:

    income        Total Income | Total Revenue(s) | Total Operating Income …
    expenditure   Total Expenses | Total Expenditure | Total Operating Expenses …
    surplus       a line naming the surplus or deficit
    assets        Total Assets
    liabilities   Total Liabilities
    net_assets    Net Assets | Total Equity | Total Members' Funds | Total Accumulated Funds …

The Commission publishes no figure for a statement, so each figure is
checked by the statement's own arithmetic, in two pairs, and a pair that
does not hold publishes nothing:

    income-less-expenditure   income − expenditure is a surplus or deficit line the statement prints
    assets-less-liabilities   assets − liabilities is a net-assets or equity line the statement prints

Income is the last income line before the first expenditure line, on its
page or the one before (Te Pāti Māori prints a subtotal first; New
Conservatives 2024 put income and expenditure on facing pages). Whole-dollar statements may
round each line, so they agree within a dollar; statements with cents to
the cent. Where no line agrees so, a line less than $100 off is taken
(ruling 66, `reconcile.py`): the printed figure published, and every
figure of the pair carrying the `issue` that names the difference. A pair
that agrees only within its printed precision carries its difference too, and
no precision admits $100 or more. A printed dash or NIL is zero; brackets are negative, and a line
named deficit alone is negative. The second figure on a line, when there
is one, is the prior year's, kept to check against the year before.

This tranche reads text-layer pages only (`pages.thin_pages` are left for
the page reader's stored readings).

    read_statement(data, sha256) -> Result
"""
import re
from dataclasses import dataclass, field

from support import profiles
from support.docread import pages
from registers.party_finance import reconcile

PROFILE = "ec-party-financial-statements"
READER = "registers.party_finance.statements 1"
MODEL = "pdftotext -layout"
FIGURES = ("income", "expenditure", "surplus", "assets", "liabilities", "net_assets")
#: the two pairs a statement is checked by, and the three figures each publishes
PAIRS = {"operating": ("income", "expenditure", "surplus"), "position": ("assets", "liabilities", "net_assets")}

#: one figure as a statement prints it: `1,234`, `(1,234)`, `$ 1,234.56`, `-`, `NIL`; a scanner's `3 ,135,643` is one
#: figure. A lone dash is a nil column where the page's figure columns end, and the next figure's sign anywhere else
#: (`-            339` is minus 339 in NewZeal 2025; `-           12,143` is nil, then 12,143, in TOP 2024)
NUM = r"\d[\d,]*(?:\s,\d{3}(?:,\d{3})*)*(?:\.\d+)?"
TOKEN = re.compile(r"\(\s*\$?\s*" + NUM + r"\s*\)|-?\$?\s?" + NUM
                   + r"|(?<!\S)[-–—](?!\S)|\bNIL\b|\bNil\b|\bnil\b")
#: a line is a label and then figures and nothing else
LINE = re.compile(r"^\s*(?P<label>[A-Za-z][A-Za-z’'&/().,\- ]*?)\s*:?\s+(?P<figs>(?:" + TOKEN.pattern + r")(?:\s+(?:"
                  + TOKEN.pattern + r"))*)\s*$")
#: the column heads: two years on a line of their own (after an optional word); `2023  2024` puts the reported year last
YEARS = re.compile(r"^[ \t]*(?:[A-Za-z][A-Za-z ]*?[ \t]+)?((?:19|20)\d\d)[ \t]+((?:19|20)\d\d)[ \t]*$", re.M)
#: a statement in thousands says so in its column head
THOUSANDS = re.compile(r"\$\s*['’]?\s*000s?\b|\(\s*\$?\s*000s?\s*\)|in\s+thousands", re.I)
TI = r"(?:ti|\s)?"   # a dropped `ti` ligature: `Opera ng`
LABELS = {
    "income": re.compile(r"^total\s+(?:opera" + TI + r"ng\s+)?(?:income|revenues?)(?:\s+and\s+other\s+income)?$", re.I),
    "expenditure": re.compile(r"^total\s+(?:opera" + TI + r"ng\s+)?(?:expenses|expenditure)$", re.I),
    "surplus": re.compile(r"^(?:(?:net|gross|total)\s+)?(?:opera" + TI + r"ng\s+)?(?:surplus|deficit|profit|loss|income|gain\s*/\s*loss|"
                          r"surplus\s*/?\s*\(?\s*defic[ie]t\s*\)?|\(?\s*deficit\s*\)?\s*/?\s*surplus|"
                          r"profit\s*\(\s*loss\s*\))(?:\s+(?:before|after)\s+(?:income\s+)?tax(?:ation)?)?"
                          r"(?:\s+for\s+(?:the\s+)?(?:year|period))?$", re.I),
    "assets": re.compile(r"^total\s+assets$", re.I),
    "liabilities": re.compile(r"^total\s+liabilities$", re.I),
    "net_assets": re.compile(r"^(?:total\s+)?net\s+assets(?:\s*/\s*equity)?$|^total\s+(?:equity(?:\s+reserves)?|"
                             r"members[’']?\s+funds|accumulated\s+funds|balance)$|^total\s+assets\s+less\s+total\s+"
                             r"liabilities\s+\(net\s+assets\)$", re.I),
}


@dataclass
class Line:
    page: int
    label: str
    amount: float
    prior: float
    step: float          # the printed precision in dollars: 1 for whole dollars, 0.01 for cents, 100 for $000 to one place
    printed: str
    scale: int = 1       # 1000 where the page states its figures in thousands


@dataclass
class Figure:
    name: str
    amount: float
    prior: float
    page: int
    place: str
    printed: str
    check: str
    scale: int = 1
    issue: str = None    # ruling 66: the pair's difference from its printed line


@dataclass
class Result:
    document: str
    figures: dict = field(default_factory=dict)       # name → Figure, only those whose pair holds
    text_pages: int = 0
    thin_pages: list = field(default_factory=list)
    set_aside: list = field(default_factory=list)     # (pair, why)


def profile_version() -> int:
    p = profiles.profile(PROFILE)
    if p is None:
        raise LookupError(f"no document profile {PROFILE}: profiles come before readers")
    return int(p["version"])


def amount(tok: str):
    """A printed figure → float; a dash or NIL is zero; brackets or a leading minus are negative."""
    t = tok.strip()
    if re.fullmatch(r"[-–—]|nil", t, re.I):
        return 0.0
    neg = t.startswith("(") or t.startswith("-")
    digits = re.sub(r"[^\d.]", "", t)
    if not digits or digits.count(".") > 1:
        return None
    v = float(digits)
    return -v if neg else v


def columns(text: str) -> tuple:
    """(index of the reported year's column, index of the prior year's) from the page's column heads."""
    m = YEARS.search(text or "")
    if m and int(m.group(1)) < int(m.group(2)):
        return 1, 0
    return 0, 1


def _edges(rows) -> set:
    """Where the page's figure columns end: the right edge of each line's last two figures (a note number before
    them is not a column)."""
    out = set()
    for raw, m in rows:
        figs = [t for t in TOKEN.finditer(raw, m.start("figs")) if re.search(r"\d", t.group())]
        out.update(t.end() for t in figs[-2:])
    return out


def _tokens(raw: str, m, edges: set) -> list:
    """The line's figures. A dash before a figure is that figure's sign unless a figure column ends between them,
    which makes the dash a column of its own (nil)."""
    found = list(TOKEN.finditer(raw, m.start("figs")))
    out, sign = [], ""
    for i, t in enumerate(found):
        g = t.group()
        nxt = found[i + 1] if i + 1 < len(found) else None
        if re.fullmatch(r"[-–—]", g) and nxt is not None and re.search(r"\d", nxt.group()) \
                and not any(t.start() <= e < nxt.start() for e in edges):
            sign = "-"
            continue
        out.append(sign + g if sign else g)
        sign = ""
    return out


def lines(page_texts: dict) -> list:
    out = []
    for p in sorted(page_texts):
        text = page_texts[p] or ""
        cur, pri = columns(text)
        scale = 1000 if THOUSANDS.search(text) else 1
        rows = [(raw, m) for raw in text.splitlines() for m in (LINE.match(raw),) if m]
        edges = _edges(rows)
        amounts = {t.end() for raw, m in rows for t in TOKEN.finditer(raw, m.start("figs"))
                   if re.search(r"[,.]|\d{3}", t.group())}
        for raw, m in rows:
            toks = _tokens(raw, m, edges)
            first = next(TOKEN.finditer(raw, m.start("figs")))
            if len(toks) >= 2 and re.fullmatch(r"\d{1,2}", toks[0].strip()) \
                    and not any(abs(first.end() - e) <= 2 for e in amounts):
                toks = toks[1:]                          # a note number, in a column of its own left of the figures
            if len(toks) <= cur:
                continue
            vals = [amount(t) for t in toks]
            if vals[cur] is None:
                continue
            dec = re.search(r"\.(\d+)\s*\)?$", toks[cur].strip())
            step = (10 ** -len(dec.group(1)) if dec else 1) * scale
            label = re.sub(r"\s+", " ", m.group("label")).strip(" .")
            prior = vals[pri] * scale if len(vals) > pri and vals[pri] is not None else None
            out.append(Line(p, label, vals[cur] * scale, prior, step, re.sub(r"\s{2,}", "  ", raw.strip()), scale))
    return out


def _named(ls, name):
    return [x for x in ls if LABELS[name].match(x.label)]


def _signed(x: Line) -> float:
    """A line named deficit alone, printed without brackets, is a deficit."""
    if x.amount > 0 and re.search(r"deficit", x.label, re.I) and not re.search(r"surplus", x.label, re.I):
        return -x.amount
    return x.amount


def _fig(name, x: Line, check, amount_=None, issue=None) -> Figure:
    return Figure(name, x.amount if amount_ is None else amount_, x.prior, x.page, x.label, x.printed, check, x.scale,
                  issue)


def _pick(lines_: list, computed: float, value, tol):
    """The first line whose `value` is `computed` within its printed precision (`tol(line)`), else the first within
    ruling 66's tolerance, else None. A thousands statement's precision never admits $100 or more (ruling 66)."""
    for strict in (True, False):
        for x in lines_:
            if reconcile.within(computed, value(x)) and (not strict or abs(value(x) - computed) <= tol(x)):
                return x
    return None


def _tol(*xs) -> float:
    """Each line may round once at its own printed precision."""
    return max(x.step for x in xs) + 1e-6


def operating(ls: list) -> tuple:
    """({income, expenditure, surplus} figures, why-not)."""
    exp = _named(ls, "expenditure")
    if not exp:
        return {}, "no expenditure line read"
    e = exp[0]
    inc = [x for x in _named(ls, "income") if x.page in (e.page, e.page - 1) and ls.index(x) < ls.index(e)]
    if not inc:
        return {}, "no income line before the expenditure line, on its page or the one before"
    i = inc[-1]
    if e.amount < 0:      # an accounting export prints expenditure negative (New Conservatives 2025)
        e = Line(e.page, e.label, -e.amount, None if e.prior is None else -e.prior, e.step, e.printed, e.scale)
    diff = round(i.amount - e.amount, 2)
    s = _pick([s for s in _named(ls, "surplus") if s.page in (e.page, e.page + 1)], diff, _signed, lambda s: _tol(i, e, s))
    if s is not None:
        c = "income-less-expenditure"
        why = reconcile.issue(diff, _signed(s), "income less expenditure against the surplus or deficit line")
        return {"income": _fig("income", i, c, issue=why), "expenditure": _fig("expenditure", e, c, issue=why),
                "surplus": _fig("surplus", s, c, _signed(s), why)}, ""
    return {}, (f"income {i.amount:,.2f} less expenditure {e.amount:,.2f} is {diff:,.2f}, "
                "and no surplus or deficit line prints it")


def position(ls: list) -> tuple:
    """({assets, liabilities, net_assets} figures, why-not)."""
    assets = _named(ls, "assets")
    if not assets:
        return {}, "no total assets line read"
    a = assets[0]
    liab = [x for x in _named(ls, "liabilities") if x.page == a.page]
    if not liab:
        return {}, "no total liabilities line on the assets' page"
    li = liab[0]
    diff = round(a.amount - li.amount, 2)
    n = _pick([n for n in _named(ls, "net_assets") if n.page in (a.page, a.page + 1)], diff, lambda n: n.amount,
              lambda n: _tol(a, li, n))
    if n is not None:
        c = "assets-less-liabilities"
        why = reconcile.issue(diff, n.amount, "assets less liabilities against the net-assets line")
        return {"assets": _fig("assets", a, c, issue=why), "liabilities": _fig("liabilities", li, c, issue=why),
                "net_assets": _fig("net_assets", n, c, issue=why)}, ""
    return {}, f"assets {a.amount:,.2f} less liabilities {li.amount:,.2f} is {diff:,.2f}, and no net-assets line prints it"


def read_statement(data: bytes, sha256: str) -> Result:
    res = Result(sha256)
    if not data.startswith(b"%PDF"):
        res.set_aside += [(pair, "not a PDF") for pair in PAIRS]
        return res
    layer = pages.text_pages(data)
    res.thin_pages = pages.thin_pages(layer)
    texts = {p: t for p, t in layer.items() if p not in set(res.thin_pages)}
    res.text_pages = len(texts)
    if not texts:
        for pair in PAIRS:
            res.set_aside.append((pair, "no page has a text layer: the page reader's readings are the next tranche"))
        return res
    ls = lines(texts)
    for pair, fn in (("operating", operating), ("position", position)):
        figs, why = fn(ls)
        res.figures.update(figs)
        if why:
            res.set_aside.append((pair, why))
    return res
