import os, json, csv, re, zipfile, gzip, io
from typing import Iterable

BREACH_DIR = os.path.join(os.path.dirname(__file__), "..", "breaches")
ENABLED_FILE = os.path.join(BREACH_DIR, "_enabled.json")

class BreachHit(dict):
    pass

def _load_enabled() -> set[str]:
    try:
        with open(ENABLED_FILE, "r", encoding="utf-8") as f:
            obj = json.load(f)
            if isinstance(obj, dict) and isinstance(obj.get("enabled"), list):
                return set(obj["enabled"])
    except Exception:
        pass
    return set()  # empty => treat as "all enabled"

def _save_enabled(enabled_list: list[str]):
    try:
        with open(ENABLED_FILE, "w", encoding="utf-8") as f:
            json.dump({"enabled": enabled_list}, f, indent=2)
    except Exception:
        pass

def list_all_files() -> list[str]:
    if not os.path.isdir(BREACH_DIR):
        return []
    names = [n for n in sorted(os.listdir(BREACH_DIR)) if any(n.lower().endswith(ext) for ext in (".txt",".csv",".json",".lst",".log",".zip",".gz"))]
    return names

def set_enabled(files: list[str]):
    files_set = [f for f in files if f in list_all_files()]
    _save_enabled(files_set)

def get_enabled() -> list[str]:
    en = _load_enabled()
    if not en:
        # none explicitly enabled => everything is effectively enabled
        return list_all_files()
    return [f for f in list_all_files() if f in en]

def _iter_txt_stream(f) -> Iterable[dict]:
    for line in f:
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        row = {}
        if "@" in s and "." in s:
            row["email"] = s
        elif "." in s and "/" not in s and " " not in s and "@" not in s:
            row["domain"] = s
        else:
            row["username"] = s
        yield row

def _iter_txt(path: str) -> Iterable[dict]:
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        yield from _iter_txt_stream(f)

def _iter_csv_stream(f) -> Iterable[dict]:
    try:
        reader = csv.DictReader(f)
        for row in reader:
            out = {}
            for k,v in (row or {}).items():
                if k is None: continue
                kk = k.lower().strip()
                vv = (v or "").strip()
                if not vv: continue
                if kk in ("email","username","domain","password","password_hash","salt","source"):
                    out[kk] = vv
            if out:
                yield out
    except csv.Error:
        f.seek(0)
        for line in f:
            s = line.strip()
            if not s or s.startswith("#"):
                continue
            if ":" in s:
                a,b = s.split(":",1)
                a,b = a.strip(), b.strip()
                row = {}
                if "@" in a: row["email"] = a
                else: row["username"] = a
                if b: row["password"] = b
                yield row
            else:
                row = {}
                if "@" in s: row["email"] = s
                elif "." in s: row["domain"] = s
                else: row["username"] = s
                yield row

def _iter_csv(path: str) -> Iterable[dict]:
    with open(path, "r", encoding="utf-8", errors="ignore", newline="") as f:
        yield from _iter_csv_stream(f)

def _iter_json_stream(f) -> Iterable[dict]:
    try:
        obj = json.load(f)
    except Exception:
        return
    if isinstance(obj, list):
        for item in obj:
            if isinstance(item, str):
                s = item.strip()
                if not s: continue
                row = {}
                if "@" in s and "." in s:
                    row["email"] = s
                elif "." in s and "/" not in s and " " not in s and "@" not in s:
                    row["domain"] = s
                else:
                    row["username"] = s
                yield row
            elif isinstance(item, dict):
                out = {}
                for k,v in item.items():
                    kk = str(k).lower().strip()
                    vv = str(v).strip() if v is not None else ""
                    if not vv: continue
                    if kk in ("email","username","domain","password","password_hash","salt","source"):
                        out[kk] = vv
                if out:
                    yield out

def _iter_json(path: str) -> Iterable[dict]:
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        yield from _iter_json_stream(f)

def _iter_zip(path: str) -> Iterable[dict]:
    with zipfile.ZipFile(path, "r") as z:
        for name in z.namelist():
            lower = name.lower()
            try:
                with z.open(name) as fbin:
                    data = fbin.read()
                    if lower.endswith(('.txt','.lst','.log')):
                        yield from _iter_txt_stream(io.StringIO(data.decode('utf-8','ignore')))
                    elif lower.endswith('.csv'):
                        yield from _iter_csv_stream(io.StringIO(data.decode('utf-8','ignore')))
                    elif lower.endswith('.json'):
                        yield from _iter_json_stream(io.StringIO(data.decode('utf-8','ignore')))
            except Exception:
                continue

def _iter_gz(path: str) -> Iterable[dict]:
    with gzip.open(path, "rt", encoding="utf-8", errors="ignore") as f:
        yield from _iter_txt_stream(f)

def _iter_path(path: str) -> Iterable[dict]:
    p = path.lower()
    if p.endswith(('.txt','.lst','.log')):
        yield from _iter_txt(path)
    elif p.endswith('.csv'):
        yield from _iter_csv(path)
    elif p.endswith('.json'):
        yield from _iter_json(path)
    elif p.endswith('.zip'):
        yield from _iter_zip(path)
    elif p.endswith('.gz'):
        yield from _iter_gz(path)

def load_sources() -> list[str]:
    files = []
    enabled = set(get_enabled())  # returns all if none explicitly enabled
    all_files = list_all_files()
    # If enabled is a subset, use it; else use all files
    use = enabled if set(enabled) <= set(all_files) else all_files
    for name in use:
        files.append(os.path.join(BREACH_DIR, name))
    return files

def _norm(s: str) -> str:
    return s.strip().lower()

def _looks_email(s: str) -> bool:
    return "@" in s and "." in s

def _looks_domain(s: str) -> bool:
    return "." in s and "/" not in s and " " not in s and "@" not in s

def scan(target: str):
    if not target:
        return 0, []
    t = _norm(target)
    is_email = _looks_email(t)
    is_domain = _looks_domain(t) and not is_email

    matches = []
    for path in load_sources():
        src_name = os.path.basename(path)
        for row in _iter_path(path) or []:
            hit = { "source": src_name }
            email = _norm(row.get("email","")) if row.get("email") else ""
            username = _norm(row.get("username","")) if row.get("username") else ""
            domain = _norm(row.get("domain","")) if row.get("domain") else ""
            if row.get("password"): hit["password"] = row["password"]
            if row.get("password_hash"): hit["password_hash"] = row["password_hash"]
            if row.get("salt"): hit["salt"] = row["salt"]
            if row.get("source"): hit["src_label"] = row["source"]

            matched = False
            if is_email:
                if email == t:
                    matched = True
                    hit["email"] = row.get("email")
            elif is_domain:
                if domain == t or (email and email.endswith("@"+t)):
                    matched = True
                    if domain: hit["domain"] = row.get("domain")
                    if email: hit["email"] = row.get("email")
            else:
                if username == t:
                    matched = True
                    hit["username"] = row.get("username")

            if matched:
                matches.append(hit)

    return len(matches), matches


import os, csv, json, gzip, zipfile, io, re
SUPPORTED_EXT = {".txt", ".csv", ".json", ".gz", ".zip"}

def import_folder(folder: str):
    """Copy supported files from folder recursively into breaches dir."""
    out = []
    dest_dir = os.path.join(os.path.dirname(__file__), "breaches")
    os.makedirs(dest_dir, exist_ok=True)
    for root, dirs, files in os.walk(folder):
        for name in files:
            if any(name.lower().endswith(e) for e in SUPPORTED_EXT):
                src = os.path.join(root, name)
                dst = os.path.join(dest_dir, name)
                try:
                    if os.path.abspath(src) != os.path.abspath(dst):
                        import shutil
                        shutil.copy2(src, dst)
                    out.append((name, "ok"))
                except Exception as e:
                    out.append((name, f"error: {e}"))
    return out
