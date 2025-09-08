
import json, socket
from .utils import http_get

def ip_info(target: str) -> str:
    if not target:
        return "No IP or hostname provided."
    try:
        ip = socket.gethostbyname(target)
    except Exception:
        ip = target
    url = f"http://ip-api.com/json/{ip}?fields=status,message,continent,country,regionName,city,zip,lat,lon,timezone,isp,org,as,query"
    code, data = http_get(url, timeout=8.0)
    if code != 200:
        return f"[ip-api error] HTTP {code or '0'}"
    try:
        obj = json.loads(data.decode("utf-8", "ignore"))
    except Exception:
        return "[ip-api error] Invalid JSON"
    if obj.get("status") != "success":
        return f"[ip-api] {obj.get('message','Unknown error')}"
    lines = [
        f"Query: {obj.get('query')}",
        f"Continent/Country: {obj.get('continent')}, {obj.get('country')}",
        f"Region/City/ZIP: {obj.get('regionName')}, {obj.get('city')} {obj.get('zip')}",
        f"Lat/Lon: {obj.get('lat')}, {obj.get('lon')}",
        f"Timezone: {obj.get('timezone')}",
        f"ISP/Org/AS: {obj.get('isp')} / {obj.get('org')} / {obj.get('as')}",
    ]
    return "\n".join(lines)
