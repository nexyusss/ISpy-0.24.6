# LookupTool — Black Terminal Network Toolbox (v9)

A portable, **Python + Tkinter** app that looks like a black terminal and gives you a focused set of network + OSINT helpers.
It’s privacy‑first (offline where possible), with clear prompts when showing sensitive results.

---

## Quick Start

### Windows (recommended)
1. **Install Python 3.8+** from [python.org] (includes Tkinter).
2. Unzip this folder anywhere (e.g., Desktop).
3. Double‑click **`ISpy_Run_Debug.bat`** the first time.
   - A console stays open so you can see messages.
   - If anything fails, the reason is printed here.
4. After that, use **`ISpy_Run.bat`** for normal runs.
   - Logs go to `logs\run.log` and the window **pauses on error**.

### macOS / Linux
```bash
cd /path/to/LookupTool9/LookupTool9
python3 app/main.py
```
If Tk isn’t installed: `sudo apt install python3-tk` (Debian/Ubuntu) or your distro equivalent.

---

## Requirements & Auto‑Install

- **Python 3.8+** (3.13 is fine).
- **Tkinter** (bundled with python.org installer on Windows).
- This repo ships with **`requirements.txt`**. It’s **empty by default** (stdlib only).
- The launchers **auto‑install** any packages listed (if you add some):
  - `ISpy_Run.bat` / `ISpy_Run_Debug.bat` will run `pip install -r requirements.txt` automatically
    if the file has any non‑comment lines.

> Tip: if you add optional features that need libraries (e.g., `requests`), just add them to `requirements.txt` and relaunch.

---

## What You Can Do (Features)

### 1) Ping
- Send **4 echo requests** to a host/IP.
- Shows system `ping` output (latency, packet loss).
- Useful for **basic reachability** checks.

### 2) IP Info (Geo/ISP)
- Looks up a host/IP using a simple public endpoint (ip‑api).
- Displays **continent, country, region, city, ZIP, lat/lon, timezone, ISP/Org/AS**, and the resolved IP.
- Notes: free tier has **rate limits**; accuracy varies.

### 3) DNS Tools
- **A record**: resolve hostname → IPv4.
- **Reverse PTR**: IPv4 → hostname (if available).

### 4) WHOIS (Domain/IP)
- Queries raw WHOIS servers.
- For **IPs**: starts with ARIN and follows referrals.
- For **domains**: uses IANA to find the registry WHOIS then queries it.
- Output is **raw registry text**, which can vary by TLD/region.

### 5) Port Check (Common Ports)
- Quickly checks TCP **connect** to common ports (e.g., 21,22,25,53,80,443,8080,3389, etc.).
- **Use only on hosts you own or are authorized to test.**
- This is not a full scanner; it’s a quick “are typical services open?” helper.

### 6) Social Lookup (Multi‑site, Binary Status + Details)
- Supports: **Instagram, Facebook, X (Twitter), TikTok, YouTube, Reddit, GitHub, Twitch, Pinterest, LinkedIn, Snapchat**, or **All**.
- Returns **found / not found** and tries to extract:
  - **Display name**
  - **Canonical username** (from canonical URL when present)
  - **Short bio/description**
  - **Follower count** (heuristic)
  - **Direct profile link** (always shown)
- Implementation uses lightweight HTML parsing (no JS). Sites may throttle or change markup — treat this as a **best‑effort OSINT aid**.

### 7) Breach Check (Offline, Local Lists)
- Enter an **email**, **username**, or **domain** and scan **local breach lists** in `app/breaches/`.
- Supports **TXT / CSV / JSON** and compressed **`.gz` / `.zip`** (inner files `.txt/.csv/.json`).
- **Match rules (case‑insensitive):**
  - Email → exact match on email field.
  - Username → exact match on username field.
  - Domain → exact match on domain **or** any email ending with `@domain`.
- If matches are found, the app asks **“Reveal details?” (Yes/No)** before printing fields like email/username/domain/password/password_hash/salt (when present).
- **Manage Sources**: enable/disable specific files (state saved to `app/breaches/_enabled.json`).
- **Sources**: quickly list all files that are active in the scan.
- **Import Pack**: add your own `.zip/.gz/.txt/.csv/.json` files to the breaches folder from inside the app.

> This is a **lightweight feature**, not a HIBP clone. It’s designed for local/offline checks with your own lists.

---

## Using the UI

- **Target row** (top): enter host/IP → use **Ping**, **IP Info**, **DNS A**, **Reverse PTR**, **WHOIS**, **Port Check**.
- **Social row**:
  - Choose a network (or **All**), enter **username**, click **Lookup**.
  - Use **Open Profile** to open the profile link in your browser.
- **Breach row**:
  - Enter **email/username/domain** and click **Scan**.
  - **Sources**: lists active files.
  - **Manage Sources**: turn individual files on/off.
  - **Import Pack**: copy a `.zip/.gz/.txt/.csv/.json` into `app/breaches/`.
- **Console panel**:
  - Shows command echoes and results in a black terminal‑style view.
- **Bottom bar**: **Help**, **Clear**, **Quit**.

---

## Privacy & Safety

- Most tools are **local/offline**. Online calls used by:
  - **IP Info** (ip-api), **Social Lookup** (public profile pages), **WHOIS** (registry servers).
- Breach Check runs **entirely offline on your files**.
- Only scan or probe systems you **own** or are **authorized** to test.
- Respect site **rate limits** and **terms of service** for social lookups.

---

## Troubleshooting

- **Window closes instantly (Windows)**: run **`ISpy_Run_Debug.bat`** to keep the console open. Check `logs\run.log` when using `ISpy_Run.bat`.
- **Tkinter missing**: install Python from python.org; on Linux, `python3-tk` package.
- **Ping output empty**: some networks block ICMP; still try DNS/WHOIS/ports.
- **Social lookup inconsistent**: sites throttle, use anti‑bot, or change markup. Try again later or a VPN if appropriate.
- **WHOIS empty/odd**: different registries return different formats; follow referrals where shown.
- **Port check shows closed**: firewalls may drop connections; try from within the same network if you control the host.

---

## Customize / Extend

- **Add libraries**: put them in `requirements.txt` — launchers will auto‑install next run.
- **Add breach lists**: drop files into `app/breaches/`, use **Manage Sources** to enable/disable.
- **Tweak UI**: `app/main.py` (Tkinter); colors/fonts at the top of the file.
- **Services** live in `app/services/`:
  - `ping.py`, `ip_lookup.py`, `dns_tools.py`, `whois_tools.py`, `ports.py`, `social_lookup.py`, `breach_check.py`.

---

## FAQ

**Q: Do I need Administrator?**
A: No for most features. Port checks use standard TCP connects. `ping` uses the system command that may require firewall allowances but not admin.

**Q: Is this safe to run offline?**
A: Yes. Breach checks are offline on your local lists. Social/IP/WHOIS fetch data from public endpoints when used.

**Q: Will you add online breach APIs?**
A: Can be added behind a clear toggle. By default we stay offline for privacy.

---

## Version Highlights

- **v9**: Complete README rewrite, consolidated instructions.
- **v8**: Wider Social Lookup + richer metadata.
- **v7**: Stable imports, only two launchers, auto‑install `requirements.txt`.
- **v6**: Robust launcher pathing (fixed module import issues).
- **v5**: Preflight checks + logging; debug launcher keeps window open on errors.
- **v1–4**: Core tools, breach scanning, sources UI, compressed/zip support.

---

## License

MIT — do whatever, just be kind and legal.


### 8) Password exposure (safe)
- **Online (recommended):** HIBP k‑anonymity — only the first 5 chars of SHA‑1 are sent; response is a list of suffixes and counts.
- **Offline:** check against any plaintext `.txt` password lists you add to `app/breaches/` (or `.txt` inside `.zip`/`.gz`). The app streams the file; it doesn’t upload your password anywhere.
- The console masks your input; avoid pasting important active passwords — check older/test passwords where possible.


### SecLists Import (v12)
- Click **Import SecLists** to fetch popular password/username lists directly from the
  `danielmiessler/SecLists` GitHub repo (curated presets included).
- You can also paste any **raw GitHub URLs** (one per line) to pull exactly what you want.
- Files are saved into `app/breaches/` with a `seclists_` prefix to keep things organized.
- After downloading, use **Sources** / **Manage Sources** to confirm and enable them.

*Note:* Some SecLists files are very large. Start with the presets (10k/100k subsets) before grabbing the huge ones.

## Quick Start

1. Unzip the archive anywhere you like (e.g., `Desktop`).
2. Double‑click **ISpy_Run.bat** to launch ISpy.
3. For verbose logs or troubleshooting, run **ISpy_Run_Debug.bat**.

## Requirements

- Windows 10 or 11
- Python 3.10+ with Tkinter (use `py -3` on Windows)
- No extra packages required; standard library only
