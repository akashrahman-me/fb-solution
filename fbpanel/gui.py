import customtkinter as ctk
import threading
from queue import Queue
import time
from datetime import datetime
from main import FacebookNumberChecker, ExpirationChecker

# Set appearance mode and color theme
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")


class FacebookCheckerGUI:
    def __init__(self):
        self.root = ctk.CTk()
        self.root.title("Facebook Number Checker")
        self.root.geometry("1200x700")

        # Check expiration before starting GUI
        expired, message = ExpirationChecker.check_expiration()
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

        self.setup_ui()

    def show_expiration_error(self, message):
        """Show expiration error and close"""
        self.root.title("Software Expired")

        error_frame = ctk.CTkFrame(self.root)
        error_frame.pack(fill="both", expand=True, padx=50, pady=50)

        icon_label = ctk.CTkLabel(
            error_frame,
            text="⚠️",
            font=ctk.CTkFont(size=72)
        )
        icon_label.pack(pady=(20, 10))

        title_label = ctk.CTkLabel(
            error_frame,
            text="Software Expired",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color="#dc3545"
        )
        title_label.pack(pady=10)

        message_label = ctk.CTkLabel(
            error_frame,
            text=message,
            font=ctk.CTkFont(size=14),
            wraplength=500
        )
        message_label.pack(pady=20)

        contact_label = ctk.CTkLabel(
            error_frame,
            text="Please contact the software provider to renew your license.",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        contact_label.pack(pady=10)

        close_button = ctk.CTkButton(
            error_frame,
            text="Close",
            command=self.root.quit,
            fg_color="#dc3545",
            hover_color="#c82333",
            width=200,
            height=40
        )
        close_button.pack(pady=20)

    def setup_ui(self):
        # Main container with padding
        main_frame = ctk.CTkFrame(self.root)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Title with expiration info
        title_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        title_frame.pack(pady=(0, 10))

        title_label = ctk.CTkLabel(
            title_frame,
            text="Facebook Number Checker",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        title_label.pack()

        # Show expiration status
        expiration_label = ctk.CTkLabel(
            title_frame,
            text=self.expiration_message,
            font=ctk.CTkFont(size=10),
            text_color="gray"
        )
        expiration_label.pack()

        # Content frame (left and right sections)
        content_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        content_frame.pack(fill="both", expand=True)

        # Left Section - Input
        left_frame = ctk.CTkFrame(content_frame)
        left_frame.pack(side="left", fill="both", expand=True, padx=(0, 10))

        # Left title
        left_title = ctk.CTkLabel(
            left_frame,
            text="Phone Numbers Input",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        left_title.pack(pady=(10, 10))

        # Input instructions
        instructions = ctk.CTkLabel(
            left_frame,
            text="Enter phone numbers (one per line)",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        instructions.pack(pady=(0, 10))

        # Create a frame for text area with line numbers
        text_frame = ctk.CTkFrame(left_frame, fg_color="transparent")
        text_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Line numbers text (read-only)
        self.line_numbers = ctk.CTkTextbox(
            text_frame,
            width=50,
            font=ctk.CTkFont(size=12, family="Courier"),
            fg_color="#1a1a1a",
            text_color="#666666"
        )
        self.line_numbers.pack(side="left", fill="y")
        self.line_numbers.configure(state="disabled")  # Make it read-only

        # Phone numbers text area
        self.numbers_text = ctk.CTkTextbox(
            text_frame,
            height=400,
            font=ctk.CTkFont(size=12, family="Courier")
        )
        self.numbers_text.pack(side="left", fill="both", expand=True)

        # Bind events to update line numbers
        self.numbers_text.bind("<KeyRelease>", self.on_text_change)
        self.numbers_text.bind("<Button-1>", self.on_text_change)
        # Bind for paste operations
        self.numbers_text.bind("<Control-v>", self.on_paste_event)
        self.numbers_text.bind("<Button-2>", self.on_paste_event)

        # Bind scrolling to sync line numbers with text
        self.numbers_text.bind("<MouseWheel>", self.sync_scroll)
        self.numbers_text.bind("<Button-4>", self.sync_scroll)  # Linux scroll up
        self.numbers_text.bind("<Button-5>", self.sync_scroll)  # Linux scroll down

        # Initialize line numbers
        self.update_line_numbers()

        # Control frame
        control_frame = ctk.CTkFrame(left_frame)
        control_frame.pack(fill="x", padx=10, pady=(0, 10))

        # Workers/Concurrency setting
        workers_label = ctk.CTkLabel(
            control_frame,
            text="Concurrent Workers:",
            font=ctk.CTkFont(size=12)
        )
        workers_label.pack(side="left", padx=(0, 10))

        self.workers_var = ctk.StringVar(value="5")
        self.workers_spinbox = ctk.CTkEntry(
            control_frame,
            width=60,
            textvariable=self.workers_var
        )
        self.workers_spinbox.pack(side="left", padx=(0, 20))

        # Headless mode switch
        self.headless_var = ctk.BooleanVar(value=True)
        self.headless_switch = ctk.CTkSwitch(
            control_frame,
            text="Headless Mode",
            variable=self.headless_var,
            command=self.on_headless_toggle,
            font=ctk.CTkFont(size=12)
        )
        self.headless_switch.pack(side="left", padx=(0, 20))

        # Start/Stop button
        self.start_button = ctk.CTkButton(
            control_frame,
            text="Send verification code",
            command=self.toggle_checking,
            font=ctk.CTkFont(size=14, weight="bold"),
            height=40,
            fg_color="#28a745",
            hover_color="#218838"
        )
        self.start_button.pack(side="left", fill="x", expand=True)

        # Right Section - Results
        right_frame = ctk.CTkFrame(content_frame)
        right_frame.pack(side="right", fill="both", expand=True, padx=(10, 0))

        # Right title
        right_title = ctk.CTkLabel(
            right_frame,
            text="Results",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        right_title.pack(pady=(10, 10))

        # Statistics frame
        stats_frame = ctk.CTkFrame(right_frame)
        stats_frame.pack(fill="x", padx=10, pady=(0, 10))

        # Progress label
        self.progress_label = ctk.CTkLabel(
            stats_frame,
            text="Ready to start",
            font=ctk.CTkFont(size=12)
        )
        self.progress_label.pack(pady=5)

        # Stats grid
        stats_grid = ctk.CTkFrame(stats_frame, fg_color="transparent")
        stats_grid.pack(fill="x", pady=5)

        # Total
        total_frame = ctk.CTkFrame(stats_grid)
        total_frame.pack(side="left", fill="x", expand=True, padx=2)
        ctk.CTkLabel(total_frame, text="Total", font=ctk.CTkFont(size=11)).pack()
        self.total_label = ctk.CTkLabel(
            total_frame,
            text="0",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.total_label.pack()

        # Successful
        success_frame = ctk.CTkFrame(stats_grid)
        success_frame.pack(side="left", fill="x", expand=True, padx=2)
        ctk.CTkLabel(success_frame, text="Success", font=ctk.CTkFont(size=11)).pack()
        self.success_label = ctk.CTkLabel(
            success_frame,
            text="0",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#28a745"
        )
        self.success_label.pack()

        # Failed
        failed_frame = ctk.CTkFrame(stats_grid)
        failed_frame.pack(side="left", fill="x", expand=True, padx=2)
        ctk.CTkLabel(failed_frame, text="Failed", font=ctk.CTkFont(size=11)).pack()
        self.failed_label = ctk.CTkLabel(
            failed_frame,
            text="0",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="#dc3545"
        )
        self.failed_label.pack()

        # Tabview for results
        self.tabview = ctk.CTkTabview(right_frame)
        self.tabview.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Add tabs
        self.tabview.add("Successful Numbers")
        self.tabview.add("Failed Numbers")
        self.tabview.add("Log")

        # Successful numbers list
        self.success_text = ctk.CTkTextbox(
            self.tabview.tab("Successful Numbers"),
            font=ctk.CTkFont(size=12)
        )
        self.success_text.pack(fill="both", expand=True)

        # Failed numbers list
        self.failed_text = ctk.CTkTextbox(
            self.tabview.tab("Failed Numbers"),
            font=ctk.CTkFont(size=12)
        )
        self.failed_text.pack(fill="both", expand=True)

        # Log text
        self.log_text = ctk.CTkTextbox(
            self.tabview.tab("Log"),
            font=ctk.CTkFont(size=11)
        )
        self.log_text.pack(fill="both", expand=True)

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
            self.log_message("ERROR: No phone numbers entered!")
            return

        # Parse numbers (one per line)
        numbers = [line.strip() for line in numbers_input.split("\n") if line.strip()]

        if not numbers:
            self.log_message("ERROR: No valid phone numbers found!")
            return

        # Get workers count
        try:
            workers = int(self.workers_var.get())
            if workers < 1 or workers > 100:
                self.log_message("ERROR: Workers must be between 1 and 100!")
                return
        except ValueError:
            self.log_message("ERROR: Invalid workers value!")
            return

        # Reset state
        self.successful_numbers = []
        self.failed_numbers = []
        self.total_numbers = len(numbers)
        self.processed_count = 0
        self.is_running = True

        # Update UI
        self.start_button.configure(
            text="Stop verification sending",
            fg_color="#dc3545",
            hover_color="#c82333"
        )
        self.numbers_text.configure(state="disabled")
        self.workers_spinbox.configure(state="disabled")

        # Clear results
        self.success_text.delete("1.0", "end")
        self.failed_text.delete("1.0", "end")
        self.log_text.delete("1.0", "end")

        # Update stats
        self.total_label.configure(text=str(self.total_numbers))
        self.success_label.configure(text="0")
        self.failed_label.configure(text="0")
        self.progress_label.configure(text=f"Processing: 0/{self.total_numbers}")

        self.log_message(f"Starting to check {self.total_numbers} phone numbers with {workers} workers")

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
        self.log_message("Stopping... (current tasks will finish)")
        self.start_button.configure(
            text="Send verification code",
            fg_color="#28a745",
            hover_color="#218838"
        )
        self.numbers_text.configure(state="normal")
        self.workers_spinbox.configure(state="normal")

    def check_numbers_thread(self, numbers, workers):
        """Thread function to check phone numbers"""
        from concurrent.futures import ThreadPoolExecutor, as_completed

        # Get headless mode setting
        headless_mode = self.headless_var.get()

        def check_single_number(phone_number):
            """Worker function to check a single phone number"""
            if not self.is_running:
                return None

            checker = FacebookNumberChecker(headless=headless_mode)
            try:
                checker.setup_driver()
                checker.search_phone_number(phone_number)
                checker.handle_continuation()
                time.sleep(1)

                # Determine if successful (reached verification code page)
                success = checker.reached_success

                # Get error message if failed
                if not success:
                    error_msg = checker.error_message if checker.error_message else "Unknown error"
                else:
                    error_msg = "Verification code page reached"

                result = {
                    'phone': phone_number,
                    'status': 'success' if success else 'failed',
                    'message': error_msg
                }

                return result
            except Exception as e:
                return {
                    'phone': phone_number,
                    'status': 'error',
                    'message': str(e)
                }
            finally:
                checker.close()

        with ThreadPoolExecutor(max_workers=workers) as executor:
            future_to_phone = {
                executor.submit(check_single_number, phone): phone
                for phone in numbers
            }

            for future in as_completed(future_to_phone):
                if not self.is_running:
                    break

                phone = future_to_phone[future]
                try:
                    result = future.result()
                    if result:
                        self.results_queue.put(result)
                except Exception as e:
                    self.results_queue.put({
                        'phone': phone,
                        'status': 'error',
                        'message': str(e)
                    })

        # Signal completion
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
                        text="Send verification code",
                        fg_color="#28a745",
                        hover_color="#218838"
                    )
                    self.numbers_text.configure(state="normal")
                    self.workers_spinbox.configure(state="normal")
                    self.progress_label.configure(text="Completed!")
                    self.log_message(f"All checks completed! Success: {len(self.successful_numbers)}, Failed: {len(self.failed_numbers)}")
                    continue

                # Process result
                self.processed_count += 1
                phone = result['phone']
                status = result['status']
                message = result['message']

                if status == 'success':
                    self.successful_numbers.append(phone)
                    self.success_text.insert("end", f"{phone}\n")
                    self.log_message(f"✓ SUCCESS: {phone} - {message}")
                else:
                    self.failed_numbers.append(phone)
                    self.failed_text.insert("end", f"{phone} - {message}\n")
                    self.log_message(f"✗ FAILED: {phone} - {message}")

                # Update stats
                self.success_label.configure(text=str(len(self.successful_numbers)))
                self.failed_label.configure(text=str(len(self.failed_numbers)))
                self.progress_label.configure(
                    text=f"Processing: {self.processed_count}/{self.total_numbers}"
                )

        except Exception as e:
            self.log_message(f"UI Update Error: {e}")

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
        """Handle headless mode toggle - adjust workers field accordingly"""
        if not self.headless_var.get():
            # Headless is OFF (visible browser mode)
            # Set workers to 1 and disable the field
            self.workers_var.set("1")
            self.workers_spinbox.configure(state="disabled")
            self.log_message("Headless mode disabled - Workers set to 1 (visible browser mode)")
        else:
            # Headless is ON
            # Enable workers field
            self.workers_spinbox.configure(state="normal")
            self.log_message("Headless mode enabled - Multiple workers available")

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
            self.log_message(f"Scroll sync error: {e}")

    def run(self):
        """Start the GUI application"""
        self.root.mainloop()


if __name__ == "__main__":
    app = FacebookCheckerGUI()
    app.run()
