
import socket, concurrent.futures

BASIC = [21,22,23,25,53,80,110,143,443,465,587,993,995,3306,3389,8080,8443]
EXTENDED = BASIC + [20,69,123,135,137,138,139,161,162,389,445,636,989,990,2049,2083,2087,2181,27017,25565,5432,6379]
COMMON_1K = list(dict.fromkeys(EXTENDED + list(range(1,1025)) + [1433,1521,1900,2483,3000,3128,3388,4444,5000,5601,5900,5985,5986,6000,6667,7001,8000,8081,8082,9000,9200,9300]))

def _addrinfo(target: str, port: int, prefer_v6: bool):
    fams = [socket.AF_INET6, socket.AF_INET] if prefer_v6 else [socket.AF_INET, socket.AF_INET6]
    for fam in fams:
        try:
            for info in socket.getaddrinfo(target, port, fam, socket.SOCK_STREAM):
                yield info
        except Exception:
            continue
    # last resort: let OS decide
    try:
        for info in socket.getaddrinfo(target, port, socket.AF_UNSPEC, socket.SOCK_STREAM):
            yield info
    except Exception:
        return

def _try_one(info, timeout: float = 0.5) -> bool:
    family, socktype, proto, canonname, sockaddr = info
    s = socket.socket(family, socket.SOCK_STREAM, proto)
    s.settimeout(timeout)
    try:
        s.connect(sockaddr)
        s.close()
        return True
    except Exception:
        try:
            s.close()
        except Exception:
            pass
        return False

def quick_port_check(target: str, set_name: str = "basic", timeout: float = 0.5, prefer_v6: bool = False) -> str:
    """
    IPv4/IPv6 aware connect-scan.
    set_name: basic | extended | 1k
    prefer_v6: try IPv6 addresses first when both exist.
    """
    if not target:
        return "No target"
    if set_name == "1k":
        ports = COMMON_1K[:1000]
    elif set_name == "extended":
        ports = EXTENDED
    else:
        ports = BASIC
    open_ports, closed_ports = [], []
    def check_port(p):
        # consider open if ANY resolved address is reachable
        for info in _addrinfo(target, p, prefer_v6):
            if _try_one(info, timeout):
                return p, True
        return p, False

    with concurrent.futures.ThreadPoolExecutor(max_workers=64) as ex:
        futures = [ex.submit(check_port, p) for p in ports]
        for fut in concurrent.futures.as_completed(futures):
            p, ok = fut.result()
            (open_ports if ok else closed_ports).append(p)
    open_ports.sort(); closed_ports.sort()
    def fmt(lst, max_len=60):
        if not lst: return "none"
        s = ", ".join(str(x) for x in lst[:max_len])
        if len(lst) > max_len: s += f", +{len(lst)-max_len} more"
        return s
    return f"Open: {fmt(open_ports)}\nClosed: {fmt(closed_ports)}"
