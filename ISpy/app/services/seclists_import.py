
import os
import urllib.request
import urllib.error
from urllib.parse import urlparse
import time

from .breach_check import BREACH_DIR

# Curated SecLists presets (balanced size; good starters)
# Users can paste any raw GitHub URLs as well.
PRESETS = [
    {
        "label": "Passwords • 10k-most-common.txt",
        "url": "https://raw.githubusercontent.com/danielmiessler/SecLists/master/Passwords/Common-Credentials/10k-most-common.txt",
    },
    {
        "label": "Passwords • rockyou-75.txt (subset)",
        "url": "https://raw.githubusercontent.com/danielmiessler/SecLists/master/Passwords/Leaked-Databases/rockyou-75.txt",
    },
    {
        "label": "Passwords • xato 100k (subset)",
        "url": "https://raw.githubusercontent.com/danielmiessler/SecLists/master/Passwords/xato-net-10-million-passwords-100000.txt",
    },
    {
        "label": "Usernames • top-usernames-shortlist.txt",
        "url": "https://raw.githubusercontent.com/danielmiessler/SecLists/master/Usernames/top-usernames-shortlist.txt",
    },
    {
        "label": "Usernames • names.txt",
        "url": "https://raw.githubusercontent.com/danielmiessler/SecLists/master/Usernames/Names/names.txt",
    },
]

UA = "LookupTool/12 (SecLists importer)"

def get_presets():
    return list(PRESETS)

def _safe_name(url: str) -> str:
    base = os.path.basename(urlparse(url).path) or ("seclist_" + str(int(time.time())) + ".txt")
    if not any(base.lower().endswith(ext) for ext in (".txt",".csv",".json",".gz",".zip",".lst",".log")):
        base += ".txt"
    # prefix for clarity
    return "seclists_" + base

def download_files(urls: list[str]) -> list[tuple[str, str]]:
    """
    Downloads each URL into BREACH_DIR. Returns list of (filename, status)
    where status is 'ok' or an error message.
    """
    os.makedirs(BREACH_DIR, exist_ok=True)
    results = []
    for url in urls:
        url = url.strip()
        if not url:
            continue
        name = _safe_name(url)
        dest = os.path.join(BREACH_DIR, name)
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=30) as resp, open(dest, "wb") as f:
                # stream in chunks
                while True:
                    chunk = resp.read(65536)
                    if not chunk:
                        break
                    f.write(chunk)
            results.append((name, "ok"))
        except urllib.error.HTTPError as e:
            results.append((name, f"HTTP {e.code}"))
        except Exception as e:
            results.append((name, f"error: {e}"))
    return results
