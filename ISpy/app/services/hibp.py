
import time, json, urllib.request, urllib.error, urllib.parse

HIBP_API = "https://haveibeenpwned.com/api/v3/breachedaccount/{account}?truncateResponse=false"

def breached_account(account: str, api_key: str):
    """
    Returns (ok, data) where data is list of breaches (names) if ok, else error message.
    We throttle ~1.7s between calls to be polite.
    """
    if not api_key:
        return False, "HIBP API key is empty."
    url = HIBP_API.format(account=urllib.parse.quote(account))
    req = urllib.request.Request(url, headers={
        "hibp-api-key": api_key,
        "User-Agent": "ISpy/0.24.0"
    })
    try:
        time.sleep(1.7)
        with urllib.request.urlopen(req, timeout=15) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode("utf-8"))
                names = [b.get("Name","(unknown)") for b in (data if isinstance(data, list) else [])]
                return True, names
            elif resp.status == 404:
                return True, []  # not pwned
            else:
                return False, f"HTTP {resp.status}"
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return True, []
        if e.code == 429:
            return False, "Rate limited by HIBP (HTTP 429). Try again later."
        return False, f"HTTP {e.code}"
    except Exception as e:
        return False, str(e)
