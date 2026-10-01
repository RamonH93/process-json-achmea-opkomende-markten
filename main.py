import datetime
import json
import os
import re
import sys

import requests

BASE = "https://www.achmeainvestmentmanagement.nl"
PAGE = f"{BASE}/particulier/beleggingsfondsen/koersen"
API = f"{BASE}/apiproxy/FundRates/RetrieveAllRatesForFundsInFundGroup"
FUND_GROUP = "ODV"
FUND_CODE = "GOA"  # Achmea opkomende markten aandelen fonds A
OUT = "AchmeaOpkomendeMarkten.json"
STALE_DAYS = 7  # warn if the newest rate is older than this

# Request body as sent by the browser (confirmed via devtools).
PAYLOAD = {"fundGroupCode": FUND_GROUP}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:156.0) "
                  "Gecko/20100101 Firefox/156.0",
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": PAGE,
    "Origin": BASE,
    "x-aps-administratie-id": "900",
}

TOKEN_PATTERNS = [
    r'name="__RequestVerificationToken"[^>]*value="([^"]+)"',
    r'value="([^"]+)"[^>]*name="__RequestVerificationToken"',
    r'__RequestVerificationToken["\']?\s*[:=]\s*["\']([^"\']+)["\']',
]

# Never print these response headers: they carry session cookies.
REDACT_HEADERS = {"set-cookie", "cookie"}
BODY_SNIPPET = 1500

IN_GHA = os.environ.get("GITHUB_ACTIONS") == "true"


# --- logging helpers -------------------------------------------------------

def _escape(msg):
    """Escape for GitHub Actions workflow commands (multi-line annotations)."""
    return msg.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")


def mask(value):
    """Hide a secret-ish value in GitHub Actions logs."""
    if IN_GHA and value:
        print(f"::add-mask::{value}", flush=True)


def warn(title, msg):
    if IN_GHA:
        print(f"::warning title={title}::{_escape(msg)}", flush=True)
    else:
        print(f"WARNING [{title}]: {msg}", file=sys.stderr)


def dump_response(r, label):
    """Print status, safe headers and a body snippet in a collapsible group."""
    lines = [
        f"{label}",
        f"  {r.request.method} {r.url}",
        f"  Status: {r.status_code} {r.reason}",
        f"  Elapsed: {r.elapsed.total_seconds():.2f}s",
        "  Headers:",
    ]
    for k, v in r.headers.items():
        if k.lower() not in REDACT_HEADERS:
            lines.append(f"    {k}: {v}")
    title = re.search(r"<title[^>]*>(.*?)</title>", r.text or "", re.I | re.S)
    if title:
        lines.append(f"  HTML <title>: {title.group(1).strip()}")
    body = (r.text or "").strip()
    lines.append(f"  Body ({len(body)} chars, first {BODY_SNIPPET}):")
    lines.append(body[:BODY_SNIPPET] or "    <empty>")

    if IN_GHA:
        print(f"::group::{label}", flush=True)
    print("\n".join(lines), file=sys.stderr, flush=True)
    if IN_GHA:
        print("::endgroup::", flush=True)


def fail(step, msg, response=None):
    """Log a detailed error (annotation in GitHub Actions) and exit 1."""
    if response is not None:
        dump_response(response, f"Response details ({step})")
        msg = f"{msg}\nHTTP {response.status_code} from {response.url}"
    if IN_GHA:
        print(f"::error title={step}::{_escape(msg)}", flush=True)
    print(f"ERROR [{step}]: {msg}", file=sys.stderr, flush=True)
    sys.exit(1)


# --- main flow -------------------------------------------------------------

def get_token(session):
    step = "Load rates page"
    try:
        r = session.get(PAGE, headers=HEADERS, timeout=30)
    except requests.RequestException as e:
        fail(step, f"Network error loading {PAGE}: {type(e).__name__}: {e}")
    if not r.ok:
        fail(step, "Rates page did not return 2xx.", r)

    for pattern in TOKEN_PATTERNS:
        m = re.search(pattern, r.text)
        if m:
            token = m.group(1)
            mask(token)
            print(f"Token found (pattern {TOKEN_PATTERNS.index(pattern) + 1}), "
                  f"cookies set: {', '.join(session.cookies.keys()) or 'none'}")
            return token

    # Help diagnose a changed page: show where the token name appears, if at all.
    hits = [m.start() for m in re.finditer("RequestVerificationToken", r.text)]
    context = "\n".join(
        r.text[max(0, i - 150):i + 150].replace("\n", " ") for i in hits[:3]
    ) or "String 'RequestVerificationToken' does not occur in the page."
    fail(step, "No __RequestVerificationToken matched any pattern. "
               "The page layout may have changed.\nContext:\n" + context, r)


def fetch_rates(session, token):
    step = "Fetch rates API"
    headers = dict(HEADERS, **{"__RequestVerificationToken": token})
    try:
        r = session.post(API, json=PAYLOAD, headers=headers, timeout=30)
    except requests.RequestException as e:
        fail(step, f"Network error calling {API}: {type(e).__name__}: {e}")

    if not r.ok:
        hint = {
            400: "Likely anti-forgery validation failed (token/cookie mismatch).",
            403: "Likely blocked by bot protection (F5) or WAF.",
            503: "Proxy/backend unavailable, or request blocked upstream.",
        }.get(r.status_code, "Unexpected status.")
        fail(step, f"API returned an error. {hint}", r)

    try:
        return r.json()
    except ValueError as e:
        fail(step, f"Response is not valid JSON ({e}). "
                   f"Content-Type: {r.headers.get('content-type')}", r)


def main():
    session = requests.Session()
    token = get_token(session)
    data_remote = fetch_rates(session, token)

    step = "Parse response"
    funds = data_remote.get("funds") if isinstance(data_remote, dict) else None
    if not funds:
        fail(step, "JSON has no 'funds' list. Top-level keys: "
                   f"{list(data_remote)[:20] if isinstance(data_remote, dict) else type(data_remote).__name__}")

    fund = next((f for f in funds if f.get("fundCode") == FUND_CODE), None)
    if not fund:
        codes = ", ".join(str(f.get("fundCode")) for f in funds)
        fail(step, f"Fund {FUND_CODE} not in response. Available codes: {codes}")
    if not fund.get("rates"):
        fail(step, f"Fund {FUND_CODE} has no rates.")

    by_date = {}
    for i, item in enumerate(fund["rates"]):
        try:
            date = item["fundRateDate"][:10]
            datetime.date.fromisoformat(date)
            by_date[date] = str(item["fundRate"])
        except (KeyError, TypeError, ValueError) as e:
            fail(step, f"Unexpected rate record at index {i}: {item!r} ({e})")

    rates = [{"Date": d, "CloseQuote": q} for d, q in sorted(by_date.items())]
    newest = rates[-1]["Date"]
    age = (datetime.date.today() - datetime.date.fromisoformat(newest)).days
    if age > STALE_DAYS:
        warn("Stale data", f"Newest {FUND_CODE} rate is {newest} ({age} days old).")

    data_out = {
        "fund": fund.get("fundTitle", FUND_CODE),
        "lastUpdated": datetime.datetime.now().strftime("%Y-%m-%d %H:%M"),
        "rates": rates,
    }

    try:
        with open(OUT, "w") as f:
            json.dump(data_out, f, indent=4)
    except OSError as e:
        fail("Write output", f"Could not write {OUT}: {e}")

    dupes = len(fund["rates"]) - len(by_date)
    print(f"OK: {len(rates)} rates written to {OUT} "
          f"(range {rates[0]['Date']} to {newest}, {dupes} duplicates removed)")


if __name__ == "__main__":
    main()
