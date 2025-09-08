
import re
from .utils import whois_query, is_ip

def whois(target: str) -> str:
    if not target:
        return "No target provided."
    if is_ip(target):
        try:
            res = whois_query("whois.arin.net", f"n + {target}")
            m = re.search(r"ReferralServer:\s*whois://([^\s]+)", res, re.IGNORECASE)
            if m:
                server = m.group(1).strip()
                res = whois_query(server, target)
            return res or "[WHOIS] Empty response."
        except Exception as e:
            return f"[WHOIS IP error] {e}"
    else:
        try:
            iana = whois_query("whois.iana.org", target)
            m = re.search(r"whois:\s*([^\s]+)", iana, re.IGNORECASE)
            server = (m.group(1).strip() if m else "whois.verisign-grs.com")
            res = whois_query(server, target)
            return res or "[WHOIS] Empty response."
        except Exception as e:
            return f"[WHOIS domain error] {e}"
