import json, os

CONFIG_PATH = r"/mnt/data/ISpy0243/ISpy/app/data/config.json"

DEFAULTS = {
    "hibp_api_key": "",
    "use_hibp_email_scan": False,
    "capture_rotate": {"duration_sec": 60, "filesize_mb": 20, "files": 5}
}

def load() -> dict:
    """Load config, creating default file/dir if needed."""
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    if not os.path.exists(CONFIG_PATH):
        save(DEFAULTS)
    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    # merge defaults
    for k, v in DEFAULTS.items():
        if k not in cfg:
            cfg[k] = v
    return cfg

def save(cfg: dict) -> None:
    """Safely write config (atomic replace)."""
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    tmp = CONFIG_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)
    os.replace(tmp, CONFIG_PATH)
