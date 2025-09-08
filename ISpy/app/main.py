
import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from tkinter.scrolledtext import ScrolledText
import threading
import webbrowser

from app.services.ping import ping
from app.services.ip_lookup import ip_info
from app.services.dns_tools import resolve_a, resolve_aaaa, reverse_ptr
from app.services.ports import quick_port_check
from app.services.whois_tools import whois

from app.services.social_enhanced import enhanced_lookup
from app.services.social_lookup import check_all, generate_variants
from app.services.social_search import search_profiles, direct_probe_many

from app.services.breach_check import scan, load_sources, list_all_files, get_enabled, set_enabled, import_folder as svc_import_folder
from app.services.password_check import hibp_k_anon, local_password_hit

from app.services.sniff import list_connections, start_capture, stop_capture, list_interfaces, capture_running, adapter_stats
from app.services.install_scanner import install_best

from app.services.settings import load as cfg_load, save as cfg_save
from app.services.hibp import breached_account

APP_TITLE = "ISpy — Black Terminal UI (0.24.6)"
HELP_TEXT = (
    "Tabs:\n"
    "- Network: ping (live), ip-info, dns (A/AAAA), reverse PTR, whois, ports (IPv4/IPv6)\n"
    "- Social: lookup profile or Find Matches chooser\n"
    "- Breach: scan local lists + optional HIBP (email), import packs / SecLists / folders\n"
    "- Traffic: connections snapshot, packet capture with auto-rotate, adapter stats, installer\n"
)

BLACK = "#0b0b0b"
GREEN = "#00ff7f"
GRAY = "#202020"
FG = "#e6ffe6"


class App(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title(APP_TITLE)
        self.geometry("1120x840")
        self.configure(bg=BLACK)
        self._setup_styles()
        self._build()
        self._conn_auto_job = None

    def _setup_styles(self) -> None:
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TLabel", background=BLACK, foreground=FG, font=("Consolas", 11))
        style.configure("TFrame", background=BLACK)
        style.configure("TButton", background=GRAY, foreground=FG, font=("Consolas", 11), padding=6)
        style.map("TButton", background=[("active", "#2c2c2c")])
        style.configure("TEntry", fieldbackground="#111111", foreground=FG)
        style.configure("TNotebook", background=BLACK)
        style.configure("TNotebook.Tab", background=BLACK, foreground=FG)
        style.map("TNotebook.Tab", background=[("selected", "#151515")], foreground=[("selected", FG)])

    def _build(self) -> None:
        notebook = ttk.Notebook(self)
        notebook.pack(fill="both", expand=True, padx=10, pady=10)

        # === Network ===
        tab_net = ttk.Frame(notebook)
        notebook.add(tab_net, text="Network")

        top = ttk.Frame(tab_net); top.pack(fill="x", padx=4, pady=6)
        ttk.Label(top, text="Target: ").pack(side="left")
        self.target_var = tk.StringVar()
        self.target_entry = ttk.Entry(top, textvariable=self.target_var, width=54)
        self.target_entry.pack(side="left", padx=8)
        self.target_entry.focus_set()

        ttk.Button(top, text="Ping", command=self.do_ping).pack(side="left", padx=4)
        ttk.Button(top, text="IP Info", command=self.do_ip).pack(side="left", padx=4)
        ttk.Button(top, text="DNS A", command=self.do_a).pack(side="left", padx=4)
        ttk.Button(top, text="DNS AAAA", command=self.do_aaaa).pack(side="left", padx=4)
        ttk.Button(top, text="Reverse PTR", command=self.do_ptr).pack(side="left", padx=4)
        ttk.Button(top, text="WHOIS", command=self.do_whois).pack(side="left", padx=4)
        ttk.Button(top, text="Port Check", command=self.do_ports).pack(side="left", padx=4)

        self.prefer_v6 = tk.BooleanVar(value=False)
        ttk.Checkbutton(top, text="Prefer IPv6", variable=self.prefer_v6).pack(side="left", padx=8)

        prow = ttk.Frame(tab_net); prow.pack(fill="x", padx=4, pady=(4,2))
        ttk.Label(prow, text="Pings:").pack(side="left")
        self.ping_count = tk.IntVar(value=4)
        sc1 = ttk.Scale(prow, from_=1, to=1000, orient="horizontal", command=lambda v: self.ping_count.set(int(float(v))))
        sc1.set(4); sc1.pack(side="left", fill="x", expand=True, padx=6)
        self.lbl_ping_count = ttk.Label(prow, text="4"); self.lbl_ping_count.pack(side="left", padx=6)
        self.ping_count.trace_add("write", lambda *a: self.lbl_ping_count.configure(text=str(self.ping_count.get())))

        ttk.Label(prow, text="Rate (ms):").pack(side="left", padx=(10,0))
        self.ping_rate = tk.IntVar(value=250)
        sc2 = ttk.Scale(prow, from_=0, to=1000, orient="horizontal", command=lambda v: self.ping_rate.set(int(float(v))))
        sc2.set(250); sc2.pack(side="left", fill="x", expand=True, padx=6)
        self.lbl_ping_rate = ttk.Label(prow, text="250"); self.lbl_ping_rate.pack(side="left", padx=6)
        self.ping_rate.trace_add("write", lambda *a: self.lbl_ping_rate.configure(text=str(self.ping_rate.get())))

        ps = ttk.Frame(tab_net); ps.pack(fill="x", padx=4, pady=(2,6))
        ttk.Label(ps, text="Port set:").pack(side="left")
        self.port_set = tk.StringVar(value="basic")
        ttk.OptionMenu(ps, self.port_set, "basic", "basic","extended","1k").pack(side="left", padx=6)

        # === Social ===
        tab_soc = ttk.Frame(notebook); notebook.add(tab_soc, text="Social")
        s1 = ttk.Frame(tab_soc); s1.pack(fill="x", padx=4, pady=6)
        ttk.Label(s1, text="Network: ").pack(side="left")
        self.network_var = tk.StringVar(value="instagram")
        ttk.OptionMenu(s1, self.network_var, "instagram", "instagram","facebook","x","tiktok","youtube","reddit","github","twitch","pinterest","linkedin","snapchat","all").pack(side="left")
        ttk.Label(s1, text="Username/Name:").pack(side="left", padx=(10,2))
        self.username_var = tk.StringVar()
        ttk.Entry(s1, textvariable=self.username_var, width=30).pack(side="left", padx=4)
        ttk.Button(s1, text="Lookup", command=self.do_social).pack(side="left", padx=4)
        ttk.Button(s1, text="Find Matches", command=self.do_social_search).pack(side="left", padx=4)
        ttk.Button(s1, text="Open Profile", command=self.open_profile_in_browser).pack(side="left", padx=4)

        # === Breach ===
        tab_breach = ttk.Frame(notebook); notebook.add(tab_breach, text="Breach")
        br = ttk.Frame(tab_breach); br.pack(fill="x", padx=4, pady=6)
        ttk.Label(br, text="Email / Username / Domain:").pack(side="left")
        self.breach_var = tk.StringVar()
        ttk.Entry(br, textvariable=self.breach_var, width=40).pack(side="left", padx=6)
        ttk.Button(br, text="Scan", command=self.do_breach).pack(side="left", padx=4)
        ttk.Button(br, text="Sources", command=self.list_sources).pack(side="left", padx=4)
        ttk.Button(br, text="Manage Sources", command=self.manage_sources).pack(side="left", padx=4)
        ttk.Button(br, text="Import Pack", command=self.import_pack).pack(side="left", padx=4)
        ttk.Button(br, text="Import SecLists", command=self.import_seclists).pack(side="left", padx=4)
        ttk.Button(br, text="Import Folder", command=self.do_import_folder).pack(side="left", padx=4)

        pwd = ttk.Frame(tab_breach); pwd.pack(fill="x", padx=4, pady=6)
        ttk.Label(pwd, text="Password Check:").pack(side="left")
        self.pwd_var = tk.StringVar()
        ttk.Entry(pwd, textvariable=self.pwd_var, width=30, show="*").pack(side="left", padx=6)
        self.use_k_anon = tk.BooleanVar(value=True)
        ttk.Checkbutton(pwd, text="Online (HIBP k-anon)", variable=self.use_k_anon).pack(side="left", padx=6)
        ttk.Button(pwd, text="Check", command=self.do_pwd_check).pack(side="left", padx=4)

        cfg = cfg_load()
        self.use_hibp_email = tk.BooleanVar(value=bool(cfg.get("use_hibp_email_scan", False)))
        ttk.Checkbutton(tab_breach, text="Also query HIBP for this email (needs API key in Settings)", variable=self.use_hibp_email).pack(anchor="w", padx=12, pady=(0,6))

        # === Traffic ===
        tab_traffic = ttk.Frame(notebook); notebook.add(tab_traffic, text="Traffic")
        t0 = ttk.Frame(tab_traffic); t0.pack(fill="x", padx=4, pady=6)
        ttk.Label(t0, text="Interface:").pack(side="left")
        self.iface_var = tk.StringVar(value="(auto)"); self.iface_menu = ttk.OptionMenu(t0, self.iface_var, "(auto)"); self.iface_menu.pack(side="left", padx=6)
        ttk.Button(t0, text="Refresh", command=self.refresh_ifaces).pack(side="left")
        ttk.Label(t0, text="Filter (BPF):").pack(side="left", padx=(12,2))
        self.bpf_var = tk.StringVar(value=""); ttk.Entry(t0, textvariable=self.bpf_var, width=40).pack(side="left", padx=4)

        t1 = ttk.Frame(tab_traffic); t1.pack(fill="x", padx=4, pady=6)
        ttk.Button(t1, text="Snapshot Connections", command=self.do_conn_once).pack(side="left", padx=4)
        self.auto_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(t1, text="Auto-Refresh", variable=self.auto_var, command=self.toggle_conn_auto).pack(side="left", padx=8)
        ttk.Button(t1, text="Start Capture", command=self.do_cap_start).pack(side="left", padx=12)
        ttk.Button(t1, text="Stop Capture", command=self.do_cap_stop).pack(side="left", padx=4)
        ttk.Button(t1, text="Adapter Stats", command=self.do_adapter_stats).pack(side="left", padx=12)
        ttk.Button(t1, text="Install Scanner (Best)", command=self.do_install_scanner).pack(side="left", padx=12)
        ttk.Label(t1, text="(Needs dumpcap/tshark/windump)").pack(side="left", padx=12)

        self.cap_status = ttk.Label(tab_traffic, text="Capture: (not running)"); self.cap_status.pack(anchor="w", padx=8, pady=(0,6))

        # Output + bottom bar
        self.out = ScrolledText(self, wrap="word", bg=BLACK, fg=GREEN, insertbackground=FG, font=("Consolas", 11), height=22)
        self.out.pack(fill="both", expand=True, padx=10, pady=(0,10))
        self.out.insert("end", "ISpy 0.24.6 ready. Tabs: Network • Social • Breach • Traffic.\n\n")
        self.out.configure(state="disabled")

        bottom = ttk.Frame(self); bottom.pack(fill="x", padx=10, pady=(0,10))
        ttk.Button(bottom, text="Help", command=self.show_help).pack(side="left")
        ttk.Button(bottom, text="Clear", command=self.clear).pack(side="left", padx=5)
        ttk.Button(bottom, text="Settings", command=self.open_settings).pack(side="left", padx=5)
        ttk.Button(bottom, text="Quit", command=self.destroy).pack(side="right")

        self.refresh_ifaces()
        self.after(200, self._auto_start_capture)

    # ---------- Spinner helpers ----------
    def _show_spinner(self, msg="Working..."):
        try:
            if getattr(self, "_sp", None): return
            win = tk.Toplevel(self); win.title("Please wait"); win.configure(bg=BLACK)
            x = self.winfo_rootx() + self.winfo_width()//2 - 140; y = self.winfo_rooty() + self.winfo_height()//2 - 40
            win.geometry(f"280x80+{x}+{y}"); win.transient(self); win.grab_set(); win.resizable(False, False)
            ttk.Label(win, text=msg).pack(pady=(12,6)); pb = ttk.Progressbar(win, mode="indeterminate", length=220); pb.pack(pady=(0,8)); pb.start(15)
            self._sp=(win,pb)
        except Exception: pass
    def _hide_spinner(self):
        try:
            if not getattr(self, "_sp", None): return
            win,pb=self._sp; pb.stop(); win.grab_release(); win.destroy(); self._sp=None
        except Exception: pass

    # ---------- Generic helpers ----------
    def append(self, text: str) -> None:
        self.out.configure(state="normal")
        self.out.insert("end", text + ("" if text.endswith("\n") else "\n"))
        self.out.see("end")
        self.out.configure(state="disabled")

    def clear(self) -> None:
        self.out.configure(state="normal"); self.out.delete("1.0","end"); self.out.configure(state="disabled")

    def show_help(self) -> None:
        messagebox.showinfo("Help", HELP_TEXT)

    def run_async(self, fn, *args, post=None, spinner=None):
        def worker():
            try:
                if spinner: self.after(0, lambda: self._show_spinner(spinner))
                res = fn(*args)
            except Exception as e:
                res = f"[error] {e}"
            def finalize():
                if spinner: self._hide_spinner()
                if post: post(res)
                else: self.append(res if isinstance(res, str) else str(res))
            self.after(0, finalize)
        threading.Thread(target=worker, daemon=True).start()

    def run_stream(self, fn, *args, spinner=None):
        def worker():
            try:
                if spinner: self.after(0, lambda: self._show_spinner(spinner))
                def emit(line: str): self.after(0, lambda: self.append(line))
                res = fn(*args, on_update=emit)
            except Exception as e:
                res = f"[error] {e}"
            def finalize():
                if spinner: self._hide_spinner()
                if isinstance(res, str) and res: self.append(res)
            self.after(0, finalize)
        threading.Thread(target=worker, daemon=True).start()

    # ---------- Network actions ----------
    def do_ping(self):
        target = self.target_var.get().strip()
        if not target: return messagebox.showwarning("Ping", "Enter a host or IP.")
        self.append(f"ISpy is pinging {target}")
        self.append(f"$ ping {target}")
        self.run_stream(lambda on_update=None: ping(target, self.ping_count.get(), self.ping_rate.get(), on_update=on_update, ipv6=self.prefer_v6.get()))

    def do_ip(self):
        target = self.target_var.get().strip(); self.append(f"$ ip-info {target}"); self.run_async(ip_info, target)

    def do_a(self):
        target = self.target_var.get().strip(); self.append(f"$ dns-a {target}"); self.run_async(resolve_a, target)

    def do_aaaa(self):
        target = self.target_var.get().strip(); self.append(f"$ dns-aaaa {target}"); self.run_async(resolve_aaaa, target)

    def do_ptr(self):
        target = self.target_var.get().strip(); self.append(f"$ dns-ptr {target}"); self.run_async(reverse_ptr, target)

    def do_whois(self):
        target = self.target_var.get().strip(); self.append(f"$ whois {target}"); self.run_async(whois, target)

    def do_ports(self):
        target = self.target_var.get().strip()
        self.append(f"$ ports {target} ({self.port_set.get()})")
        self.run_async(lambda: quick_port_check(target, self.port_set.get(), prefer_v6=self.prefer_v6.get()), spinner="Scanning ports…")

    # ---------- Social ----------
    def _fmt_social(self, res: dict) -> str:
        d = res.get("details", {})
        lines = [f"{res.get('network','?')}: {res.get('status','?')}"]
        if d.get("display_name"): lines.append(f"  name: {d['display_name']}")
        if d.get("username"): lines.append(f"  user: {d['username']}")
        if d.get("followers") is not None: lines.append(f"  followers: {d['followers']}")
        if d.get("description"): lines.append(f"  about: {d['description'][:220]}")
        if d.get("profile_url"): lines.append(f"  link: {d['profile_url']}")
        return "\n".join(lines)

    def do_social(self):
        net = self.network_var.get().strip(); user = self.username_var.get().strip()
        if not user: return messagebox.showwarning("Social Lookup", "Enter a username first.")
        if net == "all":
            self.append(f"$ social all {user}")
            self.run_async(lambda: check_all(user), post=lambda L: self.append("\n".join(self._fmt_social(r) for r in L)))
        else:
            self.append(f"$ social {net} {user}")
            def work():
                best=None
                for u in generate_variants(user):
                    res = enhanced_lookup(net, u); best = best or res
                    if res.get("status") == "found": return res
                return best
            self.run_async(work, post=lambda r: (self.append(self._fmt_social(r)), self.append("(No direct hit. Try 'Find Matches'.)") if r.get("status")!="found" else None))

    def do_social_search(self):
        query = self.username_var.get().strip(); net = self.network_var.get().strip()
        if not query: return messagebox.showwarning("Find Matches", "Enter a username or name to search.")
        self.append(f"$ social-search {net if net!='all' else 'any'} {query}")
        def work():
            res = search_profiles(query, None if net=="all" else net, max_results=25)
            if res: return ("search", res)
            return ("probe", direct_probe_many(query, None if net=="all" else net, max_total=25))
        def post(payload):
            kind, results = payload
            if not results: return self.append("No candidates found.")
            top = tk.Toplevel(self); top.title("Select a profile"); top.configure(bg=BLACK)
            ttk.Label(top, text=f"Choose a profile for: {query}").pack(anchor="w", padx=10, pady=8)
            cols=("network","username","url"); tree=ttk.Treeview(top, columns=cols, show="headings", height=12)
            for c in cols: tree.heading(c, text=c); tree.column(c, width=220 if c!="url" else 520, anchor="w")
            tree.pack(fill="both", expand=True, padx=10, pady=8)
            for r in results: tree.insert("", "end", values=(r.get("network",""), r.get("username",""), r.get("url","")))
            def choose():
                item=tree.focus()
                if not item: return messagebox.showwarning("Select", "Pick a row.")
                vals=tree.item(item, "values"); chosen_net, chosen_user, chosen_url = vals[0], vals[1], vals[2]
                top.destroy()
                if not chosen_user: chosen_user = chosen_url.rstrip("/").split("/")[-1].lstrip("@")
                self.run_async(lambda: enhanced_lookup(chosen_net or "x", chosen_user), post=lambda res: self.append(self._fmt_social(res)))
            btns=ttk.Frame(top); btns.pack(fill="x", padx=10, pady=10)
            ttk.Button(btns, text="Choose", command=choose).pack(side="right")
            ttk.Button(btns, text="Cancel", command=top.destroy).pack(side="right", padx=6)
        self.run_async(work, post=post, spinner="Searching…")

    def open_profile_in_browser(self):
        net=self.network_var.get().strip(); user=self.username_var.get().strip()
        if not user: return messagebox.showwarning("Profile", "Enter a username first.")
        urls = {
            "instagram": f"https://www.instagram.com/{user}/",
            "facebook": f"https://www.facebook.com/{user}/",
            "x": f"https://x.com/{user}",
            "tiktok": f"https://www.tiktok.com/@{user}",
            "youtube": f"https://www.youtube.com/@{user}",
            "reddit": f"https://www.reddit.com/user/{user}/",
            "github": f"https://github.com/{user}",
            "twitch": f"https://www.twitch.tv/{user}",
            "pinterest": f"https://www.pinterest.com/{user}/",
            "linkedin": f"https://www.linkedin.com/in/{user}/",
            "snapchat": f"https://www.snapchat.com/add/{user}",
        }
        url=urls.get(net); webbrowser.open(url) if url else messagebox.showinfo("Profile", f"No opener for network: {net}")

    # ---------- Breach ----------
    def do_pwd_check(self):
        pwd=self.pwd_var.get()
        if not pwd: return messagebox.showwarning("Password Check","Enter a password to check.")
        masked="*"*max(4, min(12, len(pwd)))
        self.append(f"$ pwd-check {masked} ({'k-anon' if self.use_k_anon.get() else 'local'})")
        def work():
            if self.use_k_anon.get():
                found,count=hibp_k_anon(pwd); return f"password: {'found' if found else 'not found'}" + (f" (seen {count} times) — via HIBP k-anon" if found else " — via HIBP k-anon")
            found,src=local_password_hit(pwd); return f"password: {'found in ' + src if found else 'not found in local lists'}"
        self.run_async(work, spinner="Checking…")

    def do_breach(self):
        target=self.breach_var.get().strip()
        if not target: return messagebox.showwarning("Breach Check", "Enter an email, username, or domain.")
        self.append(f"$ breach-scan {target}")
        def combo():
            local = scan(target); cfg = cfg_load()
            if self.use_hibp_email.get() and cfg.get("hibp_api_key") and "@" in target:
                ok,data = breached_account(target, cfg.get("hibp_api_key")); return ("combo", local, (ok,data))
            return ("local", local, None)
        def post_combo(payload):
            kind, local, hibp = payload
            if isinstance(local, tuple): count,matches = local
            else: self.append(str(local)); return
            if count==0: self.append("No matches found in local breach lists.")
            else:
                self.append(f"Found {count} matches across local lists.")
                if messagebox.askyesno("Reveal details?","Matches found. Reveal full breached info?"):
                    lines=[]; 
                    for m in matches:
                        parts=[f"source={m.get('source','')}"]
                        for key in ("email","username","domain","password","password_hash","salt","src_label"):
                            if m.get(key): parts.append(f"{key}={m.get(key)}")
                        lines.append(" - "+", ".join(parts))
                    self.append("\n".join(lines))
                else: self.append("(Local details were hidden by user choice.)")
            if hibp:
                ok,data=hibp
                if ok:
                    if data: self.append("HIBP: account appears in "+str(len(data))+" breach(es): "+", ".join(data[:10])+(" …" if len(data)>10 else ""))
                    else: self.append("HIBP: no breached sites for this account.")
                else: self.append("HIBP error: "+str(data))
        self.run_async(combo, post=post_combo, spinner="Scanning…")

    def list_sources(self):
        files=load_sources()
        if not files: self.append("No breach files detected in app/breaches.")
        else:
            self.append("Loaded breach files:")
            for p in files: self.append(f" - {os.path.basename(p)}")

    def manage_sources(self):
        files=list_all_files(); enabled=set(get_enabled())
        if not files: return messagebox.showinfo("Manage Sources","No breach files found in app/breaches.")
        top=tk.Toplevel(self); top.title("Manage Sources"); top.configure(bg=BLACK)
        ttk.Label(top, text="Enable/disable breach files:").pack(anchor="w", padx=10, pady=8)
        vars_map={}; frame=ttk.Frame(top); frame.pack(fill="both", expand=True, padx=10, pady=8)
        for f in files:
            var=tk.BooleanVar(value=(f in enabled) or (len(enabled)==0)); ttk.Checkbutton(frame, text=f, variable=var).pack(anchor="w"); vars_map[f]=var
        def save_and_close():
            selected=[name for name,v in vars_map.items() if v.get()]; set_enabled(selected); messagebox.showinfo("Sources", f"Saved. Enabled files: {len(selected)}"); top.destroy()
        btns=ttk.Frame(top); btns.pack(fill="x", padx=10, pady=10); ttk.Button(btns, text="Save", command=save_and_close).pack(side="right")

    def import_pack(self):
        path=filedialog.askopenfilename(title="Import breach pack", filetypes=[("Data packs",".zip .gz .txt .csv .json"),("All files","*.*")])
        if not path: return
        try:
            base=os.path.basename(path); dest=os.path.join(os.path.dirname(__file__),"breaches",base); import shutil; shutil.copy2(path,dest); self.append(f"Imported: {base}")
        except Exception as e: messagebox.showerror("Import", f"Failed to import: {e}")

    def import_seclists(self):
        from app.services.seclists_import import get_presets, download_files
        presets=get_presets(); top=tk.Toplevel(self); top.title("Import SecLists"); top.configure(bg=BLACK)
        ttk.Label(top, text="Choose presets (download from GitHub):").pack(anchor="w", padx=10, pady=8)
        vars_map=[]; frame=ttk.Frame(top); frame.pack(fill="both", expand=True, padx=10, pady=4)
        for item in presets:
            var=tk.BooleanVar(value=True); ttk.Checkbutton(frame, text=f"{item['label']}", variable=var).pack(anchor="w"); vars_map.append((var,item["url"]))
        ttk.Label(top, text="Or paste additional raw URLs (one per line):").pack(anchor="w", padx=10, pady=(10,4))
        text=tk.Text(top, height=5, width=80, bg="#111111", fg=FG, insertbackground=FG, font=("Consolas",10)); text.pack(fill="both", expand=False, padx=10, pady=(0,10))
        btns=ttk.Frame(top); btns.pack(fill="x", padx=10, pady=10)
        def do_download():
            urls=[url for var,url in vars_map if var.get()]; extra=[line.strip() for line in text.get("1.0","end").splitlines() if line.strip()]; urls.extend(extra)
            if not urls: return messagebox.showwarning("Import SecLists","Select at least one preset or enter URLs.")
            top.destroy(); self.append(f"$ seclists-import ({len(urls)} file(s))")
            self.run_async(lambda: download_files(urls), post=lambda res: ( [self.append(f" - {name}: {status}") for (name,status) in res], self.append("Done. Use Sources / Manage Sources to confirm and enable.") ), spinner="Downloading…")
        ttk.Button(btns, text="Download", command=do_download).pack(side="right"); ttk.Button(btns, text="Cancel", command=top.destroy).pack(side="right", padx=6)

    def do_import_folder(self):
        folder=filedialog.askdirectory(title="Choose a folder to import recursively")
        if not folder: return
        self.append(f"$ import-folder {folder}")
        def work(): return svc_import_folder(folder)
        def post(res):
            for name,status in res: self.append(f" - {name}: {status}")
            self.append("Done. Use Sources / Manage Sources to enable/disable.")
        self.run_async(work, post=post, spinner="Importing…")

    # ---------- Traffic ----------
    def refresh_ifaces(self):
        items=list_interfaces(); menu=self.iface_menu["menu"]; menu.delete(0,"end"); menu.add_command(label="(auto)", command=lambda v="(auto)": self.iface_var.set(v))
        for idx,desc in items:
            lab=f"{idx}: {desc}" if ":" not in str(desc) else str(desc); menu.add_command(label=lab, command=lambda v=lab: self.iface_var.set(v))
        self.iface_var.set("(auto)" if not items else (f"{items[0][0]}: {items[0][1]}" if isinstance(items[0],(tuple,list)) else str(items[0])))

    def do_conn_once(self):
        self.append("$ netstat snapshot"); self.run_async(list_connections, post=lambda out: self.append(out))

    def toggle_conn_auto(self):
        if self.auto_var.get():
            self.append("$ netstat auto-refresh ON (2s)"); self._schedule_conn_refresh()
        else:
            self.append("$ netstat auto-refresh OFF"); 
            if self._conn_auto_job:
                try: self.after_cancel(self._conn_auto_job)
                except Exception: pass
                self._conn_auto_job=None

    def _schedule_conn_refresh(self):
        def do():
            self.run_async(list_connections, post=lambda out: self.append(out)); self._conn_auto_job=self.after(2000, do)
        self._conn_auto_job=self.after(2000, do)

    def _auto_start_capture(self):
        if capture_running(): self.cap_status.config(text="Capture: running"); return
        sel=self.iface_var.get(); iface_idx=None
        if sel and sel!="(auto)":
            try: iface_idx=int(sel.split(":",1)[0].strip())
            except Exception: iface_idx=None
        bpf=self.bpf_var.get().strip() or None
        def post(out):
            self.append("(auto) "+out); self.cap_status.config(text="Capture: running" if "started" in out.lower() else "Capture: (not running)")
        self.run_async(lambda: start_capture(iface_idx, bpf), post=post)

    def do_cap_start(self):
        sel=self.iface_var.get(); iface_idx=None
        if sel and sel!="(auto)":
            try: iface_idx=int(sel.split(":",1)[0].strip())
            except Exception: iface_idx=None
        bpf=self.bpf_var.get().strip() or None
        self.append(f"$ capture start iface={iface_idx if iface_idx is not None else 'auto'} filter={bpf or '(none)'}")
        self.run_async(lambda: start_capture(iface_idx, bpf), post=lambda out: (self.append(out), self.cap_status.config(text="Capture: running" if "started" in out.lower() else "Capture: (not running)")) )

    def do_cap_stop(self):
        self.append("$ capture stop"); self.run_async(stop_capture, post=lambda out: (self.append(out), self.cap_status.config(text="Capture: (not running)")) )

    def do_adapter_stats(self):
        self.append("$ adapter-stats"); self.run_async(adapter_stats, post=lambda out: self.append(out))

    def do_install_scanner(self):
        self.append("$ install-scanner best (Wireshark + Npcap)")
        def post(out):
            self.append(out); self.refresh_ifaces(); self._auto_start_capture()
        self.run_stream(lambda on_update=None: install_best(on_update), post=post, spinner="Installing…")

    # ---------- Settings ----------
    def open_settings(self):
        cfg = cfg_load(); win = tk.Toplevel(self); win.title("Settings"); win.configure(bg=BLACK)
        ttk.Label(win, text="Have I Been Pwned (HIBP) API Key:").pack(anchor="w", padx=10, pady=(10,2))
        hibp_var=tk.StringVar(value=cfg.get("hibp_api_key","")); ttk.Entry(win, textvariable=hibp_var, width=60, show="*").pack(fill="x", padx=10)
        hibp_en=tk.BooleanVar(value=bool(cfg.get("use_hibp_email_scan", False))); ttk.Checkbutton(win, text="Use HIBP for breach scans (email only)", variable=hibp_en).pack(anchor="w", padx=10, pady=4)
        ttk.Label(win, text="Capture rotation:").pack(anchor="w", padx=10, pady=(10,2))
        row=ttk.Frame(win); row.pack(fill="x", padx=10, pady=2)
        ttk.Label(row, text="Duration (sec):").pack(side="left"); dur_var=tk.IntVar(value=int(cfg.get("capture_rotate",{}).get("duration_sec",60))); ttk.Entry(row, textvariable=dur_var, width=8).pack(side="left", padx=8)
        ttk.Label(row, text="File size (MB):").pack(side="left", padx=(12,0)); fsize_var=tk.IntVar(value=int(cfg.get("capture_rotate",{}).get("filesize_mb",20))); ttk.Entry(row, textvariable=fsize_var, width=8).pack(side="left", padx=8)
        ttk.Label(row, text="Files (count):").pack(side="left", padx=(12,0)); files_var=tk.IntVar(value=int(cfg.get("capture_rotate",{}).get("files",5))); ttk.Entry(row, textvariable=files_var, width=8).pack(side="left", padx=8)
        btns=ttk.Frame(win); btns.pack(fill="x", padx=10, pady=10)
        def save_close():
            new_cfg=cfg_load(); new_cfg["hibp_api_key"]=hibp_var.get().strip(); new_cfg["use_hibp_email_scan"]=bool(hibp_en.get())
            new_cfg["capture_rotate"]={"duration_sec": int(max(5,dur_var.get())), "filesize_mb": int(max(1,fsize_var.get())), "files": int(max(1,files_var.get()))}
            cfg_save(new_cfg); self.append("Settings saved."); win.destroy()
        ttk.Button(btns, text="Save", command=save_close).pack(side="right"); ttk.Button(btns, text="Cancel", command=win.destroy).pack(side="right", padx=6)


def safe_main():
    try:
        print("[GUI] Creating window...")
        app = App()
        print("[GUI] Entering mainloop")
        app.mainloop()
        print("[GUI] Mainloop ended")
    except Exception as e:
        import traceback, sys
        print("[Fatal] App failed to start:", repr(e))
        print(traceback.format_exc())
        try:
            import ctypes
            ctypes.windll.user32.MessageBoxW(0, "ISpy failed to start.\n\n" + str(e), "ISpy 0.24.6", 0x10)
        except Exception:
            pass
        sys.exit(1)


if __name__ == "__main__":
    safe_main()
