import customtkinter as ctk
import threading
from queue import Queue
import time
from datetime import datetime
from main import (
    process_phone_numbers,
    check_expiration,
    ensure_directories,
    start_proxy_server,
    EXPIRATION_DATE
)

# Set appearance mode and color theme
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class ModernButton(ctk.CTkButton):
    """Custom modern button with hover effects"""
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.configure(
            corner_radius=8,
            font=ctk.CTkFont(size=13, weight="bold"),
            height=38,
            border_width=0
        )


class StatCard(ctk.CTkFrame):
    """Modern stat card component"""
    def __init__(self, master, title, value="0", color="#3b82f6"):
        super().__init__(master, corner_radius=12, fg_color=("#f8fafc", "#1e293b"))

        # Icon/Value
        self.value_label = ctk.CTkLabel(
            self,
            text=value,
            font=ctk.CTkFont(size=32, weight="bold"),
            text_color=color
        )
        self.value_label.pack(pady=(15, 5))

        # Title
        self.title_label = ctk.CTkLabel(
            self,
            text=title,
            font=ctk.CTkFont(size=12),
            text_color=("#64748b", "#94a3b8")
        )
        self.title_label.pack(pady=(0, 15))

    def update_value(self, value):
        self.value_label.configure(text=str(value))


class FacebookCheckerGUI:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("Facebook Account Checker Pro")
        self.root.geometry("1400x850")

        # Ensure directories exist
        ensure_directories()

        # Check expiration before starting GUI
        try:
            check_expiration()
            expired = False
            message = self.get_expiration_message()
        except Exception as e:
            expired = True
            message = str(e)

        if expired:
            self.show_expiration_error(message)
            return

        # State variables
        self.is_running = False
        self.results_queue = Queue()
        self.successful_numbers = []
        self.failed_numbers = []
        self.total_numbers = 0
        self.processed_count = 0
        self.expiration_message = message

        # Color scheme
        self.colors = {
            'primary': '#3b82f6',
            'success': '#10b981',
            'danger': '#ef4444',
            'warning': '#f59e0b',
            'background': '#0f172a',
            'surface': '#1e293b',
            'surface_light': '#334155',
            'text_primary': '#f1f5f9',
            'text_secondary': '#94a3b8',
            'border': '#334155'
        }

        # Start the proxy server
        start_proxy_server()

        self.setup_ui()

    def get_expiration_message(self):
        """Get expiration message"""
        if EXPIRATION_DATE is None:
            return "No expiration"

        now = datetime.now()
        days_remaining = (EXPIRATION_DATE - now).days

        if days_remaining <= 3:
            return f"Expires in {days_remaining} days"
        else:
            return f"Valid until {EXPIRATION_DATE.strftime('%B %d, %Y')}"

    def show_expiration_error(self, message):
        """Show expiration error with modern design"""
        self.root.title("Software Expired")

        # Background
        bg = ctk.CTkFrame(self.root, fg_color=("#ffffff", "#0f172a"))
        bg.pack(fill="both", expand=True)

        error_frame = ctk.CTkFrame(
            bg,
            corner_radius=20,
            fg_color=("#ffffff", "#1e293b"),
            border_width=2,
            border_color=("#e2e8f0", "#334155")
        )
        error_frame.place(relx=0.5, rely=0.5, anchor="center")

        # Icon
        icon_label = ctk.CTkLabel(
            error_frame,
            text="⚠️",
            font=ctk.CTkFont(size=80)
        )
        icon_label.pack(pady=(40, 20))

        # Title
        title_label = ctk.CTkLabel(
            error_frame,
            text="Software Expired",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color="#ef4444"
        )
        title_label.pack(pady=(0, 15))

        # Message
        message_label = ctk.CTkLabel(
            error_frame,
            text=message,
            font=ctk.CTkFont(size=14),
            wraplength=500,
            text_color=("#475569", "#cbd5e1")
        )
        message_label.pack(pady=(0, 20), padx=40)

        # Contact
        contact_label = ctk.CTkLabel(
            error_frame,
            text="Please contact the software provider to renew your license.",
            font=ctk.CTkFont(size=12),
            text_color=("#64748b", "#94a3b8")
        )
        contact_label.pack(pady=(0, 30), padx=40)

        # Close button
        close_button = ModernButton(
            error_frame,
            text="Close Application",
            command=self.root.quit,
            fg_color="#ef4444",
            hover_color="#dc2626",
            width=250,
            height=45
        )
        close_button.pack(pady=(0, 40))

    def setup_ui(self):
        # Main container
        main_container = ctk.CTkFrame(self.root, fg_color="transparent")
        main_container.pack(fill="both", expand=True, padx=25, pady=25)

        # ============ HEADER SECTION ============
        header_frame = ctk.CTkFrame(
            main_container,
            height=100,
            corner_radius=15,
            fg_color=("#f8fafc", "#1e293b"),
            border_width=1,
            border_color=("#e2e8f0", "#334155")
        )
        header_frame.pack(fill="x", pady=(0, 20))
        header_frame.pack_propagate(False)

        # Header content
        header_content = ctk.CTkFrame(header_frame, fg_color="transparent")
        header_content.pack(fill="both", expand=True, padx=30, pady=20)

        # Left side - Title and subtitle
        title_section = ctk.CTkFrame(header_content, fg_color="transparent")
        title_section.pack(side="left", fill="y")

        app_title = ctk.CTkLabel(
            title_section,
            text="Facebook Account Checker Pro",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color=self.colors['primary']
        )
        app_title.pack(anchor="w")

        subtitle = ctk.CTkLabel(
            title_section,
            text="Automated phone number verification system",
            font=ctk.CTkFont(size=13),
            text_color=self.colors['text_secondary']
        )
        subtitle.pack(anchor="w", pady=(2, 0))

        # Right side - Expiration info
        info_section = ctk.CTkFrame(header_content, fg_color="transparent")
        info_section.pack(side="right", fill="y")

        expiration_badge = ctk.CTkFrame(
            info_section,
            corner_radius=8,
            fg_color=("#e0f2fe", "#0c4a6e")
        )
        expiration_badge.pack(anchor="e")

        ctk.CTkLabel(
            expiration_badge,
            text=f"📅 {self.expiration_message}",
            font=ctk.CTkFont(size=11),
            text_color=("#0369a1", "#7dd3fc")
        ).pack(padx=15, pady=8)

        # ============ MAIN CONTENT AREA ============
        content_container = ctk.CTkFrame(main_container, fg_color="transparent")
        content_container.pack(fill="both", expand=True)

        # ============ LEFT PANEL - INPUT ============
        left_panel = ctk.CTkFrame(
            content_container,
            corner_radius=15,
            fg_color=("#f8fafc", "#1e293b"),
            border_width=1,
            border_color=("#e2e8f0", "#334155")
        )
        left_panel.pack(side="left", fill="both", expand=True, padx=(0, 15))

        # Left panel header
        left_header = ctk.CTkFrame(left_panel, fg_color="transparent", height=60)
        left_header.pack(fill="x", padx=25, pady=(20, 10))
        left_header.pack_propagate(False)

        ctk.CTkLabel(
            left_header,
            text="📱 Phone Numbers",
            font=ctk.CTkFont(size=20, weight="bold"),
            anchor="w"
        ).pack(side="left", fill="y")

        # Input info badge
        info_badge = ctk.CTkFrame(left_header, corner_radius=6, fg_color=("#dbeafe", "#1e3a8a"))
        info_badge.pack(side="right")
        ctk.CTkLabel(
            info_badge,
            text="One per line",
            font=ctk.CTkFont(size=10),
            text_color=("#1e40af", "#93c5fd")
        ).pack(padx=10, pady=4)

        # Text input area with line numbers
        text_container = ctk.CTkFrame(left_panel, fg_color="transparent")
        text_container.pack(fill="both", expand=True, padx=25, pady=(10, 20))

        # Line numbers
        self.line_numbers = ctk.CTkTextbox(
            text_container,
            width=45,
            font=ctk.CTkFont(size=12, family="Consolas"),
            fg_color=("#e2e8f0", "#0f172a"),
            text_color=("#64748b", "#475569"),
            border_width=0,
            corner_radius=8,
            activate_scrollbars=False
        )
        self.line_numbers.pack(side="left", fill="y", padx=(0, 2))
        self.line_numbers.configure(state="disabled")

        # Phone numbers input
        self.numbers_text = ctk.CTkTextbox(
            text_container,
            font=ctk.CTkFont(size=13, family="Consolas"),
            fg_color=("#ffffff", "#0f172a"),
            border_width=1,
            border_color=("#cbd5e1", "#334155"),
            corner_radius=8
        )
        self.numbers_text.pack(side="left", fill="both", expand=True)

        # Bind events
        self.numbers_text.bind("<KeyRelease>", self.on_text_change)
        self.numbers_text.bind("<Button-1>", self.on_text_change)
        self.numbers_text.bind("<Control-v>", self.on_paste_event)
        self.numbers_text.bind("<MouseWheel>", self.sync_scroll)

        # Bind scrollbar movement to sync line numbers
        # This ensures line numbers scroll when using the scrollbar
        self.numbers_text._textbox.bind("<Configure>", lambda e: self.sync_line_numbers_scroll())
        self.numbers_text._textbox.bind("<<Modified>>", lambda e: self.sync_line_numbers_scroll())

        self.update_line_numbers()

        # ============ CONTROL PANEL ============
        control_panel = ctk.CTkFrame(
            left_panel,
            corner_radius=12,
            fg_color=("#f1f5f9", "#0f172a"),
            border_width=1,
            border_color=("#e2e8f0", "#334155")
        )
        control_panel.pack(fill="x", padx=25, pady=(0, 25))

        control_inner = ctk.CTkFrame(control_panel, fg_color="transparent")
        control_inner.pack(fill="x", padx=20, pady=18)

        # Workers control
        workers_frame = ctk.CTkFrame(control_inner, fg_color="transparent")
        workers_frame.pack(side="left", padx=(0, 20))

        ctk.CTkLabel(
            workers_frame,
            text="⚙️ Workers",
            font=ctk.CTkFont(size=12, weight="bold")
        ).pack(side="left", padx=(0, 10))

        self.workers_var = ctk.StringVar(value="5")
        self.workers_spinbox = ctk.CTkEntry(
            workers_frame,
            width=70,
            height=35,
            textvariable=self.workers_var,
            font=ctk.CTkFont(size=13, weight="bold"),
            justify="center",
            corner_radius=8,
            border_width=1,
            border_color=("#cbd5e1", "#334155")
        )
        self.workers_spinbox.pack(side="left")

        # Headless toggle
        self.headless_var = ctk.BooleanVar(value=True)
        self.headless_switch = ctk.CTkSwitch(
            control_inner,
            text="🎭 Headless Mode",
            variable=self.headless_var,
            command=self.on_headless_toggle,
            font=ctk.CTkFont(size=12, weight="bold"),
            progress_color=self.colors['primary']
        )
        self.headless_switch.pack(side="left", padx=(0, 20))

        # Start button
        self.start_button = ModernButton(
            control_inner,
            text="🚀 Start Verification",
            command=self.toggle_checking,
            fg_color=self.colors['success'],
            hover_color="#059669",
            font=ctk.CTkFont(size=14, weight="bold"),
            height=42
        )
        self.start_button.pack(side="right", fill="x", expand=True)

        # ============ RIGHT PANEL - RESULTS ============
        right_panel = ctk.CTkFrame(
            content_container,
            corner_radius=15,
            fg_color=("#f8fafc", "#1e293b"),
            border_width=1,
            border_color=("#e2e8f0", "#334155")
        )
        right_panel.pack(side="right", fill="both", expand=True)

        # Right panel header
        right_header = ctk.CTkFrame(right_panel, fg_color="transparent", height=60)
        right_header.pack(fill="x", padx=25, pady=(20, 15))
        right_header.pack_propagate(False)

        ctk.CTkLabel(
            right_header,
            text="📊 Results Dashboard",
            font=ctk.CTkFont(size=20, weight="bold"),
            anchor="w"
        ).pack(side="left", fill="y")

        # Progress indicator
        self.progress_label = ctk.CTkLabel(
            right_header,
            text="Ready to start",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=self.colors['text_secondary']
        )
        self.progress_label.pack(side="right")

        # ============ STATISTICS CARDS ============
        stats_container = ctk.CTkFrame(right_panel, fg_color="transparent")
        stats_container.pack(fill="x", padx=25, pady=(0, 20))

        # Create stat cards
        stats_grid = ctk.CTkFrame(stats_container, fg_color="transparent")
        stats_grid.pack(fill="x")

        self.total_card = StatCard(stats_grid, "Total Numbers", "0", self.colors['primary'])
        self.total_card.pack(side="left", fill="x", expand=True, padx=(0, 10))

        self.success_card = StatCard(stats_grid, "Successful", "0", self.colors['success'])
        self.success_card.pack(side="left", fill="x", expand=True, padx=(5, 10))

        self.failed_card = StatCard(stats_grid, "Failed", "0", self.colors['danger'])
        self.failed_card.pack(side="left", fill="x", expand=True, padx=(5, 0))

        # ============ RESULTS TABS ============
        self.tabview = ctk.CTkTabview(
            right_panel,
            corner_radius=12,
            border_width=1,
            border_color=("#e2e8f0", "#334155"),
            segmented_button_fg_color=("#e2e8f0", "#0f172a"),
            segmented_button_selected_color=self.colors['primary'],
            segmented_button_selected_hover_color="#2563eb"
        )
        self.tabview.pack(fill="both", expand=True, padx=25, pady=(0, 25))

        # Add tabs with icons
        self.tabview.add("✅ Successful")
        self.tabview.add("❌ Failed")
        self.tabview.add("📝 Activity Log")

        # Successful numbers tab
        self.success_text = ctk.CTkTextbox(
            self.tabview.tab("✅ Successful"),
            font=ctk.CTkFont(size=12, family="Consolas"),
            fg_color=("#f0fdf4", "#064e3b"),
            text_color=("#166534", "#86efac"),
            border_width=0,
            corner_radius=8
        )
        self.success_text.pack(fill="both", expand=True, padx=10, pady=10)

        # Failed numbers tab
        self.failed_text = ctk.CTkTextbox(
            self.tabview.tab("❌ Failed"),
            font=ctk.CTkFont(size=12, family="Consolas"),
            fg_color=("#fef2f2", "#7f1d1d"),
            text_color=("#991b1b", "#fca5a5"),
            border_width=0,
            corner_radius=8
        )
        self.failed_text.pack(fill="both", expand=True, padx=10, pady=10)

        # Activity log tab
        self.log_text = ctk.CTkTextbox(
            self.tabview.tab("📝 Activity Log"),
            font=ctk.CTkFont(size=11, family="Consolas"),
            fg_color=("#fafaf9", "#0c0a09"),
            border_width=0,
            corner_radius=8
        )
        self.log_text.pack(fill="both", expand=True, padx=10, pady=10)

    def log_message(self, message):
        """Add a message to the log with timestamp"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        log_entry = f"[{timestamp}] {message}\n"
        self.log_text.insert("end", log_entry)
        self.log_text.see("end")

    def toggle_checking(self):
        """Start or stop the checking process"""
        if not self.is_running:
            self.start_checking()
        else:
            self.stop_checking()

    def start_checking(self):
        """Start the phone number checking process"""
        # Get phone numbers from input
        numbers_input = self.numbers_text.get("1.0", "end-1c").strip()
        if not numbers_input:
            self.log_message("❌ ERROR: No phone numbers entered!")
            return

        # Parse numbers (one per line)
        numbers = [line.strip() for line in numbers_input.split("\n") if line.strip()]

        if not numbers:
            self.log_message("❌ ERROR: No valid phone numbers found!")
            return

        # Get workers count
        try:
            workers = int(self.workers_var.get())
            if workers < 1 or workers > 100:
                self.log_message("❌ ERROR: Workers must be between 1 and 100!")
                return
        except ValueError:
            self.log_message("❌ ERROR: Invalid workers value!")
            return

        # Reset state
        self.successful_numbers = []
        self.failed_numbers = []
        self.total_numbers = len(numbers)
        self.processed_count = 0
        self.is_running = True

        # Update UI
        self.start_button.configure(
            text="⏸️ Stop Verification",
            fg_color=self.colors['danger'],
            hover_color="#dc2626"
        )
        self.numbers_text.configure(state="disabled")
        self.workers_spinbox.configure(state="disabled")
        self.headless_switch.configure(state="disabled")

        # Clear results
        self.success_text.delete("1.0", "end")
        self.failed_text.delete("1.0", "end")
        self.log_text.delete("1.0", "end")

        # Update stats
        self.total_card.update_value(self.total_numbers)
        self.success_card.update_value(0)
        self.failed_card.update_value(0)
        self.progress_label.configure(text="⏳ Processing: 0/" + str(self.total_numbers))

        self.log_message(f"🚀 Starting verification for {self.total_numbers} numbers with {workers} workers")

        # Start checking in a separate thread
        thread = threading.Thread(
            target=self.check_numbers_thread,
            args=(numbers, workers),
            daemon=True
        )
        thread.start()

        # Start UI update loop
        self.root.after(100, self.update_ui)

    def stop_checking(self):
        """Stop the checking process"""
        self.is_running = False
        self.log_message("⏸️ Stopping... (current tasks will finish)")
        self.start_button.configure(
            text="🚀 Start Verification",
            fg_color=self.colors['success'],
            hover_color="#059669"
        )
        self.numbers_text.configure(state="normal")
        self.workers_spinbox.configure(state="normal")
        self.headless_switch.configure(state="normal")

    def check_numbers_thread(self, numbers, workers):
        """Thread function to check phone numbers using functional API with real-time callback"""
        # Get headless mode setting
        headless_mode = self.headless_var.get()

        # Define callback function that will be called for each result
        def result_callback(result):
            """Called by main.py worker threads when each result is ready"""
            if self.is_running:  # Only add if still running
                self.results_queue.put(result)

        try:
            # Use the functional API from main.py with callback
            results = process_phone_numbers(
                numbers,
                num_workers=workers,
                headless=headless_mode,
                callback=result_callback  # This enables real-time updates
            )

            # Signal completion
            self.results_queue.put(None)

        except Exception as e:
            self.log_message(f"❌ Error during checking: {e}")
            self.results_queue.put(None)

    def update_ui(self):
        """Update UI with results from the queue"""
        try:
            # Process all available results
            while not self.results_queue.empty():
                result = self.results_queue.get_nowait()

                if result is None:
                    # Checking complete
                    self.is_running = False
                    self.start_button.configure(
                        text="🚀 Start Verification",
                        fg_color=self.colors['success'],
                        hover_color="#059669"
                    )
                    self.numbers_text.configure(state="normal")
                    self.workers_spinbox.configure(state="normal")
                    self.headless_switch.configure(state="normal")
                    self.progress_label.configure(text="✅ Completed!")
                    self.log_message(f"✅ All checks completed! Success: {len(self.successful_numbers)}, Failed: {len(self.failed_numbers)}")
                    continue

                # Process result
                self.processed_count += 1
                phone = result['phone']
                status = result['status']
                message = result['message']

                if status == 'success':
                    self.successful_numbers.append(phone)
                    self.success_text.insert("end", f"{phone}\n")
                    self.log_message(f"✅ SUCCESS: {phone} - {message}")
                else:
                    self.failed_numbers.append(phone)
                    self.failed_text.insert("end", f"{phone} - {message}\n")
                    self.log_message(f"❌ FAILED: {phone} - {message}")

                # Update stats
                self.success_card.update_value(len(self.successful_numbers))
                self.failed_card.update_value(len(self.failed_numbers))
                self.progress_label.configure(
                    text=f"⏳ Processing: {self.processed_count}/{self.total_numbers}"
                )

        except Exception as e:
            self.log_message(f"⚠️ UI Update Error: {e}")

        # Continue updating if still running
        if self.is_running or not self.results_queue.empty():
            self.root.after(100, self.update_ui)

    def on_text_change(self, event=None):
        """Handle text change event to update line numbers"""
        self.update_line_numbers()

    def on_paste_event(self, event=None):
        """Handle paste event to update line numbers after a short delay"""
        self.root.after(10, self.update_line_numbers)

    def on_headless_toggle(self):
        """Handle headless mode toggle"""
        if not self.headless_var.get():
            # Headless is OFF (visible browser mode)
            self.log_message("🎭 Headless mode disabled - Browsers will be visible")
        else:
            # Headless is ON
            self.log_message("🎭 Headless mode enabled - Browsers will run in background")

    def update_line_numbers(self, event=None):
        """Update the line numbers display"""
        try:
            # Get the number of lines in the text area
            content = self.numbers_text.get("1.0", "end-1c")
            lines = content.split("\n")
            num_lines = len(lines)

            # Generate line numbers
            line_numbers_text = "\n".join(str(i) for i in range(1, num_lines + 1))

            # Update the line numbers display
            self.line_numbers.configure(state="normal")
            self.line_numbers.delete("1.0", "end")
            self.line_numbers.insert("1.0", line_numbers_text)
            self.line_numbers.configure(state="disabled")

            # Sync scroll position
            self.line_numbers.yview_moveto(self.numbers_text.yview()[0])
        except Exception as e:
            pass  # Avoid logging during initialization

    def sync_scroll(self, event):
        """Sync scrolling between line numbers and text area"""
        try:
            if event.delta > 0:  # Scroll up
                self.numbers_text.yview_scroll(-1, "units")
                self.line_numbers.yview_scroll(-1, "units")
            elif event.delta < 0:  # Scroll down
                self.numbers_text.yview_scroll(1, "units")
                self.line_numbers.yview_scroll(1, "units")
        except Exception as e:
            self.log_message(f"⚠️ Scroll sync error: {e}")

    def sync_line_numbers_scroll(self):
        """Sync line numbers scroll position with main text (for scrollbar usage)"""
        try:
            # Get the current scroll position of the main text area
            yview = self.numbers_text.yview()
            # Apply the same scroll position to line numbers
            self.line_numbers.yview_moveto(yview[0])
        except Exception:
            pass  # Ignore errors during initialization

    def run(self):
        """Start the GUI application"""
        self.root.mainloop()


if __name__ == "__main__":
    app = FacebookCheckerGUI()
    app.run()
