
import re
from urllib.parse import quote, urlparse
import urllib.request, urllib.error

UA = "LookupTool/13 SocialSearch"
DDG_HTML = "https://duckduckgo.com/html/?q={query}&kl=wt-wt"

# Map network -> domain root to filter candidates
NETWORK_DOMAINS = {
    "instagram": "instagram.com",
    "facebook": "facebook.com",
    "x": "x.com",
    "twitter": "twitter.com",
    "tiktok": "tiktok.com",
    "youtube": "youtube.com",
    "reddit": "reddit.com",
    "github": "github.com",
    "twitch": "twitch.tv",
    "pinterest": "pinterest.com",
    "linkedin": "linkedin.com",
    "snapchat": "snapchat.com",
}

A_TAG = re.compile(r'<a[^>]+href=["\'](?P<href>[^"\']+)["\'][^>]*>(?P<text>.*?)</a>', re.I)
TAG_RE = re.compile(r"<[^>]+>")  # strip tags

def _fetch(query: str, timeout: float = 12.0) -> str:
    url = DDG_HTML.format(query=quote(query))
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read().decode("utf-8", "ignore")

def _clean_text(html_text: str) -> str:
    return TAG_RE.sub("", html_text or "").strip()

def _extract_candidates(html: str, network: str | None = None) -> list[dict]:
    out = []
    for m in A_TAG.finditer(html):
        href = m.group("href")
        txt = _clean_text(m.group("text"))
        if not href.startswith("http"):
            continue
        host = urlparse(href).netloc.lower()
        # Filter by domains
        if network:
            dom = NETWORK_DOMAINS.get(network)
            if not dom or dom not in host:
                continue
        else:
            # accept any known domain
            if not any(dom in host for dom in NETWORK_DOMAINS.values()):
                continue
        out.append({"url": href, "text": txt})
    # Dedup by URL
    seen = set()
    uniq = []
    for c in out:
        if c["url"] in seen: continue
        seen.add(c["url"])
        uniq.append(c)
    return uniq

def search_profiles(name_or_user: str, network: str | None = None, max_results: int = 25) -> list[dict]:
    # SIMILAR NAME VARIANTS: try quoted, spaceless, underscores, dots
    """
    Returns a list of candidate profiles from DuckDuckGo HTML results.
    Each item: {url, text, network?, username?}
    """
    q = name_or_user.strip()
    if not q:
        return []
    # Build queries
    queries = []
    if network:
        dom = NETWORK_DOMAINS.get(network,'')
        base = [q, f'"{q}"']
        if ' ' in q:
            base += [q.replace(' ', ''), q.replace(' ', '_'), q.replace(' ', '.')]
        for b in base:
            queries.append(f"site:{dom} {b}")
    else:
        # General: add common domains and a broad query
        base = [q, f'"{q}"']
        if ' ' in q:
            base += [q.replace(' ', ''), q.replace(' ', '_'), q.replace(' ', '.')]
        for b in base:
            queries.append(b + " site:instagram.com OR site:twitter.com OR site:x.com OR site:github.com OR site:linkedin.com")
        queries.append(q + " site:youtube.com OR site:tiktok.com OR site:reddit.com OR site:twitch.tv")
        queries.append(q + " site:pinterest.com OR site:facebook.com OR site:snapchat.com")
    results = []
    for qq in queries:
        try:
            html = _fetch(qq)
            results.extend(_extract_candidates(html, network=network))
        except Exception:
            continue
        if len(results) >= max_results:
            break
    # Post-process: infer network from URL and guess username by path
    for r in results:
        host = urlparse(r["url"]).netloc.lower()
        r["network"] = None
        for n, dom in NETWORK_DOMAINS.items():
            if dom in host:
                r["network"] = "x" if n == "twitter" else n
                break
        path = urlparse(r["url"]).path
        parts = [p for p in path.split("/") if p]
        # heuristics per site
        user = None
        if r["network"] in ("instagram","facebook","github","twitch","pinterest","linkedin","snapchat","x"):
            user = parts[-1] if parts else None
        elif r["network"] == "tiktok":
            if parts and parts[0].startswith("@"):
                user = parts[0][1:]
        elif r["network"] == "reddit":
            # /user/<name>/
            if len(parts) >= 2 and parts[0] in ("user","u"):
                user = parts[1]
        elif r["network"] == "youtube":
            # /@user or /c/<name> or /channel/<id>
            if parts:
                if parts[0].startswith("@"):
                    user = parts[0][1:]
                elif len(parts) >= 2 and parts[0] in ("c","channel","user"):
                    user = parts[1]
        r["username"] = user
    # Trim
    results = results[:max_results]
    return results


from .social_lookup import generate_variants
from .social_enhanced import enhanced_lookup

def direct_probe_many(name_or_user: str, network: str | None = None, max_total: int = 25) -> list[dict]:
    """
    Try direct profile URLs by running lookup_network across variants and networks.
    Returns list of {network, username, url} for confirmed profiles.
    """
    targets = ["instagram","facebook","x","tiktok","youtube","reddit","github","twitch","pinterest","linkedin","snapchat"]
    nets = targets if not network or network=="all" else [network]
    out = []
    seen = set()
    for net in nets:
        for u in generate_variants(name_or_user):
            res = enhanced_lookup(net, u)
            if res.get("status") == "found":
                url = res.get("details",{}).get("profile_url","")
                key = (net, res.get("details",{}).get("username", u), url)
                if key in seen: 
                    continue
                seen.add(key)
                out.append({"network": net, "username": key[1], "url": url})
                if len(out) >= max_total:
                    return out
    return out
