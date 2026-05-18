import ctypes
import ctypes.wintypes
import time
import threading
import tkinter as tk
from tkinter import messagebox
import json
import os
import sys

# ── Single instance check ──
import socket
_lock_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
try:
    _lock_socket.bind(("127.0.0.1", 47832))
except OSError:
    import sys
    sys.exit(0)  # Already running, exit silently

try:
    import keyboard
except ImportError:
    import subprocess, sys
    subprocess.run([sys.executable, "-m", "pip", "install", "keyboard"],
                   creationflags=0x08000000)
    import keyboard



# Windows API
user32 = ctypes.windll.user32
EnumWindows = user32.EnumWindows
EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.wintypes.HWND, ctypes.wintypes.LPARAM)
GetWindowTextW = user32.GetWindowTextW
IsWindowVisible = user32.IsWindowVisible
PostMessage = user32.PostMessageW

WM_KEYDOWN     = 0x0100
WM_KEYUP       = 0x0101
WM_LBUTTONDOWN = 0x0201
WM_LBUTTONUP   = 0x0202
WM_RBUTTONDOWN = 0x0204
WM_RBUTTONUP   = 0x0205

# SendInput structures for real hardware simulation
import ctypes
from ctypes import wintypes

MOUSEEVENTF_RIGHTDOWN = 0x0008
MOUSEEVENTF_RIGHTUP   = 0x0010

class MOUSEINPUT(ctypes.Structure):
    _fields_ = [("dx", ctypes.c_long), ("dy", ctypes.c_long),
                ("mouseData", wintypes.DWORD), ("dwFlags", wintypes.DWORD),
                ("time", wintypes.DWORD), ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong))]

class INPUT(ctypes.Structure):
    class _INPUT(ctypes.Union):
        _fields_ = [("mi", MOUSEINPUT)]
    _anonymous_ = ("_input",)
    _fields_ = [("type", wintypes.DWORD), ("_input", _INPUT)]

MOUSEEVENTF_MOVE      = 0x0001
MOUSEEVENTF_LEFTDOWN  = 0x0002
MOUSEEVENTF_LEFTUP    = 0x0004

def send_lclick_to_window(hwnd):
    """Focus window briefly, send left click, return focus."""
    prev = ctypes.windll.user32.GetForegroundWindow()
    ctypes.windll.user32.SetForegroundWindow(hwnd)
    time.sleep(0.02)
    i = (INPUT * 2)()
    i[0].type = 0; i[0].mi.dwFlags = MOUSEEVENTF_LEFTDOWN
    i[1].type = 0; i[1].mi.dwFlags = MOUSEEVENTF_LEFTUP
    ctypes.windll.user32.SendInput(2, i, ctypes.sizeof(INPUT))
    time.sleep(0.02)
    if prev: ctypes.windll.user32.SetForegroundWindow(prev)

def send_rclick_down():
    i = INPUT(type=0)
    i.mi.dwFlags = MOUSEEVENTF_RIGHTDOWN
    ctypes.windll.user32.SendInput(1, ctypes.byref(i), ctypes.sizeof(INPUT))

def send_rclick_up():
    i = INPUT(type=0)
    i.mi.dwFlags = MOUSEEVENTF_RIGHTUP
    ctypes.windll.user32.SendInput(1, ctypes.byref(i), ctypes.sizeof(INPUT))

def send_mouse_move_relative(dx, dy):
    """Move mouse by relative pixels using SendInput."""
    i = INPUT(type=0)
    i.mi.dwFlags = MOUSEEVENTF_MOVE
    i.mi.dx = dx
    i.mi.dy = dy
    ctypes.windll.user32.SendInput(1, ctypes.byref(i), ctypes.sizeof(INPUT))

def send_lclick_sendinput():
    """Send left click using SendInput."""
    inputs = (INPUT * 2)()
    inputs[0].type = 0
    inputs[0].mi.dwFlags = MOUSEEVENTF_LEFTDOWN
    inputs[1].type = 0
    inputs[1].mi.dwFlags = MOUSEEVENTF_LEFTUP
    ctypes.windll.user32.SendInput(2, inputs, ctypes.sizeof(INPUT))
VK_G = 0x47

if getattr(sys, 'frozen', False):
    BASE_DIR = os.path.dirname(sys.executable)
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

SETTINGS_FILE = os.path.join(BASE_DIR, "DD2_macro_settings.json")
DEFAULT_SETTINGS = {
    "hotkey": "f5", "interval_ms": 1000,
    "custom_key": "g", "custom_key_hotkey": "f8", "custom_key_interval_ms": 1000,
    "always_on_top": True,
    "attack_hotkey": "f6", "attack_interval_ms": 0,
    "attack_r_hotkey": "f7",
    "attack_r_bpm": 0,
    "combos": [],
    "overlay_visible": True,
    "client1_path": "",
    "client2_path": "",
    "client2_sandboxie": False,
    "sandboxie_path": "C:\\Program Files\\Sandboxie-Plus\\Start.exe",
    "sandboxie_box": "DefaultBox",
    "sandboxie_steam_path": "C:\\Program Files (x86)\\Steam\\steam.exe",
    "talisman_hotkey": "f9", "talisman_key": "1", "talisman_interval_ms": 1000,
    "talisman_key_delay_ms": 300,
    "g_target": "both",
    "custom_target": "both",
    "attack_target": "both",
    "attack_r_target": "both",
    "talisman_target": "both",
}

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r") as f:
                return {**DEFAULT_SETTINGS, **json.load(f)}
        except:
            pass
    return DEFAULT_SETTINGS.copy()

def save_settings(s):
    with open(SETTINGS_FILE, "w") as f:
        json.dump(s, f)

def find_dd2_windows(target="both"):
    """target: 'both', 'client1' (Steam), 'client2' (Sandboxie [#])"""
    handles = []
    def callback(hwnd, _):
        if IsWindowVisible(hwnd):
            buf = ctypes.create_unicode_buffer(256)
            GetWindowTextW(hwnd, buf, 256)
            title = buf.value
            if "Dungeon Defenders 2" not in title:
                return True
            is_sandboxie = title.startswith("[#]")
            if target == "both":
                handles.append(hwnd)
            elif target == "client1" and not is_sandboxie:
                handles.append(hwnd)
            elif target == "client2" and is_sandboxie:
                handles.append(hwnd)
        return True
    EnumWindows(EnumWindowsProc(callback), 0)
    return handles

def get_vk(key_name):
    key_name = key_name.strip().lower()
    aliases = {
        "num0":"numpad0","num1":"numpad1","num2":"numpad2","num3":"numpad3",
        "num4":"numpad4","num5":"numpad5","num6":"numpad6","num7":"numpad7",
        "num8":"numpad8","num9":"numpad9","esc":"escape","del":"delete",
        "ins":"insert","ret":"enter","pgup":"page_up","pgdn":"page_down",
        "caps":"capslock","capslk":"capslock","scrlk":"scrolllock",
    }
    key_name = aliases.get(key_name, key_name)
    vk_map = {
        "a":0x41,"b":0x42,"c":0x43,"d":0x44,"e":0x45,"f":0x46,"g":0x47,
        "h":0x48,"i":0x49,"j":0x4A,"k":0x4B,"l":0x4C,"m":0x4D,"n":0x4E,
        "o":0x4F,"p":0x50,"q":0x51,"r":0x52,"s":0x53,"t":0x54,"u":0x55,
        "v":0x56,"w":0x57,"x":0x58,"y":0x59,"z":0x5A,
        "0":0x30,"1":0x31,"2":0x32,"3":0x33,"4":0x34,
        "5":0x35,"6":0x36,"7":0x37,"8":0x38,"9":0x39,
        "f1":0x70,"f2":0x71,"f3":0x72,"f4":0x73,"f5":0x74,"f6":0x75,
        "f7":0x76,"f8":0x77,"f9":0x78,"f10":0x79,"f11":0x7A,"f12":0x7B,
        "numpad0":0x60,"numpad1":0x61,"numpad2":0x62,"numpad3":0x63,
        "numpad4":0x64,"numpad5":0x65,"numpad6":0x66,"numpad7":0x67,
        "numpad8":0x68,"numpad9":0x69,
        "space":0x20,"enter":0x0D,"tab":0x09,"backspace":0x08,"escape":0x1B,
        "home":0x24,"end":0x23,"insert":0x2D,"delete":0x2E,
        "up":0x26,"down":0x28,"left":0x25,"right":0x27,
        "page_up":0x21,"page_down":0x22,"capslock":0x14,
        "shift":0x10,"ctrl":0x11,"alt":0x12,
        ";":0xBA,"=":0xBB,",":0xBC,"-":0xBD,".":0xBE,"/":0xBF,"`":0xC0,
        "[":0xDB,"]":0xDD,"'":0xDE,
    }
    if key_name.startswith("scan:"):
        try:
            sc = int(key_name.split(":")[1])
            vk = ctypes.windll.user32.MapVirtualKeyW(sc, 3)
            return vk if vk else None
        except:
            return None
    return vk_map.get(key_name)

SCAN_TO_VK = {
    11:"0",2:"1",3:"2",4:"3",5:"4",6:"5",7:"6",8:"7",9:"8",10:"9",
    16:"q",17:"w",18:"e",19:"r",20:"t",21:"y",22:"u",23:"i",24:"o",25:"p",
    30:"a",31:"s",32:"d",33:"f",34:"g",35:"h",36:"j",37:"k",38:"l",
    44:"z",45:"x",46:"c",47:"v",48:"b",49:"n",50:"m",
    59:"f1",60:"f2",61:"f3",62:"f4",63:"f5",64:"f6",
    65:"f7",66:"f8",67:"f9",68:"f10",87:"f11",88:"f12",
    82:"numpad0",79:"numpad1",80:"numpad2",81:"numpad3",
    75:"numpad4",76:"numpad5",77:"numpad6",
    71:"numpad7",72:"numpad8",73:"numpad9",
    57:"space",28:"enter",15:"tab",14:"backspace",1:"escape",
}

NORMALIZE = {
    "left alt":"alt","right alt":"alt","left ctrl":"ctrl","right ctrl":"ctrl",
    "left shift":"shift","right shift":"shift",
    "left windows":"windows","right windows":"windows",
}

# ── Macro loops ──
g_running = False
def send_g_loop(get_interval, get_target):
    global g_running
    while g_running:
        for hwnd in find_dd2_windows(get_target()):
            PostMessage(hwnd, WM_KEYDOWN, VK_G, 0)
            time.sleep(0.05)
            PostMessage(hwnd, WM_KEYUP, VK_G, 0)
        time.sleep(max(0.05, get_interval() / 1000.0))

custom_running = False
def send_custom_loop(get_key, get_interval, get_target):
    global custom_running
    while custom_running:
        vk = get_vk(get_key())
        if vk:
            for hwnd in find_dd2_windows(get_target()):
                PostMessage(hwnd, WM_KEYDOWN, vk, 0)
                time.sleep(0.05)
                PostMessage(hwnd, WM_KEYUP, vk, 0)
        time.sleep(max(0.05, get_interval() / 1000.0))

attack_running = False
def send_attack_loop(get_interval, get_target):
    global attack_running
    interval = get_interval()
    target = get_target()
    if interval == 0:
        # Hold mode - PostMessage to background
        for hwnd in find_dd2_windows(target):
            PostMessage(hwnd, WM_LBUTTONDOWN, 0x0001, 0)
        while attack_running:
            time.sleep(0.05)
        for hwnd in find_dd2_windows(target):
            PostMessage(hwnd, WM_LBUTTONUP, 0, 0)
    else:
        while attack_running:
            for hwnd in find_dd2_windows(target):
                PostMessage(hwnd, WM_LBUTTONDOWN, 0x0001, 0)
                time.sleep(0.05)
                PostMessage(hwnd, WM_LBUTTONUP, 0, 0)
            time.sleep(max(0.05, interval / 1000.0))

attack_r_running = False
def send_attack_r_loop(get_bpm, get_target):
    global attack_r_running
    bpm = get_bpm()
    target = get_target()
    if bpm == 0:
        # Hold mode
        for hwnd in find_dd2_windows(target):
            PostMessage(hwnd, WM_RBUTTONDOWN, 0x0002, 0)
        while attack_r_running:
            time.sleep(0.05)
        for hwnd in find_dd2_windows(target):
            PostMessage(hwnd, WM_RBUTTONUP, 0, 0)
    else:
        # BPM rapid click
        interval = 60.0 / bpm
        click_time = min(0.05, interval * 0.3)
        while attack_r_running:
            for hwnd in find_dd2_windows(target):
                PostMessage(hwnd, WM_RBUTTONDOWN, 0x0002, 0)
            time.sleep(click_time)
            for hwnd in find_dd2_windows(target):
                PostMessage(hwnd, WM_RBUTTONUP, 0, 0)
            time.sleep(max(0.01, interval - click_time))

talisman_running = False
def send_talisman_loop(get_key, get_interval, get_delay, get_target):
    global talisman_running
    while talisman_running:
        vk = get_vk(get_key())
        if vk:
            windows = find_dd2_windows(get_target())
            for hwnd in windows:
                # Press key down and hold briefly
                PostMessage(hwnd, WM_KEYDOWN, vk, 0)
            time.sleep(0.1)
            for hwnd in windows:
                PostMessage(hwnd, WM_KEYUP, vk, 0)
            # Wait for game to process skill selection
            delay = max(0.1, get_delay() / 1000.0)
            time.sleep(delay)
            # Move mouse slightly using SendInput (game sees real movement)
            import random
            dx = random.choice([-15, -10, 10, 15])
            send_mouse_move_relative(dx, 0)
            time.sleep(0.05)
            # Left click using SendInput
            send_lclick_sendinput()
            # Move back
            time.sleep(0.05)
            send_mouse_move_relative(-dx, 0)
        time.sleep(max(0.1, get_interval() / 1000.0))

# ── Overlay ──
class Overlay:
    def __init__(self):
        self.win = tk.Toplevel()
        self.win.overrideredirect(True)
        self.win.attributes("-topmost", True)
        self.win.attributes("-alpha", 0.88)
        self.win.geometry("200x162+20+20")
        self.win.configure(bg="#0a0a18")
        self.canvas = tk.Canvas(self.win, width=200, height=162,
                                bg="#0a0a18", highlightthickness=0)
        self.canvas.pack()
        self._draw_bg()
        self.canvas.create_text(100, 14, text="DD2 MACRO",
                                font=("Segoe UI", 9, "bold"), fill="#5566aa")
        self.canvas.create_line(16, 26, 184, 26, fill="#1e1e3a", width=1)
        self.rows = {}
        items = [
            ("g",        "G Key",       42),
            ("custom",   "Custom Key",  62),
            ("attack",   "Left Click",  82),
            ("attack_r", "Right Click", 102),
            ("talisman", "Talisman",    122),
        ]
        for key, label, y in items:
            self.canvas.create_text(24, y, text=label, font=("Segoe UI", 8),
                                    fill="#8888aa", anchor="w")
            dot_id = self.canvas.create_text(176, y, text="⬤",
                                              font=("Segoe UI", 8),
                                              fill="#1e2040", anchor="e")
            status_id = self.canvas.create_text(160, y, text="OFF",
                                                 font=("Segoe UI", 7, "bold"),
                                                 fill="#2a2a50", anchor="e")
            self.rows[key] = (dot_id, status_id)
        self.canvas.bind("<Button-1>", self._drag_start)
        self.canvas.bind("<B1-Motion>", self._drag_move)
        self._drag_x = self._drag_y = 0

    def _draw_bg(self):
        r, w, h = 10, 200, 162
        self.canvas.create_polygon(
            r,0, w-r,0, w,r, w,h-r, w-r,h, r,h, 0,h-r, 0,r,
            fill="#11112a", outline="#2a2a55", width=1, smooth=True)

    def _drag_start(self, e): self._drag_x, self._drag_y = e.x, e.y
    def _drag_move(self, e):
        x = self.win.winfo_x() + e.x - self._drag_x
        y = self.win.winfo_y() + e.y - self._drag_y
        self.win.geometry(f"+{x}+{y}")

    def update(self, key, active):
        dot_id, status_id = self.rows[key]
        if active:
            self.canvas.itemconfig(dot_id, fill="#00dd77")
            self.canvas.itemconfig(status_id, text="ON", fill="#00aa55")
        else:
            self.canvas.itemconfig(dot_id, fill="#1e2040")
            self.canvas.itemconfig(status_id, text="OFF", fill="#2a2a50")

    def show(self):
        self.win.deiconify()

    def hide(self):
        self.win.withdraw()

# ── Panel helper ──
BG = "#1a1a2e"
BG2 = "#12122a"
ACCENT = "#2a2a55"

def make_panel(parent, title):
    """Creates a styled panel frame with title."""
    outer = tk.Frame(parent, bg=ACCENT, padx=1, pady=1)
    inner = tk.Frame(outer, bg=BG2)
    inner.pack(fill="both", expand=True)
    tk.Label(inner, text=title, font=("Segoe UI", 10, "bold"),
             bg=BG2, fg="#7788cc").pack(pady=(6,2))
    return outer, inner

# ── Main GUI ──
class App:
    def __init__(self, root):
        self.root = root
        self.root.title("DD2 Macro")
        self.root.configure(bg=BG)
        self.root.resizable(False, False)

        self.settings = load_settings()
        self.current_hotkey      = self.settings["hotkey"]
        self.attack_hotkey       = self.settings["attack_hotkey"]
        self.attack_r_hotkey     = self.settings["attack_r_hotkey"]
        self.attack_r_bpm_var    = tk.StringVar(value=str(self.settings["attack_r_bpm"]))
        self.custom_key_hotkey   = self.settings["custom_key_hotkey"]
        self.talisman_hotkey     = self.settings["talisman_hotkey"]
        self.always_on_top_var   = tk.BooleanVar(value=self.settings["always_on_top"])
        self.overlay_visible_var  = tk.BooleanVar(value=self.settings.get("overlay_visible", True))
        self.client1_path_var     = tk.StringVar(value=self.settings.get("client1_path", ""))
        self.client2_path_var     = tk.StringVar(value=self.settings.get("client2_path", ""))
        self.client2_sandboxie_var = tk.BooleanVar(value=self.settings.get("client2_sandboxie", False))
        self.sandboxie_path_var    = tk.StringVar(value=self.settings.get("sandboxie_path", "C:\\Program Files\\Sandboxie-Plus\\Start.exe"))
        self.sandboxie_box_var     = tk.StringVar(value=self.settings.get("sandboxie_box", "DefaultBox"))
        self.sandboxie_steam_var   = tk.StringVar(value=self.settings.get("sandboxie_steam_path", "C:\\Program Files (x86)\\Steam\\steam.exe"))
        self.sandman_path_var      = tk.StringVar(value=self.settings.get("sandman_path", "C:\\Program Files\\Sandboxie-Plus\\SandMan.exe"))
        self.client1_steam_var     = tk.StringVar(value=self.settings.get("client1_steam_path", "C:\\Program Files (x86)\\Steam\\steam.exe"))
        self.root.attributes("-topmost", self.settings["always_on_top"])

        self.listening        = False
        self.listening_target = None
        self._alt_pressed     = False
        self._listening_custom_key  = False
        self._listening_talisman_key = False

        self.hotkey_handles = {
            "g":None,"attack":None,"attack_r":None,"custom":None,"talisman":None
        }

        # StringVars
        self.g_interval_var        = tk.StringVar(value=str(self.settings["interval_ms"]))
        self.attack_interval_var   = tk.StringVar(value=str(self.settings["attack_interval_ms"]))
        self.custom_key_var        = tk.StringVar(value=self.settings["custom_key"])
        self.custom_interval_var   = tk.StringVar(value=str(self.settings["custom_key_interval_ms"]))
        self.talisman_key_var      = tk.StringVar(value=self.settings["talisman_key"])
        self.talisman_interval_var = tk.StringVar(value=str(self.settings["talisman_interval_ms"]))
        self.talisman_delay_var    = tk.StringVar(value=str(self.settings["talisman_key_delay_ms"]))
        self.g_target_var        = tk.StringVar(value=self.settings["g_target"])
        self.custom_target_var   = tk.StringVar(value=self.settings["custom_target"])
        self.attack_target_var   = tk.StringVar(value=self.settings["attack_target"])
        self.attack_r_target_var = tk.StringVar(value=self.settings["attack_r_target"])
        self.talisman_target_var = tk.StringVar(value=self.settings["talisman_target"])

        # ── Title ──
        tk.Label(root, text="DD2 Macro", font=("Segoe UI", 15, "bold"),
                 bg=BG, fg="white").pack(pady=(10,4))

        # ── Tabs ──
        from tkinter import ttk
        style = ttk.Style()
        style.theme_use("default")
        style.configure("TNotebook", background=BG, borderwidth=0)
        style.configure("TNotebook.Tab", background=ACCENT, foreground="white",
                        font=("Segoe UI", 9, "bold"), padding=[12, 4])
        style.map("TNotebook.Tab",
                  background=[("selected", "#4a4a88")],
                  foreground=[("selected", "white")])

        notebook = ttk.Notebook(root)
        notebook.pack(fill="both", expand=True, padx=4, pady=4)

        self.main_tab   = tk.Frame(notebook, bg=BG)
        self.custom_tab = tk.Frame(notebook, bg=BG)
        notebook.add(self.main_tab,   text="  Main  ")
        notebook.add(self.custom_tab, text="  Custom  ")

        root = self.main_tab

        # ── Top row: G Key + Custom Key ──
        top_row = tk.Frame(root, bg=BG)
        top_row.pack(fill="x", padx=8, pady=4)

        g_outer, g_panel = make_panel(top_row, "G KEY MACRO")
        g_outer.pack(side="left", fill="both", expand=True, padx=(0,4))
        self.g_status = self._status_lbl(g_panel)
        self.g_btn    = self._toggle_btn(g_panel, self.toggle_g)
        self._interval_field(g_panel, self.g_interval_var, self.save_g_interval)
        self.g_bind_btn = self._bind_btn(g_panel, self.current_hotkey, "g")
        _cf = tk.Frame(g_panel, bg=BG2)
        _cf.pack(pady=(3,4))
        tk.Label(_cf, text="Client:", font=("Segoe UI", 9), bg=BG2, fg="#aaaaaa").pack(side="left", padx=(0,4))
        tk.OptionMenu(_cf, self.g_target_var, "both", "client1", "client2",
                      command=lambda _: self._save_all()).pack(side="left")

        cust_outer, cust_panel = make_panel(top_row, "CUSTOM KEY")
        cust_outer.pack(side="left", fill="both", expand=True)
        self.custom_status = self._status_lbl(cust_panel)
        self.custom_btn    = self._toggle_btn(cust_panel, self.toggle_custom)
        self._key_detect_field(cust_panel, self.custom_key_var, self.start_listening_custom_key)
        self._interval_field(cust_panel, self.custom_interval_var, self.save_custom)
        self.custom_bind_btn = self._bind_btn(cust_panel, self.custom_key_hotkey, "custom")
        _cf = tk.Frame(cust_panel, bg=BG2)
        _cf.pack(pady=(3,4))
        tk.Label(_cf, text="Client:", font=("Segoe UI", 9), bg=BG2, fg="#aaaaaa").pack(side="left", padx=(0,4))
        tk.OptionMenu(_cf, self.custom_target_var, "both", "client1", "client2",
                      command=lambda _: self._save_all()).pack(side="left")

        # ── Middle row: Left Click + Right Click ──
        mid_row = tk.Frame(root, bg=BG)
        mid_row.pack(fill="x", padx=8, pady=4)

        lc_outer, lc_panel = make_panel(mid_row, "LEFT CLICK")
        lc_outer.pack(side="left", fill="both", expand=True, padx=(0,4))
        tk.Label(lc_panel, text="0=hold  >0=click/N ms",
                 font=("Segoe UI", 9), bg=BG2, fg="#666688").pack()
        self.attack_status = self._status_lbl(lc_panel)
        self.attack_btn    = self._toggle_btn(lc_panel, self.toggle_attack)
        self._interval_field(lc_panel, self.attack_interval_var, self.save_attack_interval)
        self.attack_bind_btn = self._bind_btn(lc_panel, self.attack_hotkey, "attack")
        _cf = tk.Frame(lc_panel, bg=BG2)
        _cf.pack(pady=(3,4))
        tk.Label(_cf, text="Client:", font=("Segoe UI", 9), bg=BG2, fg="#aaaaaa").pack(side="left", padx=(0,4))
        tk.OptionMenu(_cf, self.attack_target_var, "both", "client1", "client2",
                      command=lambda _: self._save_all()).pack(side="left")

        rc_outer, rc_panel = make_panel(mid_row, "RIGHT CLICK")
        rc_outer.pack(side="left", fill="both", expand=True)
        tk.Label(rc_panel, text="0=hold  >0=BPM rapid click",
                 font=("Segoe UI", 9), bg=BG2, fg="#666688").pack()
        self.attack_r_status = self._status_lbl(rc_panel)
        self.attack_r_btn    = self._toggle_btn(rc_panel, self.toggle_attack_r)
        atk_r_bpm_frame = tk.Frame(rc_panel, bg=BG2)
        atk_r_bpm_frame.pack(pady=(2,0))
        tk.Label(atk_r_bpm_frame, text="BPM:", font=("Segoe UI", 9),
                 bg=BG2, fg="#aaaaaa").pack(side="left", padx=(0,4))
        tk.Entry(atk_r_bpm_frame, textvariable=self.attack_r_bpm_var,
                 font=("Segoe UI", 9), width=6, bg="white", fg="black",
                 relief="flat").pack(side="left", padx=(0,4))
        tk.Button(atk_r_bpm_frame, text="Save", font=("Segoe UI", 9),
                  bg=ACCENT, fg="white", relief="flat", cursor="hand2",
                  command=self.save_attack_r_bpm).pack(side="left")
        self.attack_r_bind_btn = self._bind_btn(rc_panel, self.attack_r_hotkey, "attack_r")
        _cf = tk.Frame(rc_panel, bg=BG2)
        _cf.pack(pady=(3,4))
        tk.Label(_cf, text="Client:", font=("Segoe UI", 9), bg=BG2, fg="#aaaaaa").pack(side="left", padx=(0,4))
        tk.OptionMenu(_cf, self.attack_r_target_var, "both", "client1", "client2",
                      command=lambda _: self._save_all()).pack(side="left")

        # ── Bottom row: Talisman (full width) ──
        bot_row = tk.Frame(root, bg=BG)
        bot_row.pack(fill="x", padx=8, pady=4)

        tal_outer, tal_panel = make_panel(bot_row, "TALISMAN BUFF  (Key + Left Click)")
        tal_outer.pack(fill="x")
        tk.Label(tal_panel, text="Presses skill key then left clicks at interval",
                 font=("Segoe UI", 9), bg=BG2, fg="#666688").pack()
        self.talisman_status = self._status_lbl(tal_panel)

        tal_mid = tk.Frame(tal_panel, bg=BG2)
        tal_mid.pack(pady=2)
        self.talisman_btn = self._toggle_btn(tal_mid, self.toggle_talisman, width=18)
        self.talisman_btn.pack_forget()
        self.talisman_btn = tk.Button(tal_mid, text="► Start", font=("Segoe UI", 10),
                                      bg=ACCENT, fg="white", relief="flat",
                                      width=18, height=1, cursor="hand2",
                                      command=self.toggle_talisman)
        self.talisman_btn.pack(side="left", padx=(0,8))

        tal_fields = tk.Frame(tal_mid, bg=BG2)
        tal_fields.pack(side="left")
        self._key_detect_field(tal_fields, self.talisman_key_var, self.start_listening_talisman_key)
        self._interval_field(tal_fields, self.talisman_interval_var, self.save_talisman)
        self._delay_field(tal_fields, self.talisman_delay_var, self.save_talisman)

        self.talisman_bind_btn = self._bind_btn(tal_panel, self.talisman_hotkey, "talisman")
        _cf = tk.Frame(tal_panel, bg=BG2)
        _cf.pack(pady=(3,4))
        tk.Label(_cf, text="Client:", font=("Segoe UI", 9), bg=BG2, fg="#aaaaaa").pack(side="left", padx=(0,4))
        tk.OptionMenu(_cf, self.talisman_target_var, "both", "client1", "client2",
                      command=lambda _: self._save_all()).pack(side="left")

        # ── Always on top ──
        aot_frame = tk.Frame(root, bg=BG)
        aot_frame.pack(pady=(2,10))
        tk.Checkbutton(aot_frame, text="Always on top",
                       variable=self.always_on_top_var,
                       font=("Segoe UI", 11), bg=BG, fg="white",
                       selectcolor=ACCENT, activebackground=BG,
                       activeforeground="white", cursor="hand2",
                       command=self.toggle_always_on_top).pack()
        tk.Checkbutton(aot_frame, text="Show overlay",
                       variable=self.overlay_visible_var,
                       font=("Segoe UI", 11), bg=BG, fg="white",
                       selectcolor=ACCENT, activebackground=BG,
                       activeforeground="white", cursor="hand2",
                       command=self.toggle_overlay).pack()

        # ── Launch Clients ──
        tk.Frame(root, bg=ACCENT, height=1).pack(fill="x", padx=8, pady=(4,4))
        tk.Label(root, text="Launch Clients", font=("Segoe UI", 9, "bold"),
                 bg=BG, fg="#aaaaaa").pack()

        # Client 1
        c1_row = tk.Frame(root, bg=BG)
        c1_row.pack(fill="x", padx=8, pady=(2,0))
        tk.Label(c1_row, text="Client 1:", font=("Segoe UI", 9),
                 bg=BG, fg="#aaaaaa", width=7, anchor="w").pack(side="left")
        tk.Entry(c1_row, textvariable=self.client1_path_var,
                 font=("Segoe UI", 8), bg="white", fg="black",
                 relief="flat").pack(side="left", fill="x", expand=True, padx=(0,4))
        tk.Button(c1_row, text="...", font=("Segoe UI", 9),
                  bg=ACCENT, fg="white", relief="flat", cursor="hand2",
                  command=lambda: self._browse_client(self.client1_path_var)
                  ).pack(side="left", padx=(0,4))
        tk.Button(c1_row, text="▶ Launch", font=("Segoe UI", 9),
                  bg="#1a3a1a", fg="#44cc44", relief="flat", cursor="hand2",
                  command=self._launch_client1
                  ).pack(side="left")

        c1_steam_row = tk.Frame(root, bg=BG)
        c1_steam_row.pack(fill="x", padx=8, pady=(2,4))
        tk.Label(c1_steam_row, text="Steam:", font=("Segoe UI", 9),
                 bg=BG, fg="#aaaaaa", width=7, anchor="w").pack(side="left")
        tk.Entry(c1_steam_row, textvariable=self.client1_steam_var,
                 font=("Segoe UI", 8), bg="white", fg="black",
                 relief="flat").pack(side="left", fill="x", expand=True, padx=(0,4))
        tk.Button(c1_steam_row, text="...", font=("Segoe UI", 9),
                  bg=ACCENT, fg="white", relief="flat", cursor="hand2",
                  command=lambda: self._browse_client(self.client1_steam_var)
                  ).pack(side="left")

        # Client 2
        c2_row = tk.Frame(root, bg=BG)
        c2_row.pack(fill="x", padx=8, pady=(4,4))
        tk.Label(c2_row, text="Client 2:", font=("Segoe UI", 9),
                 bg=BG, fg="#aaaaaa", width=7, anchor="w").pack(side="left")
        tk.Entry(c2_row, textvariable=self.client2_path_var,
                 font=("Segoe UI", 8), bg="white", fg="black",
                 relief="flat").pack(side="left", fill="x", expand=True, padx=(0,4))
        tk.Button(c2_row, text="...", font=("Segoe UI", 9),
                  bg=ACCENT, fg="white", relief="flat", cursor="hand2",
                  command=lambda: self._browse_client(self.client2_path_var)
                  ).pack(side="left", padx=(0,4))
        tk.Button(c2_row, text="▶ Launch", font=("Segoe UI", 9),
                  bg="#1a3a1a", fg="#44cc44", relief="flat", cursor="hand2",
                  command=lambda: self._launch_client2()
                  ).pack(side="left")

        # Sandboxie options
        sbx_frame = tk.Frame(root, bg=BG)
        sbx_frame.pack(fill="x", padx=8, pady=(2,4))
        tk.Checkbutton(sbx_frame, text="Launch Client 2 via Sandboxie",
                       variable=self.client2_sandboxie_var,
                       font=("Segoe UI", 9), bg=BG, fg="white",
                       selectcolor=ACCENT, activebackground=BG,
                       activeforeground="white", cursor="hand2",
                       command=self._save_all).pack(anchor="w")

        sbx_path_row = tk.Frame(root, bg=BG)
        sbx_path_row.pack(fill="x", padx=8, pady=(0,2))
        tk.Label(sbx_path_row, text="Start.exe:", font=("Segoe UI", 9),
                 bg=BG, fg="#aaaaaa", width=7, anchor="w").pack(side="left")
        tk.Entry(sbx_path_row, textvariable=self.sandboxie_path_var,
                 font=("Segoe UI", 8), bg="white", fg="black",
                 relief="flat").pack(side="left", fill="x", expand=True, padx=(0,4))
        tk.Button(sbx_path_row, text="...", font=("Segoe UI", 9),
                  bg=ACCENT, fg="white", relief="flat", cursor="hand2",
                  command=lambda: self._browse_client(self.sandboxie_path_var)
                  ).pack(side="left")

        sbx_box_row = tk.Frame(root, bg=BG)
        sbx_box_row.pack(fill="x", padx=8, pady=(0,4))
        tk.Label(sbx_box_row, text="Box name:", font=("Segoe UI", 9),
                 bg=BG, fg="#aaaaaa", width=7, anchor="w").pack(side="left")
        tk.Entry(sbx_box_row, textvariable=self.sandboxie_box_var,
                 font=("Segoe UI", 9), bg="white", fg="black",
                 relief="flat", width=20).pack(side="left", padx=(0,4))
        tk.Button(sbx_box_row, text="Save", font=("Segoe UI", 9),
                  bg=ACCENT, fg="white", relief="flat", cursor="hand2",
                  command=self._save_all).pack(side="left")

        sbx_sandman_row = tk.Frame(root, bg=BG)
        sbx_sandman_row.pack(fill="x", padx=8, pady=(0,2))
        tk.Label(sbx_sandman_row, text="SandMan:", font=("Segoe UI", 9),
                 bg=BG, fg="#aaaaaa", width=7, anchor="w").pack(side="left")
        tk.Entry(sbx_sandman_row, textvariable=self.sandman_path_var,
                 font=("Segoe UI", 8), bg="white", fg="black",
                 relief="flat").pack(side="left", fill="x", expand=True, padx=(0,4))
        tk.Button(sbx_sandman_row, text="...", font=("Segoe UI", 9),
                  bg=ACCENT, fg="white", relief="flat", cursor="hand2",
                  command=lambda: self._browse_client(self.sandman_path_var)
                  ).pack(side="left")

        sbx_steam_row = tk.Frame(root, bg=BG)
        sbx_steam_row.pack(fill="x", padx=8, pady=(0,4))
        tk.Label(sbx_steam_row, text="Steam:", font=("Segoe UI", 9),
                 bg=BG, fg="#aaaaaa", width=7, anchor="w").pack(side="left")
        tk.Entry(sbx_steam_row, textvariable=self.sandboxie_steam_var,
                 font=("Segoe UI", 8), bg="white", fg="black",
                 relief="flat").pack(side="left", fill="x", expand=True, padx=(0,4))
        tk.Button(sbx_steam_row, text="...", font=("Segoe UI", 9),
                  bg=ACCENT, fg="white", relief="flat", cursor="hand2",
                  command=lambda: self._browse_client(self.sandboxie_steam_var)
                  ).pack(side="left")

        tk.Button(root, text="▶ Launch Steam + Game in Sandbox",
                  font=("Segoe UI", 9), bg="#1a2a3a", fg="#44aaff",
                  relief="flat", cursor="hand2", pady=4,
                  command=self._launch_sandboxie_full
                  ).pack(fill="x", padx=8, pady=(0,4))

        tk.Button(root, text="⚠ Kill All Game Processes",
                  font=("Segoe UI", 10, "bold"), bg="#880000", fg="white",
                  relief="flat", cursor="hand2", pady=6,
                  command=self.kill_all_games).pack(fill="x", padx=8, pady=(4,10))

        self.root.update_idletasks()
        w = self.root.winfo_reqwidth()
        h = self.root.winfo_reqheight() + 60
        self.root.geometry(f"{w}x{h}")

        # ── Custom Tab ──
        self._build_custom_tab()

        self._apply_hotkey("g",        self.current_hotkey,    save=False)
        self._apply_hotkey("attack",   self.attack_hotkey,     save=False)
        self._apply_hotkey("attack_r", self.attack_r_hotkey,   save=False)
        self._apply_hotkey("custom",   self.custom_key_hotkey, save=False)
        self._apply_hotkey("talisman", self.talisman_hotkey,   save=False)

        self.overlay = Overlay()
        if not self.settings.get("overlay_visible", True):
            self.overlay.hide()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    # ── UI helpers ──
    def _status_lbl(self, parent):
        lbl = tk.Label(parent, text="● INACTIVE", font=("Segoe UI", 11, "bold"),
                       bg=BG2, fg="#ff4444")
        lbl.pack(pady=(2,0))
        return lbl

    def _toggle_btn(self, parent, cmd, width=20):
        btn = tk.Button(parent, text="► Start", font=("Segoe UI", 10),
                        bg=ACCENT, fg="white", relief="flat",
                        width=width, height=1, cursor="hand2", command=cmd)
        btn.pack(pady=4)
        return btn

    def _interval_field(self, parent, var, save_cmd):
        f = tk.Frame(parent, bg=BG2)
        f.pack(pady=2)
        tk.Label(f, text="Interval ms:", font=("Segoe UI", 9),
                 bg=BG2, fg="#aaaaaa").pack(side="left", padx=(0,2))
        tk.Entry(f, textvariable=var, font=("Segoe UI", 9),
                 width=6, bg="white", fg="black", relief="flat").pack(side="left", padx=(0,3))
        tk.Button(f, text="Save", font=("Segoe UI", 9),
                  bg=ACCENT, fg="white", relief="flat", cursor="hand2",
                  command=save_cmd).pack(side="left")

    def _delay_field(self, parent, var, save_cmd):
        f = tk.Frame(parent, bg=BG2)
        f.pack(pady=2)
        tk.Label(f, text="Key delay ms:", font=("Segoe UI", 9),
                 bg=BG2, fg="#aaaaaa").pack(side="left", padx=(0,2))
        tk.Entry(f, textvariable=var, font=("Segoe UI", 9),
                 width=6, bg="white", fg="black", relief="flat").pack(side="left", padx=(0,3))
        tk.Button(f, text="Save", font=("Segoe UI", 9),
                  bg=ACCENT, fg="white", relief="flat", cursor="hand2",
                  command=save_cmd).pack(side="left")

    def _key_detect_field(self, parent, var, detect_cmd):
        f = tk.Frame(parent, bg=BG2)
        f.pack(pady=2)
        tk.Label(f, text="Key:", font=("Segoe UI", 9),
                 bg=BG2, fg="#aaaaaa").pack(side="left", padx=(0,2))
        tk.Entry(f, textvariable=var, font=("Segoe UI", 9),
                 width=6, bg="white", fg="black", relief="flat").pack(side="left", padx=(0,3))
        btn = tk.Button(f, text="Detect", font=("Segoe UI", 9),
                        bg=ACCENT, fg="white", relief="flat", cursor="hand2",
                        command=detect_cmd)
        btn.pack(side="left")
        return btn

    def _bind_btn(self, parent, current_key, target):
        btn = tk.Button(parent,
                        text=f"Hotkey: {current_key}",
                        font=("Segoe UI", 9), bg="#222244", fg="#aaaacc",
                        relief="flat", cursor="hand2", pady=3,
                        command=lambda t=target: self.start_listening(t))
        btn.pack(fill="x", padx=6, pady=(2,6))
        return btn

    # ── Getters ──
    def get_g_interval(self):
        try: return max(100, int(self.g_interval_var.get()))
        except: return 1000
    def get_attack_interval(self):
        try: return max(0, int(self.attack_interval_var.get()))
        except: return 0
    def get_custom_interval(self):
        try: return max(100, int(self.custom_interval_var.get()))
        except: return 1000
    def get_custom_key(self):
        return self.custom_key_var.get().strip().lower()
    def get_talisman_interval(self):
        try: return max(100, int(self.talisman_interval_var.get()))
        except: return 1000
    def get_attack_r_bpm(self):
        try: return max(0, int(self.attack_r_bpm_var.get()))
        except: return 0

    def save_attack_r_bpm(self):
        try:
            self._save_all()
        except: messagebox.showerror("Error", "Please enter a valid number!")

    def get_g_target(self):        return self.g_target_var.get()
    def get_custom_target(self):   return self.custom_target_var.get()
    def get_attack_target(self):   return self.attack_target_var.get()
    def get_attack_r_target(self): return self.attack_r_target_var.get()
    def get_talisman_target(self): return self.talisman_target_var.get()

    def get_talisman_delay(self):
        try: return max(0, int(self.talisman_delay_var.get()))
        except: return 300

    def get_talisman_key(self):
        return self.talisman_key_var.get().strip().lower()

    # ── Save ──
    def _save_all(self):
        save_settings({
            "hotkey": self.current_hotkey, "interval_ms": self.get_g_interval(),
            "custom_key": self.get_custom_key(), "custom_key_hotkey": self.custom_key_hotkey,
            "custom_key_interval_ms": self.get_custom_interval(),
            "always_on_top": self.always_on_top_var.get(),
            "attack_hotkey": self.attack_hotkey, "attack_interval_ms": self.get_attack_interval(),
            "attack_r_hotkey": self.attack_r_hotkey, "attack_r_bpm": self.get_attack_r_bpm(),
            "talisman_hotkey": self.talisman_hotkey,
            "talisman_key": self.get_talisman_key(),
            "talisman_interval_ms": self.get_talisman_interval(),
            "talisman_key_delay_ms": self.get_talisman_delay(),
            "g_target": self.get_g_target(),
            "custom_target": self.get_custom_target(),
            "attack_target": self.get_attack_target(),
            "attack_r_target": self.get_attack_r_target(),
            "talisman_target": self.get_talisman_target(),
            "combos": self.combos,
            "overlay_visible": self.overlay_visible_var.get(),
            "client1_path": self.client1_path_var.get(),
            "client2_path": self.client2_path_var.get(),
            "client2_sandboxie": self.client2_sandboxie_var.get(),
            "sandboxie_path": self.sandboxie_path_var.get(),
            "sandboxie_box": self.sandboxie_box_var.get(),
            "sandboxie_steam_path": self.sandboxie_steam_var.get(),
            "sandman_path": self.sandman_path_var.get(),
            "client1_steam_path": self.client1_steam_var.get(),
        })

    def save_g_interval(self):
        try:
            if int(self.g_interval_var.get()) < 100: messagebox.showerror("Error","Min 100 ms!"); return
            self._save_all()
        except: messagebox.showerror("Error","Invalid number!")

    def save_attack_interval(self):
        try: self._save_all()
        except: messagebox.showerror("Error","Invalid number!")

    def save_custom(self):
        try:
            if int(self.custom_interval_var.get()) < 100: messagebox.showerror("Error","Min 100 ms!"); return
            self._save_all()
        except: messagebox.showerror("Error","Invalid number!")

    def save_talisman(self):
        try:
            if int(self.talisman_interval_var.get()) < 100: messagebox.showerror("Error","Min 100 ms!"); return
            self._save_all()
        except: messagebox.showerror("Error","Invalid number!")

    def toggle_always_on_top(self):
        self.root.attributes("-topmost", self.always_on_top_var.get())
        self._save_all()

    def toggle_overlay(self):
        if self.overlay_visible_var.get():
            self.overlay.show()
        else:
            self.overlay.hide()
        self._save_all()

    # ── Toggles ──
    def _set_active(self, btn, status_lbl, overlay_key, active):
        if active:
            btn.config(text="■ Stop", bg="#cc0000")
            status_lbl.config(text="● ACTIVE", fg="#00cc66")
        else:
            btn.config(text="► Start", bg=ACCENT)
            status_lbl.config(text="● INACTIVE", fg="#ff4444")
        self.overlay.update(overlay_key, active)

    def toggle_g(self):
        global g_running
        g_running = not g_running
        self._set_active(self.g_btn, self.g_status, "g", g_running)
        if g_running:
            threading.Thread(target=send_g_loop, args=(self.get_g_interval, self.get_g_target), daemon=True).start()

    def toggle_custom(self):
        global custom_running
        custom_running = not custom_running
        self._set_active(self.custom_btn, self.custom_status, "custom", custom_running)
        if custom_running:
            threading.Thread(target=send_custom_loop,
                             args=(self.get_custom_key, self.get_custom_interval, self.get_custom_target), daemon=True).start()

    def toggle_attack(self):
        global attack_running
        attack_running = not attack_running
        self._set_active(self.attack_btn, self.attack_status, "attack", attack_running)
        if attack_running:
            threading.Thread(target=send_attack_loop, args=(self.get_attack_interval, self.get_attack_target), daemon=True).start()

    def toggle_attack_r(self):
        global attack_r_running
        attack_r_running = not attack_r_running
        self._set_active(self.attack_r_btn, self.attack_r_status, "attack_r", attack_r_running)
        if attack_r_running:
            threading.Thread(target=send_attack_r_loop, args=(self.get_attack_r_bpm, self.get_attack_r_target), daemon=True).start()

    def toggle_talisman(self):
        global talisman_running
        talisman_running = not talisman_running
        self._set_active(self.talisman_btn, self.talisman_status, "talisman", talisman_running)
        if talisman_running:
            threading.Thread(target=send_talisman_loop,
                             args=(self.get_talisman_key, self.get_talisman_interval, self.get_talisman_delay, self.get_talisman_target), daemon=True).start()

    # ── Hotkey binding ──
    def _apply_hotkey(self, target, key, save=True):
        if self.hotkey_handles[target] is not None:
            try: keyboard.remove_hotkey(self.hotkey_handles[target])
            except: pass
        toggle_fn = {
            "g": self.toggle_g, "attack": self.toggle_attack,
            "attack_r": self.toggle_attack_r, "custom": self.toggle_custom,
            "talisman": self.toggle_talisman,
        }[target]
        try:
            self.hotkey_handles[target] = keyboard.add_hotkey(key, toggle_fn, suppress=False)
            if target == "g":          self.current_hotkey    = key
            elif target == "attack":   self.attack_hotkey     = key
            elif target == "attack_r": self.attack_r_hotkey   = key
            elif target == "custom":   self.custom_key_hotkey = key
            elif target == "talisman": self.talisman_hotkey   = key
        except Exception as ex:
            messagebox.showerror("Error", f"Could not bind key: {key}\n{ex}")
        if save: self._save_all()

    def start_listening(self, target):
        if self.listening: return
        self.listening = True
        self.listening_target = target
        self._alt_pressed = False

        # Update button text
        if target.startswith("combo_"):
            idx = int(target.split("_")[1])
            if idx < len(self.combo_frames):
                self.combo_frames[idx]["hk_btn"].config(
                    text=">> Press any key <<", bg="#553300")
        else:
            btn_map = {
                "g": self.g_bind_btn, "attack": self.attack_bind_btn,
                "attack_r": self.attack_r_bind_btn, "custom": self.custom_bind_btn,
                "talisman": self.talisman_bind_btn,
            }
            btn_map[target].config(text=">> Press any key <<", bg="#553300")

        # Temporarily disable all hotkeys to prevent triggering
        for h in list(self.hotkey_handles.values()):
            if h is not None:
                try: keyboard.remove_hotkey(h)
                except: pass
        # Disable combo hotkeys too
        if hasattr(self, "combo_frames"):
            for cf in self.combo_frames:
                h = cf.get("handle", [None])[0]
                if h:
                    try: keyboard.remove_hotkey(h)
                    except: pass

        keyboard.hook(self.capture_key, suppress=True)

    def capture_key(self, event):
        if not self.listening: return
        name = NORMALIZE.get(event.name, event.name)
        if name == "alt":
            if event.event_type == "down": self._alt_pressed = True
            elif event.event_type == "up" and self._alt_pressed:
                self.listening = False
                self._alt_pressed = False
                keyboard.unhook(self.capture_key)
                target = self.listening_target
                self.root.after(0, lambda: self._finish_bind(target, "alt"))
            return
        if event.event_type != "down": return
        if name in ("ctrl","shift","windows"): return
        self._alt_pressed = False
        self.listening = False
        keyboard.unhook(self.capture_key)
        mods = []
        if keyboard.is_pressed("ctrl"):  mods.append("ctrl")
        if keyboard.is_pressed("shift"): mods.append("shift")
        if keyboard.is_pressed("alt"):   mods.append("alt")
        full_key = "+".join(mods + [name]) if mods else name
        target = self.listening_target
        self.root.after(0, lambda: self._finish_bind(target, full_key))

    def _finish_bind(self, target, full_key):
        # Re-apply all main hotkeys
        self._apply_hotkey("g",        self.current_hotkey,    save=False)
        self._apply_hotkey("attack",   self.attack_hotkey,     save=False)
        self._apply_hotkey("attack_r", self.attack_r_hotkey,   save=False)
        self._apply_hotkey("custom",   self.custom_key_hotkey, save=False)
        self._apply_hotkey("talisman", self.talisman_hotkey,   save=False)

        if target.startswith("combo_"):
            idx = int(target.split("_")[1])
            if idx < len(self.combo_frames):
                self.combo_frames[idx]["hk_apply"](full_key)
            return

        self._apply_hotkey(target, full_key)
        btn_map = {
            "g": self.g_bind_btn, "attack": self.attack_bind_btn,
            "attack_r": self.attack_r_bind_btn, "custom": self.custom_bind_btn,
            "talisman": self.talisman_bind_btn,
        }
        btn_map[target].config(text=f"Hotkey: {full_key}", bg="#222244")

    # ── Key detect for custom / talisman ──
    def _do_key_detect(self, on_done):
        keyboard.hook(lambda e: self._capture_detect_key(e, on_done))

    def _capture_detect_key(self, event, on_done):
        if event.event_type != "down": return
        name = NORMALIZE.get(event.name, event.name)
        if name in ("ctrl","shift","alt","windows"): return
        keyboard.unhook_all()
        # Re-hook hotkeys
        for target, handle in self.hotkey_handles.items():
            if handle is not None:
                try: keyboard.remove_hotkey(handle)
                except: pass
        for target in list(self.hotkey_handles.keys()):
            toggle_fn = {
                "g": self.toggle_g, "attack": self.toggle_attack,
                "attack_r": self.toggle_attack_r, "custom": self.toggle_custom,
                "talisman": self.toggle_talisman,
            }[target]
            hk = getattr(self, {
                "g":"current_hotkey","attack":"attack_hotkey","attack_r":"attack_r_hotkey",
                "custom":"custom_key_hotkey","talisman":"talisman_hotkey"
            }[target])
            try:
                self.hotkey_handles[target] = keyboard.add_hotkey(hk, toggle_fn, suppress=False)
            except: pass
        key_name = SCAN_TO_VK.get(event.scan_code, f"scan:{event.scan_code}")
        self.root.after(0, lambda: on_done(key_name))

    def start_listening_custom_key(self):
        self._do_key_detect(lambda k: (
            self.custom_key_var.set(k)
        ))

    def start_listening_talisman_key(self):
        self._do_key_detect(lambda k: (
            self.talisman_key_var.set(k)
        ))

    def _browse_client(self, var):
        from tkinter import filedialog
        path = filedialog.askopenfilename(
            title="Select game executable",
            filetypes=[("Executable", "*.exe"), ("All files", "*.*")]
        )
        if path:
            var.set(path)
            self._save_all()

    def _launch_client1(self):
        steam = self.client1_steam_var.get()
        game  = self.client1_path_var.get()

        if not steam and not game:
            messagebox.showwarning("Warning", "No paths set for Client 1!")
            return

        def launch_sequence():
            import subprocess, time
            try:
                if steam and os.path.exists(steam):
                    subprocess.Popen([steam, "-silent", "-nochatui", "-nofriendsui"], cwd=os.path.dirname(steam))
                    # Minimize Steam window when it appears
                    minimize_window_by_title("Steam", timeout=20)
                    time.sleep(30)
                if game and os.path.exists(game):
                    # Launch game via Steam protocol
                    subprocess.Popen(
                        [steam, "-applaunch", "236110", "-silent"],
                        cwd=os.path.dirname(steam)
                    )
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Error", f"Failed: {e}"))

        import threading
        threading.Thread(target=launch_sequence, daemon=True).start()
        messagebox.showinfo("Launching", "Starting Steam...\nGame will launch automatically after 15 seconds.")

    def _launch_sandboxie_full(self):
        """Launch Steam in sandbox, wait, then launch game."""
        sbx  = self.sandboxie_path_var.get()
        box  = self.sandboxie_box_var.get()
        steam = self.sandboxie_steam_var.get()
        game  = self.client2_path_var.get()

        if not os.path.exists(sbx):
            messagebox.showerror("Error", f"Sandboxie Start.exe not found:\n{sbx}")
            return
        if not os.path.exists(steam):
            messagebox.showerror("Error", f"Steam not found:\n{steam}")
            return
        if not game or not os.path.exists(game):
            messagebox.showerror("Error", "Game exe not found for Client 2!")
            return

        def launch_sequence():
            import subprocess, time
            try:
                sandman = self.sandman_path_var.get()
                # 1. Start Sandboxie driver service first, then UI
                if sandman and os.path.exists(sandman):
                    # Start SbieDrv service
                    subprocess.run(["sc", "start", "SbieDrv"],
                                   capture_output=True, creationflags=0x08000000)
                    time.sleep(3)
                    # Start SbieSvc service
                    subprocess.run(["sc", "start", "SbieSvc"],
                                   capture_output=True, creationflags=0x08000000)
                    time.sleep(3)
                    # Start SandMan UI minimized
                    info = subprocess.STARTUPINFO()
                    info.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                    info.wShowWindow = 2  # SW_SHOWMINIMIZED
                    subprocess.Popen([sandman], cwd=os.path.dirname(sandman),
                                     startupinfo=info)
                    time.sleep(5)
                # 2. Launch Steam minimized in sandbox
                subprocess.Popen([sbx, f"/box:{box}", steam, "-silent", "-nochatui", "-nofriendsui"],
                                 cwd=os.path.dirname(sbx))
                # 3. Wait for Steam to load (15 seconds)
                time.sleep(30)
                # 4. Launch game in sandbox
                subprocess.Popen([sbx, f"/box:{box}", game],
                                 cwd=os.path.dirname(sbx))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Error", f"Failed: {e}"))

        import threading
        t = threading.Thread(target=launch_sequence, daemon=True)
        t.start()
        messagebox.showinfo("Launching", 
            "Starting Steam in Sandboxie...\nGame will launch automatically after 15 seconds.")

    def _launch_client2(self):
        path = self.client2_path_var.get()
        if not path:
            messagebox.showwarning("Warning", "No path set for Client 2!")
            return
        if self.client2_sandboxie_var.get():
            # Launch via Sandboxie
            sbx = self.sandboxie_path_var.get()
            box = self.sandboxie_box_var.get()
            if not os.path.exists(sbx):
                messagebox.showerror("Error", f"Sandboxie Start.exe not found:\n{sbx}")
                return
            try:
                import subprocess
                subprocess.Popen(
                    [sbx, f"/box:{box}", path],
                    cwd=os.path.dirname(sbx)
                )
                messagebox.showinfo("Launched", "Client 2 launched via Sandboxie!")
            except Exception as e:
                messagebox.showerror("Error", f"Failed: {e}")
        else:
            self._launch(path, "Client 2")

    def _launch(self, path, name):
        if not path:
            messagebox.showwarning("Warning", f"No path set for {name}!")
            return
        import subprocess
        try:
            subprocess.Popen([path], cwd=os.path.dirname(path))
            messagebox.showinfo("Launched", f"{name} launched!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed: {e}")

    def kill_all_games(self):
        import subprocess
        result = subprocess.run(
            ["taskkill", "/F", "/IM", "DunDefGame.exe"],
            capture_output=True, text=True
        )
        if result.returncode == 0:
            messagebox.showinfo("Done", "All game processes terminated.")
        else:
            messagebox.showwarning("Warning", "No game processes found or could not terminate.")

    def _build_custom_tab(self):
        """Build the Custom tab with combo configurations."""
        tab = self.custom_tab
        self.combos = self.settings.get("combos", [])
        self.combo_frames = []

        tk.Label(tab, text="Custom Combos", font=("Segoe UI", 11, "bold"),
                 bg=BG, fg="white").pack(pady=(10,4))
        tk.Label(tab, text="Each combo triggers multiple macros with one hotkey",
                 font=("Segoe UI", 8), bg=BG, fg="#aaaaaa").pack()

        # Scrollable area for combos
        self.combos_container = tk.Frame(tab, bg=BG)
        self.combos_container.pack(fill="both", expand=True, padx=8, pady=4)

        # Render existing combos
        for combo in self.combos:
            self._render_combo(combo)

        # Buttons row
        btn_row = tk.Frame(tab, bg=BG)
        btn_row.pack(fill="x", padx=8, pady=(4,8))
        tk.Button(btn_row, text="+ Add New Combo",
                  font=("Segoe UI", 10), bg="#1a3a1a", fg="#44cc44",
                  relief="flat", cursor="hand2", pady=5,
                  command=self._add_combo).pack(side="left", fill="x", expand=True, padx=(0,4))
        tk.Button(btn_row, text="💾 Save",
                  font=("Segoe UI", 10), bg="#1a2a3a", fg="#44aaff",
                  relief="flat", cursor="hand2", pady=5,
                  command=lambda: [self._save_all(),
                      messagebox.showinfo("Saved", "Custom combos saved!")
                  ]).pack(side="left", fill="x", expand=True)

    def _add_combo(self):
        """Add a new empty combo."""
        combo = {
            "name": f"Combo {len(self.combos)+1}",
            "hotkey": "f10",
            "functions": {
                "g": False, "custom": False, "attack": False,
                "attack_r": False, "talisman": False
            }
        }
        self.combos.append(combo)
        self._render_combo(combo)
        self._save_all()

    def _render_combo(self, combo):
        """Render a single combo panel."""
        idx = len(self.combo_frames)

        outer = tk.Frame(self.combos_container, bg=ACCENT, padx=1, pady=1)
        outer.pack(fill="x", pady=3)
        inner = tk.Frame(outer, bg=BG2)
        inner.pack(fill="both", expand=True)

        # Header row - name + delete
        header = tk.Frame(inner, bg=BG2)
        header.pack(fill="x", padx=6, pady=(6,2))

        name_var = tk.StringVar(value=combo.get("name", f"Combo {idx+1}"))
        tk.Entry(header, textvariable=name_var, font=("Segoe UI", 10, "bold"),
                 bg=BG2, fg="white", relief="flat", width=16,
                 insertbackground="white").pack(side="left")
        name_var.trace_add("write", lambda *a: self._update_combo(idx, "name", name_var.get()))

        # Active indicator
        active_lbl = tk.Label(header, text="● INACTIVE",
                              font=("Segoe UI", 9, "bold"), bg=BG2, fg="#ff4444")
        active_lbl.pack(side="left", padx=8)

        tk.Button(header, text="✕", font=("Segoe UI", 9), bg="#440000", fg="white",
                  relief="flat", cursor="hand2", padx=6,
                  command=lambda i=idx: self._delete_combo(i)).pack(side="right")

        # Start/Stop button
        toggle_btn = tk.Button(inner, text="► Start Combo",
                               font=("Segoe UI", 10), bg=ACCENT, fg="white",
                               relief="flat", cursor="hand2", pady=4)
        toggle_btn.pack(fill="x", padx=6, pady=2)

        # Function checkboxes
        check_frame = tk.Frame(inner, bg=BG2)
        check_frame.pack(fill="x", padx=6, pady=2)
        funcs = combo.get("functions", {})
        func_labels = [("g","G Key"), ("custom","Custom Key"),
                       ("attack","Left Click"), ("attack_r","Right Click"),
                       ("talisman","Talisman")]
        check_vars = {}
        for i, (key, label) in enumerate(func_labels):
            var = tk.BooleanVar(value=funcs.get(key, False))
            check_vars[key] = var
            cb = tk.Checkbutton(check_frame, text=label, variable=var,
                                font=("Segoe UI", 9), bg=BG2, fg="white",
                                selectcolor=ACCENT, activebackground=BG2,
                                activeforeground="white", cursor="hand2",
                                command=lambda k=key, v=var, i=idx: self._update_combo_func(i, k, v.get()))
            cb.grid(row=i//3, column=i%3, sticky="w", padx=4, pady=1)

        # Client selector
        client_row = tk.Frame(inner, bg=BG2)
        client_row.pack(fill="x", padx=6, pady=(2,0))
        tk.Label(client_row, text="Client:", font=("Segoe UI", 9),
                 bg=BG2, fg="#aaaaaa").pack(side="left", padx=(0,4))
        client_var = tk.StringVar(value=combo.get("target", "both"))
        tk.OptionMenu(client_row, client_var, "both", "client1", "client2",
                      command=lambda v, i=idx: self._update_combo(i, "target", v)
                      ).pack(side="left")

        # Hotkey bind button
        hk_var = [combo.get("hotkey", "f10")]
        hk_btn = tk.Button(inner,
                           text=f"Hotkey: {hk_var[0]}",
                           font=("Segoe UI", 7), bg="#222244", fg="#aaaacc",
                           relief="flat", cursor="hand2", pady=3)
        hk_btn.pack(fill="x", padx=6, pady=(2,6))

        # Combo running state
        running_state = [False]
        combo_hotkey_handle = [None]

        def toggle_combo():
            running_state[0] = not running_state[0]
            selected = [k for k, v in check_vars.items() if v.get()]
            if running_state[0]:
                toggle_btn.config(text="■ Stop Combo", bg="#cc0000")
                active_lbl.config(text="● ACTIVE", fg="#00cc66")
                for fn in selected:
                    toggle_map = {
                        "g": self.toggle_g, "custom": self.toggle_custom,
                        "attack": self.toggle_attack, "attack_r": self.toggle_attack_r,
                        "talisman": self.toggle_talisman
                    }
                    if fn in toggle_map:
                        toggle_map[fn]()
            else:
                toggle_btn.config(text="► Start Combo", bg=ACCENT)
                active_lbl.config(text="● INACTIVE", fg="#ff4444")
                for fn in selected:
                    toggle_map = {
                        "g": self.toggle_g, "custom": self.toggle_custom,
                        "attack": self.toggle_attack, "attack_r": self.toggle_attack_r,
                        "talisman": self.toggle_talisman
                    }
                    if fn in toggle_map:
                        toggle_map[fn]()

        toggle_btn.config(command=toggle_combo)

        def start_hk_listen():
            hk_btn.config(text=">> Press any key <<", bg="#555577")
            self.start_listening(f"combo_{idx}")

        hk_btn.config(command=start_hk_listen)

        # Register hotkey
        def apply_combo_hk(key):
            if combo_hotkey_handle[0]:
                try: keyboard.remove_hotkey(combo_hotkey_handle[0])
                except: pass
            try:
                combo_hotkey_handle[0] = keyboard.add_hotkey(key, toggle_combo, suppress=False)
                hk_var[0] = key
                hk_btn.config(text=f"Hotkey: {key}", bg="#222244")
                self._update_combo(idx, "hotkey", key)
            except: pass

        apply_combo_hk(hk_var[0])

        self.combo_frames.append({
            "outer": outer, "toggle_btn": toggle_btn,
            "active_lbl": active_lbl, "hk_btn": hk_btn,
            "hk_apply": apply_combo_hk, "handle": combo_hotkey_handle
        })

    def _update_combo(self, idx, key, value):
        if idx < len(self.combos):
            self.combos[idx][key] = value
            self._save_all()

    def _update_combo_func(self, idx, func_key, value):
        if idx < len(self.combos):
            self.combos[idx].setdefault("functions", {})[func_key] = value
            self._save_all()

    def _delete_combo(self, idx):
        if idx < len(self.combos):
            # Remove hotkey
            if idx < len(self.combo_frames):
                h = self.combo_frames[idx]["handle"][0]
                if h:
                    try: keyboard.remove_hotkey(h)
                    except: pass
                self.combo_frames[idx]["outer"].destroy()
            self.combos.pop(idx)
            self.combo_frames.pop(idx)
            self._save_all()

    def on_close(self):
        global g_running, custom_running, attack_running, attack_r_running, talisman_running
        g_running = custom_running = attack_running = attack_r_running = talisman_running = False
        self._save_all()
        for h in self.hotkey_handles.values():
            if h is not None:
                try: keyboard.remove_hotkey(h)
                except: pass
        self.root.destroy()

root = tk.Tk()
app = App(root)
root.mainloop()
