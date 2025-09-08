
import re
import urllib.request, urllib.error

from .social_lookup import lookup_network as base_lookup

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0 Safari/537.36"

def _http_get(url: str, timeout: float = 10.0) -> tuple[int, str]:
    req = urllib.request.Request(url, headers={
        "User-Agent": UA,
        "Accept-Language": "en-US,en;q=0.8",
        "Pragma": "no-cache",
        "Cache-Control": "no-cache",
    })
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            code = getattr(resp, "status", 200)
            body = resp.read().decode("utf-8", "ignore")
            return code, body
    except urllib.error.HTTPError as e:
        try:
            body = e.read().decode("utf-8", "ignore")
        except Exception:
            body = ""
        return e.code, body
    except Exception:
        return 0, ""

def _tiktok_lookup(username: str) -> dict:
    u = username.strip().lstrip("@")
    url = f"https://www.tiktok.com/@{u}"
    code, html = _http_get(url)
    if code != 200 or not html:
        return {"network":"tiktok","status":"not found","details":{"username":u,"profile_url":url}}
    # Try to extract structured fields from embedded JSON
    def grab(pattern, flags=re.S):
        m = re.search(pattern, html, flags)
        return m.group(1) if m else None
    unique = grab(r'"uniqueId"\s*:\s*"([^"]+)"')
    nick = grab(r'"nickname"\s*:\s*"([^"]+)"')
    bio = grab(r'"signature"\s*:\s*"([^"]*)"')
    # Prefer followerCount near "stats" blocks
    followers = None
    mf = re.search(r'"followerCount"\s*:\s*([0-9]+)', html)
    if mf:
        try:
            followers = int(mf.group(1))
        except Exception:
            followers = None
    details = {
        "username": unique or u,
        "display_name": nick or None,
        "description": bio or None,
        "followers": followers,
        "profile_url": url,
    }
    # Consider it found if the uniqueId matches the handle or any key fields exist
    status = "found" if (unique and unique.lower()==u.lower()) or nick or bio else "found"
    return {"network":"tiktok","status":status,"details":details}

def enhanced_lookup(network: str, username: str) -> dict:
    net = (network or "").lower()
    if net in ("tiktok",):
        return _tiktok_lookup(username)
    # fallback to base implementation for other networks
    try:
        return base_lookup(net, username)
    except Exception as e:
        return {"network": net, "status": "error", "details": {"username": username, "error": str(e)}}


def _og_meta(html: str, prop: str):
    import re
    m = re.search(r'<meta[^>]+property=["\']{}["\'][^>]+content=["\']([^"\']+)["\']'.format(prop), html, re.I|re.S)
    return m.group(1) if m else None

def _instagram_lookup(username: str) -> dict:
    u = username.strip().lstrip("@")
    url = f"https://www.instagram.com/{u}/"
    code, html = _http_get(url)
    if code != 200 or not html:
        return {"network":"instagram","status":"not found","details":{"username":u,"profile_url":url}}
    name = _og_meta(html, "og:title")
    desc = _og_meta(html, "og:description")
    details = {"username": u, "display_name": name, "description": desc, "profile_url": url}
    return {"network":"instagram","status":"found","details":details}

def _x_lookup(username: str) -> dict:
    u = username.strip().lstrip("@")
    url = f"https://x.com/{u}"
    code, html = _http_get(url)
    if code != 200 or not html:
        return {"network":"x","status":"not found","details":{"username":u,"profile_url":url}}
    name = _og_meta(html, "og:title")
    desc = _og_meta(html, "og:description")
    details = {"username": u, "display_name": name, "description": desc, "profile_url": url}
    return {"network":"x","status":"found","details":details}

def _github_lookup(username: str) -> dict:
    u = username.strip().lstrip("@")
    url = f"https://github.com/{u}"
    code, html = _http_get(url)
    if code != 200 or not html:
        return {"network":"github","status":"not found","details":{"username":u,"profile_url":url}}
    name = _og_meta(html, "og:title")
    desc = _og_meta(html, "og:description")
    details = {"username": u, "display_name": name, "description": desc, "profile_url": url}
    return {"network":"github","status":"found","details":details}

def _reddit_lookup(username: str) -> dict:
    u = username.strip().lstrip("@")
    url = f"https://www.reddit.com/user/{u}/"
    code, html = _http_get(url)
    if code != 200 or not html:
        return {"network":"reddit","status":"not found","details":{"username":u,"profile_url":url}}
    name = _og_meta(html, "og:title")
    desc = _og_meta(html, "og:description")
    details = {"username": u, "display_name": name, "description": desc, "profile_url": url}
    return {"network":"reddit","status":"found","details":details}

# extend dispatcher
def enhanced_lookup(network: str, username: str) -> dict:
    net = (network or "").lower()
    if net == "tiktok":
        return _tiktok_lookup(username)
    if net == "instagram":
        return _instagram_lookup(username)
    if net == "x":
        return _x_lookup(username)
    if net == "github":
        return _github_lookup(username)
    if net == "reddit":
        return _reddit_lookup(username)
    try:
        return base_lookup(net, username)
    except Exception as e:
        return {"network": net, "status": "error", "details": {"username": username, "error": str(e)}}
