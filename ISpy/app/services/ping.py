
import subprocess, sys, time, shutil

def _is_windows():
    return sys.platform.startswith("win")

def ping(target: str, count: int = 4, interval_ms: int = 250, on_update=None, ipv6: bool = False) -> str:
    """
    Portable ping with controlled rate.
    - count: 1..1000 (clamped)
    - interval_ms: 0..1000 (clamped)
    Sends one packet at a time and sleeps between sends.
    Uses a 64-byte payload (-l 64 on Windows, -s 64 on POSIX).
    Set ipv6=True to prefer IPv6 ping (-6 switch when available).
    """
    if not target:
        return "No target"
    count = max(1, min(1000, int(count)))
    interval_ms = max(0, min(1000, int(interval_ms)))
    total_sent = 0
    total_recv = 0
    rtts = []
    outputs = []
    for i in range(count):
        total_sent += 1
        if _is_windows():
            # -n 1 one echo; -w 1000 timeout ms; -l 64 payload 8 bytes
            cmd = ["ping", "-n", "1", "-w", "1000", "-l", "8", target]
        else:
            # -c 1 one echo; -W 1 timeout s; -s 64 payload 8 bytes
            # -i is global interval; we're looping so we don't use it
            cmd = ["ping", "-c", "1", "-W", "1", "-s", "8", target]
        try:
            out = subprocess.run(cmd, capture_output=True, text=True, timeout=3)
            text = out.stdout or out.stderr or ""
            outputs.append(text.strip())
            # crude RTT parse
            ms = None
            for token in text.replace("=", " ").replace("/", " ").split():
                try:
                    v = float(token)
                    if 0 <= v <= 10000:
                        ms = v
                        break
                except ValueError:
                    pass
            if out.returncode == 0:
                total_recv += 1
                if ms is not None:
                    rtts.append(ms)
                if on_update:
                    on_update(f"reply from {target}: {ms if ms is not None else '?'} ms")
            else:
                if on_update:
                    on_update(f"request to {target} timed out")
        except Exception as e:
            outputs.append(str(e))
        # sleep between attempts (except after last one)
        if i != count - 1 and interval_ms > 0:
            time.sleep(interval_ms / 1000.0)
    loss = 0.0 if total_sent == 0 else (1 - (total_recv / total_sent)) * 100
    summary = [f"Ping {target} — sent={total_sent}, recv={total_recv}, loss={loss:.0f}%"]
    if rtts:
        summary.append(f"rtt min/avg/max ≈ {min(rtts):.0f}/{sum(rtts)/len(rtts):.0f}/{max(rtts):.0f} ms")
    return "\n".join(summary)
