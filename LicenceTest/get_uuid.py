import sys, os, uuid, tkinter as tk
from tkinter import ttk

def get_system_uuid():
    try:
        if sys.platform.startswith("win"):
            import winreg
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                                 r"SOFTWARE\Microsoft\Cryptography")
            val, _ = winreg.QueryValueEx(key, "MachineGuid")
            return val.strip()
    except Exception:
        pass
    try:
        for path in ("/etc/machine-id", "/var/lib/dbus/machine-id"):
            if os.path.exists(path):
                with open(path) as f:
                    return f.read().strip()
    except Exception:
        pass
    return f"{uuid.getnode():x}"

def copy_to_clipboard(uuid_value, status_label, copy_icon_btn):
    root.clipboard_clear()
    root.clipboard_append(uuid_value)
    root.update()
    status_label.config(text="✓ Copied to clipboard!")
    copy_icon_btn.config(text="✓", bg=SUCCESS_COLOR)
    root.after(2000, lambda: [status_label.config(text=""), copy_icon_btn.config(text="📋", bg=ACCENT_COLOR)])

uuid_value = get_system_uuid()
root = tk.Tk()
root.title("Key Generator")
root.geometry("520x280")
root.resizable(False, False)

# Modern color scheme
BG_COLOR = "#f5f7fa"
ACCENT_COLOR = "#4a90e2"
DARK_TEXT = "#2c3e50"
LIGHT_TEXT = "#7f8c8d"
SUCCESS_COLOR = "#27ae60"
ENTRY_BG = "#ffffff"

root.configure(bg=BG_COLOR)

# Center the window
root.update_idletasks()
width = root.winfo_width()
height = root.winfo_height()
x = (root.winfo_screenwidth() // 2) - (width // 2)
y = (root.winfo_screenheight() // 2) - (height // 2)
root.geometry(f'{width}x{height}+{x}+{y}')

# Configure styles
style = ttk.Style()
style.theme_use('clam')

# Configure custom styles
style.configure("Modern.TFrame", background=BG_COLOR)
style.configure("Title.TLabel",
                background=BG_COLOR,
                foreground=DARK_TEXT,
                font=("Segoe UI", 14, "bold"))
style.configure("Subtitle.TLabel",
                background=BG_COLOR,
                foreground=LIGHT_TEXT,
                font=("Segoe UI", 9))
style.configure("Status.TLabel",
                background=BG_COLOR,
                foreground=SUCCESS_COLOR,
                font=("Segoe UI", 10, "bold"))

# Main frame
main_frame = ttk.Frame(root, padding="30", style="Modern.TFrame")
main_frame.pack(fill=tk.BOTH, expand=True)

# Header icon/emoji
header_label = ttk.Label(main_frame, text="🔑",
                         font=("Segoe UI", 32),
                         background=BG_COLOR)
header_label.pack(pady=(0, 10))

# Title
title_label = ttk.Label(main_frame, text="System UUID",
                        style="Title.TLabel")
title_label.pack(pady=(0, 5))

# Subtitle
subtitle_label = ttk.Label(main_frame, text="Copy your generated key below",
                           style="Subtitle.TLabel")
subtitle_label.pack(pady=(0, 20))

# UUID Container Frame with copy button
uuid_row_frame = tk.Frame(main_frame, bg=BG_COLOR)
uuid_row_frame.pack(pady=(0, 20))

uuid_container = tk.Frame(uuid_row_frame, bg=ENTRY_BG,
                         highlightbackground=ACCENT_COLOR,
                         highlightthickness=2,
                         highlightcolor=ACCENT_COLOR)
uuid_container.pack(side=tk.LEFT, padx=(0, 10))

# UUID Entry (read-only but selectable)
uuid_entry = tk.Entry(uuid_container,
                      width=len(uuid_value),
                      font=("Consolas", 11, "bold"),
                      justify="center",
                      fg=DARK_TEXT,
                      bg=ENTRY_BG,
                      relief=tk.FLAT,
                      bd=0,
                      selectbackground=ACCENT_COLOR,
                      selectforeground="white")
uuid_entry.pack(pady=12, padx=15)
uuid_entry.insert(0, uuid_value)
uuid_entry.config(state="readonly")
# Select all text by default
uuid_entry.select_range(0, tk.END)
uuid_entry.focus()

# Status label (declare before button so it can be referenced)
status_label = ttk.Label(main_frame, text="", style="Status.TLabel")
status_label.pack()

# Copy icon button next to UUID
copy_icon_btn = tk.Button(uuid_row_frame,
                         text="📋",
                         font=("Segoe UI", 16),
                         bg=ACCENT_COLOR,
                         fg="white",
                         activebackground="#357abd",
                         activeforeground="white",
                         relief=tk.FLAT,
                         cursor="hand2",
                         width=3,
                         height=1,
                         command=lambda: copy_to_clipboard(uuid_value, status_label, copy_icon_btn))
copy_icon_btn.pack(side=tk.LEFT)

# Hover effect for copy button
def on_enter(e):
    if copy_icon_btn['text'] == "📋":
        copy_icon_btn['bg'] = '#357abd'

def on_leave(e):
    if copy_icon_btn['text'] == "📋":
        copy_icon_btn['bg'] = ACCENT_COLOR
    else:
        copy_icon_btn['bg'] = SUCCESS_COLOR

copy_icon_btn.bind("<Enter>", on_enter)
copy_icon_btn.bind("<Leave>", on_leave)

root.mainloop()
