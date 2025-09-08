
import sys, os, traceback, platform, runpy

def eprint(*a, **k):
    print(*a, **k, file=sys.stderr)

def check_python():
    v = sys.version_info
    if v.major < 3 or (v.major == 3 and v.minor < 8):
        eprint("[Preflight] Python 3.8+ required, found: %d.%d.%d" % (v.major, v.minor, v.micro))
        return False
    print("[Preflight] Python:", sys.version.replace("\n"," "))
    return True

def check_tk():
    try:
        import tkinter
        root = tkinter.Tk()
        root.withdraw()
        root.update_idletasks()
        root.destroy()
        print("[Preflight] Tkinter: OK")
        return True
    except Exception as e:
        eprint("[Preflight] Tkinter NOT available:", repr(e))
        eprint("  - On Windows, install Python from python.org (includes Tcl/Tk).")
        eprint("  - If using Microsoft Store Python, ensure 'tcl/tk and IDLE' optional feature is installed.")
        return False

def main():
    print("=== ISpy v0.24.6 Launcher ===")
    print("[Env] Platform:", platform.platform())
    print("[Env] CWD:", os.getcwd())

    ok = True
    ok &= check_python()
    ok &= check_tk()
    if not ok:
        return 2

    # Ensure project root and app folder are on sys.path so imports work regardless of how we launch
    THIS = os.path.abspath(__file__)
    APP_DIR = os.path.dirname(THIS)                # ...\ISpy6\app
    ROOT_DIR = os.path.dirname(APP_DIR)            # ...\ISpy6
    if ROOT_DIR not in sys.path:
        sys.path.insert(0, ROOT_DIR)
    if APP_DIR not in sys.path:
        sys.path.insert(0, APP_DIR)

    print("[Launcher] sys.path[0:3]:", sys.path[:3])

    try:
        # Run the GUI by path so absolute 'from services import ...' works
        main_py = os.path.join(APP_DIR, "main.py")
        print("[Launcher] Running:", main_py)
        runpy.run_path(main_py, run_name="__main__")
        return 0
    except SystemExit as se:
        return int(getattr(se, "code", 0) or 0)
    except Exception:
        eprint("[Launcher] Unhandled exception:\n" + traceback.format_exc())
        return 1

if __name__ == "__main__":
    sys.exit(main())
