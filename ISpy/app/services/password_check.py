
import hashlib
import urllib.request
import urllib.error
import io
import gzip
import zipfile
import os

from .breach_check import BREACH_DIR

UA = "LookupTool/11 (k-anon)"
API_BASE = "https://api.pwnedpasswords.com/range/"

def hibp_k_anon(password: str, timeout: float = 8.0) -> tuple[bool, int]:
    """
    Uses HaveIBeenPwned PwnedPasswords k-anonymity API.
    Sends only SHA1 prefix (5 chars). Returns (found, count).
    """
    if not password:
        return False, 0
    sha1 = hashlib.sha1(password.encode("utf-8")).hexdigest().upper()
    prefix, suffix = sha1[:5], sha1[5:]
    url = API_BASE + prefix
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = resp.read().decode("utf-8", "ignore")
    except Exception:
        return False, 0
    count = 0
    found = False
    for line in body.splitlines():
        if ":" not in line: continue
        suf, cnt = line.split(":", 1)
        if suf.strip().upper() == suffix:
            try:
                count = int(cnt.strip())
            except ValueError:
                count = 0
            found = True
            break
    return found, count

def _iter_lines(path: str):
    lower = path.lower()
    try:
        if lower.endswith(".gz"):
            with gzip.open(path, "rt", encoding="utf-8", errors="ignore") as f:
                for line in f: yield line
        elif lower.endswith(".zip"):
            with zipfile.ZipFile(path, "r") as z:
                for name in z.namelist():
                    if name.lower().endswith((".txt",)):
                        with z.open(name) as fbin:
                            for line in io.TextIOWrapper(fbin, encoding="utf-8", errors="ignore"):
                                yield line
        else:
            with open(path, "r", encoding="utf-8", errors="ignore") as f:
                for line in f: yield line
    except Exception:
        return

def local_password_hit(password: str, limit_files: list[str] | None = None, max_scan_files: int = 50) -> tuple[bool, str]:
    """
    Streams through local lists in BREACH_DIR to see if the exact password appears.
    Returns (found, source_file) first match only (to limit scanning time).
    Only checks plaintext .txt (or .txt in .zip/.gz). Keeps privacy local.
    """
    if not password:
        return False, ""
    pwd = password.strip()
    base = BREACH_DIR
    if not os.path.isdir(base):
        return False, ""
    files = limit_files if limit_files else sorted(os.listdir(base))
    scanned = 0
    for name in files:
        if scanned >= max_scan_files:
            break
        if not name.lower().endswith((".txt", ".txt.gz", ".zip")):
            continue
        scanned += 1
        path = os.path.join(base, name)
        for line in _iter_lines(path) or []:
            if line.strip() == pwd:
                return True, name
    return False, ""

