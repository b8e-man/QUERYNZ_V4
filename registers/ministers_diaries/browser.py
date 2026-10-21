"""The headed browser this lane reads the Beehive through (hard limit 6; old rulings 133, 242, 243).

www.beehive.govt.nz sits behind an Incapsula wall. A plain request with the estate's one User-Agent
gets the wall's shell, never the page (measured 21 October 2026: robots.txt and the sitemap both
answered with the 212-byte shell). A real headed Chromium on the node2 desktop, with its own user
agent and nothing patched, is served the page itself with no challenge shown (the home page, 79,770
characters, no reload). That is the case hard limit 6 allows: "a headed browser that is shown no
challenge may read a page; shown one, it stops."

What it never does: solve a CAPTCHA, log in, patch the browser, borrow cookies, rotate an address,
or reload a page the host refused. One plain reload is allowed only when the host answered 200 with
the wall's shell (its check sets a cookie and expects the request again, as a person's browser
does); a 403, 429 or 5xx, the wall's "Request unsuccessful" incident page, or a CAPTCHA frame is a
failed read, and the run stops at once.

Permission and pacing are the fetch gate's: every URL goes through `fg.check` (the position on file,
the held hosts, a publisher's request to stop) before it is asked for, and navigations are at least
`FLOOR_S` apart (the gate's own floor if slower). One page at a time, one browser, a fresh profile
per run (a profile left by a killed run crashes Chromium).

Runs as a subprocess under a Python that has Playwright (`QV4_BROWSER_PYTHON`); the v4 virtual
environment has none yet (card). Input: JSON lines on stdin, `{"url": ..., "kind": "page"|"pdf"}`.
Output: each body as `<out>/<n>.bin` and one JSON line per item on stdout:
`{"n", "url", "final", "status", "kind", "file", "bytes", "blocked", "at"}`; the last line is
`{"done": true, "stopped": "" | why}`. The pure parts (`blocked_reason`, `is_shell`) carry no
Playwright import, so the fast tier tests them.

    python registers/ministers_diaries/browser.py --out DIR [--positions DIR] < items.jsonl
"""
import argparse
import asyncio
import datetime as dt
import json
import os
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(os.path.dirname(HERE))
FLOOR_S = 5.0
SHELL_MARK = "_Incapsula_Resource"
SHELL_MAX = 5000            # the wall's shell is a few hundred bytes; a real Beehive page is tens of thousands
#: the wall's refusal page and the challenge frames, by their own landmarks (lesson:
#: a-real-page-can-carry-the-challenge-script-recognise-a-block-by-its-own-page)
BLOCK_MARKS = ("Incapsula incident ID", "Request unsuccessful", "hcaptcha.com", "google.com/recaptcha",
               "g-recaptcha", "cf-chl", "Attention Required!")
REFUSED_STATUSES = (403, 429)


def now() -> str:
    return dt.datetime.now().astimezone().isoformat(timespec="seconds")


def is_shell(status: int, body: bytes) -> bool:
    """The wall's own shell: tiny, carrying its resource script and nothing else. A real page carries
    the same script inside tens of thousands of bytes, so the mark alone is never the test."""
    return len(body) < SHELL_MAX and SHELL_MARK.encode() in body


def blocked_reason(status: int, body: bytes, kind: str = "page") -> str:
    """'' for a page or a PDF that may be landed; otherwise why this is a failed read (hard limit 6)."""
    if status in REFUSED_STATUSES or (status or 0) >= 500:
        return f"HTTP {status}: the host refused the read; a refused read is a failed read (hard limit 6)"
    if kind == "pdf" and body[:5] == b"%PDF-":
        return ""
    head = body[:20000].decode("utf-8", "replace")
    for mark in BLOCK_MARKS:
        if mark.lower() in head.lower():
            return f"the wall's refusal or a challenge ({mark!r}); a challenged read is a failed read (hard limit 6)"
    if is_shell(status, body):
        return "the wall's shell stayed after its check: no page was served (hard limit 6)"
    return ""


def reload_allowed(status: int, body: bytes, reloads: int) -> bool:
    """One plain reload, only on a 200 that is the shell. Never on a refusal."""
    return status == 200 and is_shell(status, body) and reloads == 0


async def _run(items: list, out: str, positions: str, log) -> str:
    sys.path.insert(0, REPO)
    import support.fetchgate as fg
    from playwright.async_api import async_playwright, Error as PwError
    os.makedirs(out, exist_ok=True)
    profile = tempfile.mkdtemp(prefix="profile-", dir=out)
    stopped, last = "", 0.0
    async with async_playwright() as pw:
        ctx = await pw.chromium.launch_persistent_context(
            profile, channel="chromium", headless=False, accept_downloads=True,
            # XWayland on DISPLAY: with WAYLAND_DISPLAY set Chromium picks Wayland and Playwright's launch hangs
            args=["--no-sandbox", "--disable-dev-shm-usage", "--ozone-platform=x11", "--window-size=1200,900"])
        page = await ctx.new_page()
        for n, it in enumerate(items):
            url, kind = it["url"], it.get("kind", "page")
            try:
                dec = fg.check(url, positions_dir=positions)
            except fg.Refused as exc:
                stopped = f"the fetch gate refused {url}: {exc}"
                break
            gap = last + max(FLOOR_S, dec.floor) - time.time()
            if gap > 0:
                await asyncio.sleep(gap)
            status, body, final, reloads = 0, b"", url, 0
            try:
                if kind == "pdf":
                    status, body, final = await _download(page, url, PwError)
                else:
                    resp = await page.goto(url, wait_until="domcontentloaded", timeout=60000)
                    status = resp.status if resp else 0
                    body = (await page.content()).encode()
                    if reload_allowed(status, body, reloads):
                        await page.wait_for_timeout(4000)
                        body = (await page.content()).encode()
                        if is_shell(status, body):
                            reloads = 1
                            resp = await page.reload(wait_until="domcontentloaded", timeout=60000)
                            status = resp.status if resp else status
                            await page.wait_for_timeout(2000)
                            body = (await page.content()).encode()
                    final = page.url
            except Exception as exc:  # noqa: BLE001 — a transport failure is a line and the run stops
                last = time.time()
                log({"n": n, "url": url, "final": url, "status": 0, "kind": kind, "file": "", "bytes": 0,
                     "blocked": f"transport: {type(exc).__name__}: {str(exc)[:200]}", "at": now()})
                stopped = f"transport failure on {url}"
                break
            last = time.time()
            why = blocked_reason(status, body, kind)
            if not why and fg.host_of(final) != fg.host_of(url):
                why = f"redirected to {fg.host_of(final)}: not landed"
            path = os.path.join(out, f"{n}.bin")
            if not why:
                with open(path, "wb") as f:
                    f.write(body)
            log({"n": n, "url": url, "final": final, "status": status, "kind": kind, "file": "" if why else path,
                 "bytes": len(body), "blocked": why, "reloads": reloads, "at": now()})
            if why:
                stopped = why
                break
        await ctx.close()
    return stopped


async def _download(page, url: str, PwError):
    """A PDF is reached by navigation, as a person follows a published link: Chromium either shows it
    (the response body is the file) or downloads it (the download is the file)."""
    try:
        async with page.expect_download(timeout=60000) as info:
            try:
                await page.goto(url, timeout=60000)
            except PwError as exc:
                if "Download is starting" not in str(exc):
                    raise
        dl = await info.value
        p = await dl.path()
        with open(p, "rb") as f:
            return 200, f.read(), dl.url
    except PwError:
        resp = await page.goto(url, wait_until="load", timeout=60000)
        return (resp.status if resp else 0), (await resp.body() if resp else b""), page.url


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="registers/ministers_diaries/browser.py")
    ap.add_argument("--out", required=True)
    ap.add_argument("--positions", default=None)
    a = ap.parse_args(argv)
    items = [json.loads(l) for l in sys.stdin if l.strip()]
    os.environ.setdefault("DISPLAY", ":0")

    def log(rec):
        print(json.dumps(rec, ensure_ascii=False), flush=True)
    stopped = asyncio.run(_run(items, a.out, a.positions, log))
    log({"done": True, "stopped": stopped})
    return 0


if __name__ == "__main__":
    sys.exit(main())
