# DD2 Macro<img width="625" height="1361" alt="obrázek_2026-05-18_153855251" src="https://github.com/user-attachments/assets/3b2ba6ff-c5a1-4420-865c-e6fd0ecd346d" />


A feature-rich macro tool for **Dungeon Defenders 2** supporting dual-client setups (Steam + Sandboxie).

![DD2 Macro](https://img.shields.io/badge/game-Dungeon%20Defenders%202-purple)
![Python](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-MIT-green)

---

## Features

- **G Key Macro** — Automatically presses G at a set interval (social interaction)
- **Custom Key Macro** — Press any key at a set interval with key detection
- **Left Click** — Hold or click at interval (auto-attack)
- **Right Click** — Hold or BPM rapid click (Mystic class rapid fire)
- **Talisman Buff** — Presses skill key + mouse movement + left click for talisman placement
- **Custom Combos** — Trigger multiple macros at once with a single hotkey
- **Dual Client Support** — Each macro can target Client 1, Client 2 (Sandboxie), or both
- **Launch Clients** — Launch Steam and game clients directly from the macro
- **Sandboxie Integration** — Full support for launching Client 2 via Sandboxie Plus
- **Kill All** — Instantly terminate all game processes
- **Overlay** — Always-on-top status indicator showing active macros
- **Persistent Settings** — All settings saved to JSON automatically

---

## Requirements

- Windows 10/11
- Python 3.10+ (only if running from source)
- [keyboard](https://pypi.org/project/keyboard/) library (auto-installed)
- [Sandboxie Plus](https://github.com/sandboxie-plus/Sandboxie/releases) (optional, for dual client)

---

## Installation

### Option A — Run the .exe (recommended)
1. Download `DD2_macro.exe` from [Releases](../../releases)
2. Right-click → **Run as administrator**
3. Configure your hotkeys and settings

### Option B — Run from source
```bash
pip install keyboard
python DD2_macro.py
```
> Must be run as **administrator** for global hotkeys to work.

---

## Usage

### Main Tab
| Section | Description | Default Hotkey |
|---|---|---|
| G Key Macro | Presses G repeatedly | F5 |
| Custom Key | Presses any key repeatedly | F8 |
| Left Click | Auto-attack (hold or interval) | F6 |
| Right Click | Rapid fire for Mystic (BPM mode) | F7 |
| Talisman Buff | Places talisman automatically | F9 |

### Custom Tab
Create combos that trigger multiple macros with one hotkey.

### Launch Clients
Configure paths to automatically launch:
- **Client 1** — Steam + Game
- **Client 2** — Sandboxie + Steam + Game (full automated sequence)

---

## Dual Client Setup

This macro was built with dual-client DD2 in mind:
- **Client 1** — Normal Steam client
- **Client 2** — Second Steam account via [Sandboxie Plus](https://github.com/sandboxie-plus/Sandboxie/releases)

Each macro function has a **Client** dropdown to target:
- `both` — sends to both clients
- `client1` — Steam client only
- `client2` — Sandboxie client only

---

## VK Codes (for Custom Key & Talisman)

| Key | VK Code |
|---|---|
| 1 | 0x31 |
| 2 | 0x32 |
| 3 | 0x33 |
| 4 | 0x34 |
| G | 0x47 |
| F1-F12 | 0x70-0x7B |

---

## Important Notes

- This tool sends inputs to the **game window directly** (own-sided, not game-sided)
- Macro usage with auto-G in DD2 is **allowed** All another functions you can use at your own risk 
- Run as **administrator** for hotkeys to work globally
- Antivirus may flag the `.exe` as suspicious — this is a **false positive** (PyInstaller behavior)

---

## Building from Source

```bash
pip install keyboard pyinstaller
pyinstaller --onefile --noconsole DD2_macro.py
```

---

## License

MIT License — free to use, modify and distribute.
