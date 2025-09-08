
import os, sys, tempfile, urllib.request, subprocess, shutil, time
from typing import Callable, Optional, Tuple

def _emit(on_update, msg: str):
    try:
        if on_update:
            on_update(msg)
    except Exception:
        pass

def find_capture_tool() -> Optional[Tuple[str,str]]:
    # fallback discover (repeat of sniff.find_capture_tool to avoid circular import)
    import shutil, os
    candidates = [("dumpcap","dumpcap"),("tshark","tshark"),("windump","windump"),("tcpdump","windump")]
    for exe, kind in candidates:
        p = shutil.which(exe)
        if p: return p, kind
    for base in [r"C:\\Program Files\\Wireshark", r"C:\\Program Files (x86)\\Wireshark"]:
        for exe, kind in [("dumpcap.exe","dumpcap"),("tshark.exe","tshark")]:
            p = os.path.join(base, exe)
            if os.path.exists(p): return p, kind
    for base in [r"C:\\Windows", r"C:\\Windows\\System32"]:
        p = os.path.join(base, "windump.exe")
        if os.path.exists(p): return p, "windump"
    return None

def _download(urls, dst, on_update):
    last_err = None
    for url in urls:
        try:
            _emit(on_update, f"Downloading: {url}")
            urllib.request.urlretrieve(url, dst)
            size = os.path.getsize(dst)
            if size < 256_000:
                raise RuntimeError("unexpected small file")
            _emit(on_update, f"Saved: {dst} ({size//1024} KB)")
            return dst
        except Exception as e:
            last_err = e
            _emit(on_update, f"  failed: {e}")
            try:
                if os.path.exists(dst): os.remove(dst)
            except Exception:
                pass
            continue
    raise RuntimeError(f"All download candidates failed: {last_err}")

def install_best(on_update: Callable[[str], None] | None = None) -> str:
    """
    Windows: download & run Wireshark (dumpcap/tshark) + Npcap silently.
    Other OS: print instructions.
    """
    if find_capture_tool():
        return "Scanner already present (dumpcap/tshark/windump found)."

    if sys.platform.startswith("win"):
        tmp = tempfile.mkdtemp(prefix="ispy_inst_")
        wireshark = os.path.join(tmp, "wireshark.exe")
        npcap = os.path.join(tmp, "npcap.exe")

        ws_urls = [
            "https://www.wireshark.org/download/win64/Wireshark-win64-latest.exe",
            "https://1.na.dl.wireshark.org/win64/Wireshark-win64-latest.exe",
        ]
        np_urls = [
            "https://npcap.com/dist/npcap.exe",
            "https://nmap.org/npcap/dist/npcap.exe",
        ]

        try:
            _download(ws_urls, wireshark, on_update)
        except Exception as e:
            return f"Wireshark download failed: {e}"

        try:
            _download(np_urls, npcap, on_update)
        except Exception as e:
            return f"Npcap download failed: {e}"

        # Run installers. These will likely trigger UAC.
        try:
            _emit(on_update, "Installing Npcap (silent)…")
            # /S silent, defaults are fine; requires admin
            subprocess.run([npcap, "/S"], check=True)
            _emit(on_update, "Npcap installed.")
        except Exception as e:
            return f"Npcap install failed: {e}"

        try:
            _emit(on_update, "Installing Wireshark (silent)…")
            # Wireshark supports /S for silent
            subprocess.run([wireshark, "/S"], check=True)
            _emit(on_update, "Wireshark installed.")
        except Exception as e:
            return f"Wireshark install failed: {e}"

        # Refresh PATH in current session by probing known install folders
        added = []
        for base in [r"C:\\Program Files\\Wireshark", r"C:\\Program Files (x86)\\Wireshark"]:
            if os.path.isdir(base):
                os.environ["PATH"] = base + os.pathsep + os.environ.get("PATH","")
                added.append(base)

        tool = find_capture_tool()
        if tool:
            exe, kind = tool
            return f"Installed {kind} at {exe}. Added to PATH: {', '.join(added) if added else '(system)'}"
        return "Installers finished, but capture tool still not detected. Try restarting ISpy."

    # Non-Windows
    return ("Auto-install is only implemented on Windows.\n"
            "- macOS: brew install wireshark\n"
            "- Debian/Ubuntu: sudo apt-get install wireshark tshark\n"
            "- Fedora: sudo dnf install wireshark wireshark-cli")

