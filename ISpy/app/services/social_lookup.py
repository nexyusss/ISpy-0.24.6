
import re
from html import unescape
from urllib.parse import quote
from .utils import http_get, DEFAULT_UA

# Map of supported networks to profile URL formats
SOCIAL_BASES = {
    "instagram": "https://www.instagram.com/{username}/",
    "facebook": "https://www.facebook.com/{username}/",
    "x": "https://x.com/{username}",
    "twitter": "https://twitter.com/{username}",  # alias -> normalized to x
    "tiktok": "https://www.tiktok.com/@{username}",
    "youtube": "https://www.youtube.com/@{username}",
    "reddit": "https://www.reddit.com/user/{username}/",
    "github": "https://github.com/{username}",
    "twitch": "https://www.twitch.tv/{username}",
    "pinterest": "https://www.pinterest.com/{username}/",
    "linkedin": "https://www.linkedin.com/in/{username}/",
    "snapchat": "https://www.snapchat.com/add/{username}",
}

# Lightweight HTML helpers (no external deps)
_META_OG = re.compile(r'<meta[^>]+property=["\']og:(?P<key>title|description|site_name)["\'][^>]+content=["\'](?P<val>[^"\']*)["\']', re.I)
_META_NAME = re.compile(r'<meta[^>]+name=["\']description["\'][^>]+content=["\'](?P<val>[^"\']*)["\']', re.I)
_TITLE = re.compile(r'<title[^>]*>(?P<val>.*?)</title>', re.I|re.S)
_CANON = re.compile(r'<link[^>]+rel=["\']canonical["\'][^>]+href=["\'](?P<val>[^"\']+)["\']', re.I)
_JSONLD = re.compile(r'<script[^>]+type=["\']application/ld\+json["\'][^>]*>(?P<val>.*?)</script>', re.I|re.S)

_NUM_FOLLOWERS = re.compile(r'(?:(?:Followers|followers|Follower|Seguidores|Abonn[ée]s))[^0-9]{0,10}([0-9][0-9,\.]*)')

def _extract_meta(html: str) -> dict:
    out = {}
    for m in _META_OG.finditer(html):
        out[f'og:{m.group("key").lower()}'] = unescape(m.group("val"))
    m = _META_NAME.search(html)
    if m:
        out["meta:description"] = unescape(m.group("val"))
    t = _TITLE.search(html)
    if t:
        out["title"] = unescape(t.group("val").strip())
    c = _CANON.search(html)
    if c:
        out["canonical"] = unescape(c.group("val"))
    # Try to parse first JSON-LD block (best-effort)
    jl = _JSONLD.search(html)
    if jl:
        out["jsonld"] = jl.group("val")
    # Followers heuristic
    nf = _NUM_FOLLOWERS.search(html)
    if nf:
        out["followers"] = nf.group(1)
    return out

def _normalize_net(net: str) -> str:
    n = net.lower().strip()
    if n == "twitter": n = "x"
    return n

def _build_url(net: str, username: str) -> str:
    net = _normalize_net(net)
    base = SOCIAL_BASES.get(net)
    return base.format(username=quote(username)) if base else ""

def _binary_from_code(code: int) -> str:
    if code in (200, 301, 302, 303, 307, 308):
        return "found"
    if code in (404, 410):
        return "not found"
    return "not found"  # indeterminate treated as not found but info will show the code

def _extract_username_from_canonical(url: str) -> str | None:
    # Try to pull the username-ish last segment
    try:
        path = url.split("://",1)[1].split("/",1)[1]
        parts = [p for p in path.split("/") if p]
        if parts:
            last = parts[-1]
            if last.startswith("@"): last = last[1:]
            return last
    except Exception:
        return None
    return None

def lookup_network(network: str, username: str) -> dict:
    net = _normalize_net(network)
    if net not in SOCIAL_BASES:
        return {"network": network, "status": "not found", "url": "", "info": f"unsupported network: {network}"}
    if not username:
        return {"network": net, "status": "not found", "url": "", "info": "empty username"}

    url = _build_url(net, username)
    headers = {"User-Agent": DEFAULT_UA, "Accept": "text/html"}
    code, data = http_get(url, timeout=12.0, headers=headers)
    status = _binary_from_code(code)

    details = {"username": username, "display_name": "", "description": "", "followers": "", "profile_url": url}
    info = f"{net} HTTP {code or 0} — {url}"

    if code and data:
        try:
            html = data.decode("utf-8", "ignore")
        except Exception:
            html = ""
        meta = _extract_meta(html)
        if meta.get("og:title"):
            details["display_name"] = meta["og:title"]
        elif meta.get("title"):
            details["display_name"] = meta["title"]
        if meta.get("og:description"):
            details["description"] = meta["og:description"]
        elif meta.get("meta:description"):
            details["description"] = meta["meta:description"]
        if meta.get("followers"):
            details["followers"] = meta["followers"]
        if meta.get("canonical"):
            maybe_user = _extract_username_from_canonical(meta["canonical"])
            if maybe_user:
                details["username"] = maybe_user

    return {
        "network": net,
        "status": status,
        "url": url,
        "details": details,
        "info": info,
    }

def check_single(network: str, username: str):
    res = lookup_network(network, username)
    # Keep legacy return of (status, info) but provide dict in 'res' for advanced printing if caller wants
    return res["status"], f"{res['network']}: {res['status']} — {res['details'].get('display_name') or res['details'].get('username','')} — {res['details']['profile_url']}"

def check_all(username: str):
    nets = ["instagram","facebook","x","tiktok","youtube","reddit","github","twitch","pinterest","linkedin","snapchat"]
    results = []
    for n in nets:
        results.append(lookup_network(n, username))
    return results


def generate_variants(username: str) -> list[str]:
    u = username.strip()
    base = set([u, u.lower(), u.replace(".", "").replace("_", "").replace("-", ""), u.replace(" ", "")])
    if "_" in u: base.add(u.replace("_",""))
    if "." in u: base.add(u.replace(".",""))
    # Add common suffix/prefix patterns
    pieces = set()
    for b in list(base):
        for suf in ["", "_", ".", "official", "real", "1", "01", "001"]:
            pieces.add(f"{b}{suf}")
            pieces.add(f"{suf}{b}" if suf and not suf.isdigit() else f"{b}")
    return [v for v in pieces if v]
