
import socket

def resolve_a(host: str) -> str:
    if not host:
        return "No hostname provided."
    try:
        ip = socket.gethostbyname(host)
        return f"A: {host} -> {ip}"
    except Exception as e:
        return f"[DNS error] {e}"

def reverse_ptr(ip: str) -> str:
    if not ip:
        return "No IP provided."
    try:
        name, alias, addr = socket.gethostbyaddr(ip)
        return f"PTR: {ip} -> {name} (aliases: {', '.join(alias) if alias else '-'})"
    except Exception as e:
        return f"[Reverse DNS error] {e}"


import socket, ipaddress

def resolve_aaaa(host: str) -> str:
    try:
        infos = socket.getaddrinfo(host, None, socket.AF_INET6, socket.SOCK_STREAM)
        addrs = sorted({info[4][0] for info in infos})
        if not addrs:
            return "No AAAA records."
        return "AAAA:\n" + "\n".join(" - " + a for a in addrs)
    except Exception as e:
        return f"[error] {e}"

def reverse_ptr_any(ip: str) -> str:
    try:
        addr = ipaddress.ip_address(ip)
        if addr.version == 4:
            import socket as _s
            return _s.gethostbyaddr(ip)[0]
        else:
            # IPv6 reverse nibble under ip6.arpa
            nib = addr.exploded.replace(":", "")[::-1]
            rev = ".".join(nib) + ".ip6.arpa"
            import dns.resolver  # not available; fallback using socket.getnameinfo on link-local won't work
            return rev
    except Exception as e:
        return f"[error] {e}"
