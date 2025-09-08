
import os, sys, subprocess, shutil, time, datetime

CAP_PROC = None
CAP_FILE = None
CAP_TOOL = None
CAP_IFACE = None

def list_connections() -> str:
    """Return a one-shot snapshot of current TCP/UDP connections (cross-platform)."""
    if sys.platform.startswith("win"):
        # Use netstat -ano
        try:
            out = subprocess.run(["netstat", "-ano"], capture_output=True, text=True, timeout=5).stdout
            return out.strip() or "(no connections)"
        except Exception as e:
            return f"[error] {e}"
    else:
        # Linux/mac: netstat -anp or ss -tunap
        for cmd in (["ss","-tunap"], ["netstat","-anp"]):
            try:
                out = subprocess.run(cmd, capture_output=True, text=True, timeout=5).stdout
                if out.strip(): return out.strip()
            except Exception:
                continue
        return "(no connections)"

def find_capture_tool() -> tuple[str,str] | None:
    """
    Try to find a capture tool on PATH or common install paths.
    Returns (exe_path, kind) where kind in {'dumpcap','tshark','windump'}.
    """
    candidates = [
        ("dumpcap", "dumpcap"),
        ("tshark", "tshark"),
        ("windump", "windump"),  # WinPcap-compatible tcpdump
        ("tcpdump", "windump"),
    ]
    for exe, kind in candidates:
        p = shutil.which(exe)
        if p: return p, kind
    # common Windows Wireshark path
    for base in [r"C:\\Program Files\\Wireshark", r"C:\\Program Files (x86)\\Wireshark"]:
        for exe, kind in [("dumpcap.exe","dumpcap"),("tshark.exe","tshark")]:
            p = os.path.join(base, exe)
            if os.path.exists(p): return p, kind
    # common WinDump path
    for base in [r"C:\\Windows", r"C:\\Windows\\System32"]:
        p = os.path.join(base, "windump.exe")
        if os.path.exists(p): return p, "windump"
    return None

def start_capture(interface: int | None = None, bpf: str | None = None, out_dir: str = "captures") -> str:
    """
    Start packet capture if a tool is present. Non-blocking; use stop_capture() to end.
    - interface: numeric index as seen by the tool (None => default).
    - bpf: optional capture filter (e.g., 'tcp port 80').
    Saves to out_dir/ISpy-YYYYmmdd-HHMMSS.pcapng (or .pcap).
    """
    global CAP_PROC, CAP_FILE
    if CAP_PROC is not None:
        return "Capture already running."
    found = find_capture_tool()
    if not found:
        return "No capture tool found (need dumpcap/tshark/windump in PATH). Install Wireshark/Npcap to enable capture."
    exe, kind = found
    os.makedirs(out_dir, exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    ext = ".pcapng" if kind in ("dumpcap","tshark") else ".pcap"
    out_path = os.path.join(out_dir, f"ISpy-{ts}{ext}")
    args = [exe]
    if kind in ("dumpcap","tshark"):
        # dumpcap defaults to best interface; '-i X' optional
        if interface is not None:
            args += ["-i", str(interface)]
        if bpf:
            args += ["-f", bpf]
        args += ["-w", out_path]
    else:  # windump/tcpdump
        if interface is not None:
            args += ["-i", str(interface)]
        if bpf:
            args += [bpf]
        args += ["-w", out_path]
    try:
        CAP_PROC = subprocess.Popen(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        CAP_FILE = out_path
        CAP_TOOL = os.path.basename(exe)
        CAP_IFACE = interface
        return f"Capture started with {CAP_TOOL} on iface={interface if interface is not None else 'auto'} → {out_path}"
    except Exception as e:
        CAP_PROC = None; CAP_FILE = None
        return f"Failed to start capture: {e}"

def stop_capture() -> str:
    """Stop capture if running and return output path."""
    global CAP_PROC, CAP_FILE
    if CAP_PROC is None:
        return "No capture running (nothing to stop)."
    try:
        CAP_PROC.terminate()
        try:
            CAP_PROC.wait(timeout=3)
        except Exception:
            CAP_PROC.kill()
    finally:
        path = CAP_FILE or "(unknown)"
        CAP_PROC = None
        CAP_FILE = None
    return f"Capture stopped. Saved to: {path}"


def list_interfaces() -> list[tuple[int, str]]:  # MERGE_FRIENDLY
    """
    Return [(index, description), ...] of capture interfaces if a tool supports listing.
    Works with dumpcap/tshark/windump/tcpdump.
    """
    found = find_capture_tool()
    if not found:
        return []
    exe, kind = found
    try:
        if kind in ("dumpcap","tshark"):
            # dumpcap -D
            out = subprocess.run([exe, "-D"], capture_output=True, text=True, timeout=5).stdout
        else:
            # windump/tcpdump -D
            out = subprocess.run([exe, "-D"], capture_output=True, text=True, timeout=5).stdout
        items = []
        for line in out.splitlines():
            line = line.strip()
            if not line:
                continue
            # lines like: "1. \Device\NPF_{GUID} (Desc)"
            # or "1.eth0"
            for sep in (". ", ".", " "):
                if sep in line:
                    left, right = line.split(sep, 1)
                    try:
                        idx = int(left.strip())
                        items.append((idx, right.strip()))
                        break
                    except Exception:
                        continue

        # merge PowerShell friendly names on Windows
        if sys.platform.startswith("win"):
            friendly = _friendly_win_ifaces()
            merged = []
            for idx, desc in items:
                label = friendly.get(idx)
                if label:
                    merged.append((idx, f"{idx}: {label}"))
                else:
                    merged.append((idx, f"{idx}: {desc}"))
            items = merged
        return items
    except Exception:
        return []


def _friendly_win_ifaces() -> dict[int, str]:
    """Return {index: 'Name (Description)'} using PowerShell Get-NetAdapter when available."""
    try:
        import subprocess, json
        cmd = ["powershell", "-NoProfile", "-Command",
               "Get-NetAdapter | Select-Object ifIndex,Name,InterfaceDescription | ConvertTo-Json -Depth 2"]
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=5).stdout.strip()
        if not out:
            return {}
        data = json.loads(out)
        if isinstance(data, dict):
            data = [data]
        table = {}
        for row in data or []:
            idx = int(row.get("ifIndex"))
            name = row.get("Name") or ""
            desc = row.get("InterfaceDescription") or ""
            label = name if name else desc
            if name and desc and desc.lower() != name.lower():
                label = f"{name} ({desc})"
            table[idx] = label
        return table
    except Exception:
        return {}

def capture_running() -> bool:
    return CAP_PROC is not None


def _load_rotate_opts():
    try:
        from app.services.settings import load
        cfg = load().get("capture_rotate", {})
        dur = int(cfg.get("duration_sec", 60))
        fsize = int(cfg.get("filesize_mb", 20))
        files = int(cfg.get("files", 5))
        return max(5, dur), max(1, fsize), max(1, files)
    except Exception:
        return 60, 20, 5


def adapter_stats() -> str:
    """Return pretty adapter stats (Windows: PowerShell Get-NetAdapterStatistics)."""
    import sys, subprocess, json
    try:
        if sys.platform.startswith("win"):
            cmd = ["powershell", "-NoProfile", "-Command",
                   "Get-NetAdapterStatistics | Select-Object Name,ReceivedBytes,SentBytes,ReceivedUnicastPackets,SentUnicastPackets | ConvertTo-Json -Depth 2"]
            out = subprocess.run(cmd, capture_output=True, text=True, timeout=5).stdout.strip()
            data = json.loads(out) if out else []
            if isinstance(data, dict): data=[data]
            lines = []
            for row in data or []:
                n = row.get("Name","(unknown)")
                rb = int(row.get("ReceivedBytes",0)); sb = int(row.get("SentBytes",0))
                rup = int(row.get("ReceivedUnicastPackets",0)); sup = int(row.get("SentUnicastPackets",0))
                lines.append(f"{n:20} RX {rb} bytes ({rup} pkts)  TX {sb} bytes ({sup} pkts)")
            return "\n".join(lines) if lines else "(no stats)"
        return "(adapter stats not implemented on this OS)"
    except Exception as e:
        return f"(stats error: {e})"
