
import urllib.request
import urllib.error
import socket

DEFAULT_UA = "Mozilla/5.0 (compatible; LookupTool/1.0; +https://example.invalid)"

def http_get(url: str, timeout: float = 8.0, headers: dict | None = None) -> tuple[int, bytes]:
    req = urllib.request.Request(url, headers=headers or {"User-Agent": DEFAULT_UA})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            code = resp.getcode()
            data = resp.read()
            return code, data
    except urllib.error.HTTPError as e:
        return e.code, e.read() if e.fp else b""
    except Exception:
        return 0, b""

def whois_query(server: str, query: str, port: int = 43, timeout: float = 10.0) -> str:
    data = ""
    with socket.create_connection((server, port), timeout=timeout) as s:
        s.sendall((query + "\r\n").encode("utf-8", "ignore"))
        s.shutdown(socket.SHUT_WR)
        chunks = []
        while True:
            buf = s.recv(4096)
            if not buf:
                break
            chunks.append(buf)
        data = b"".join(chunks).decode("utf-8", "ignore")
    return data

def is_ip(addr: str) -> bool:
    try:
        socket.inet_pton(socket.AF_INET, addr)
        return True
    except OSError:
        pass
    try:
        socket.inet_pton(socket.AF_INET6, addr)
        return True
    except OSError:
        return False
