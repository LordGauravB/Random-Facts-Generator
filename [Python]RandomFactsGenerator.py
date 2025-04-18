import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
import ctypes
from ctypes import wintypes
import pyodbc
from datetime import datetime, timedelta
import pyttsx3
from PIL import Image, ImageTk
import random
import webbrowser
import subprocess
import os
import threading
import signal
import sys
import atexit

class FactDariApp:
    # Database Constants
    CONN_STR = (
        r'DRIVER={SQL Server};'
        r'SERVER=GAURAVS_DESKTOP\SQLEXPRESS;'
        r'DATABASE=FactDari;'
        r'Trusted_Connection=yes;'
    )
    
    # UI Constants
    WINDOW_WIDTH = 500
    WINDOW_HEIGHT = 380
    WINDOW_STATIC_POS = "-1927+7"
    POPUP_POSITION = "-1923+400"
    POPUP_ADD_CARD_SIZE = "496x400"
    POPUP_EDIT_CARD_SIZE = "496x450"
    POPUP_CATEGORIES_SIZE = "400x500"
    CORNER_RADIUS = 15
    
    # Font Constants
    TITLE_FONT = ("Trebuchet MS", 14, 'bold')
    NORMAL_FONT = ("Trebuchet MS", 10)
    SMALL_FONT = ("Trebuchet MS", 8)
    LARGE_FONT = ("Trebuchet MS", 16, 'bold')
    STATS_FONT = ("Trebuchet MS", 9)
    
    # Color Constants
    BG_COLOR = "#1e1e1e"
    TITLE_BG_COLOR = "#000000"
    LISTBOX_BG_COLOR = "#2a2a2a"
    TEXT_COLOR = "white"
    GREEN_COLOR = "#4CAF50"
    BLUE_COLOR = "#2196F3"
    RED_COLOR = "#F44336"
    YELLOW_COLOR = "#FFC107"
    GRAY_COLOR = "#607D8B"
    STATUS_COLOR = "#b66d20"

    def __init__(self):
        # Instance variables (replacing globals)
        self.x_window = 0
        self.y_window = 0
        self.current_factcard_id = None
        self.show_answer = False
        self.is_home_page = True
        
        # Create main window
        self.root = tk.Tk()
        self.root.geometry(f"{self.WINDOW_WIDTH}x{self.WINDOW_HEIGHT}")
        self.root.overrideredirect(True)
        self.root.configure(bg=self.BG_COLOR)
        
        # Set up UI elements
        self.setup_ui()
        
        # Set initial transparency
        self.root.attributes('-alpha', 0.9)
        
        # Bind events
        self.bind_events()
        
        # Final setup
        self.root.update_idletasks()
        self.apply_rounded_corners()
        self.set_static_position()
        self.update_coordinates()
        self.root.after(100, self.update_ui)
        
        # Show the home page
        self.show_home_page()
    
    def setup_ui(self):
        """Set up all UI elements"""
        # Title bar
        self.title_bar = tk.Frame(self.root, bg=self.TITLE_BG_COLOR, height=30, relief='raised')
        self.title_bar.pack(side="top", fill="x")
        
        tk.Label(self.title_bar, text="FactDari", fg=self.TEXT_COLOR, bg=self.TITLE_BG_COLOR, 
                font=(self.NORMAL_FONT[0], 12, 'bold')).pack(side="left", padx=5, pady=5)
        
        # Category selection - create but don't pack yet
        self.category_frame = tk.Frame(self.title_bar, bg='#000000')
        tk.Label(self.category_frame, text="Category:", fg="white", bg='#000000', 
                font=("Trebuchet MS", 8)).pack(side="left", padx=5)
        
        self.category_var = tk.StringVar(self.root, value="All Categories")
        self.category_dropdown = ttk.Combobox(self.category_frame, textvariable=self.category_var, state="readonly", width=15)
        self.category_dropdown['values'] = self.load_categories()
        self.category_dropdown.pack(side="left")
        
        # Main content area
        self.content_frame = tk.Frame(self.root, bg="#1e1e1e")
        self.content_frame.pack(side="top", fill="both", expand=True, padx=10, pady=5)
        
        # Fact card display
        self.factcard_frame = tk.Frame(self.content_frame, bg="#1e1e1e")
        self.factcard_frame.pack(side="top", fill="both", expand=True, pady=5)
        
        # Add top padding to push content down
        self.padding_frame = tk.Frame(self.factcard_frame, bg="#1e1e1e", height=30)
        self.padding_frame.pack(side="top", fill="x")
        
        self.factcard_label = tk.Label(self.factcard_frame, text="Welcome to FactDari!", fg="white", bg="#1e1e1e", 
                                  font=("Trebuchet MS", 16, 'bold'), wraplength=450, justify="center")
        self.factcard_label.pack(side="top", fill="both", expand=True, padx=10, pady=10)
        
        # Create slogan label
        self.slogan_label = tk.Label(self.content_frame, text="Strengthen your knowledge one fact at a time", 
                              fg="#4CAF50", bg="#1e1e1e", font=("Trebuchet MS", 12, 'italic'))
        
        # Create start learning button
        self.start_button = tk.Button(self.content_frame, text="Start Learning", command=self.start_learning, 
                              bg='#4CAF50', fg="white", cursor="hand2", borderwidth=0, 
                              highlightthickness=0, padx=20, pady=10,
                              font=("Trebuchet MS", 14, 'bold'))
        
        # Create a frame for Show Answer and Mastery info
        self.answer_mastery_frame = tk.Frame(self.content_frame, bg="#1e1e1e")
        
        # Show Answer button in the combined frame
        self.show_answer_button = tk.Button(self.answer_mastery_frame, text="Show Answer", command=self.toggle_question_answer, 
                                      bg='#2196F3', fg="white", cursor="hand2", borderwidth=0, 
                                      highlightthickness=0, padx=10, pady=5, state="disabled")
        self.show_answer_button.pack(fill="x", padx=100, pady=2)
        
        # Mastery level display
        self.mastery_level_label = tk.Label(self.answer_mastery_frame, text="Mastery: N/A", fg="white", bg="#1e1e1e", 
                                     font=("Trebuchet MS", 10, 'bold'))
        self.mastery_level_label.pack(side="top", pady=2)
        
        # Add progress bar for mastery
        self.mastery_progress = ttk.Progressbar(self.answer_mastery_frame, orient="horizontal", length=280, mode="determinate")
        self.mastery_progress.pack(side="top", pady=2)
        
        # Style the progress bar
        style = ttk.Style()
        style.theme_use('default')
        style.configure("TProgressbar", thickness=8, troughcolor='#333333', background='#4CAF50')
        
        # Spaced repetition buttons
        self.sr_frame = tk.Frame(self.content_frame, bg="#1e1e1e")
        
        sr_buttons = tk.Frame(self.sr_frame, bg="#1e1e1e")
        sr_buttons.pack(side="top", fill="x")
        
        self.hard_button = tk.Button(sr_buttons, text="Hard", command=self.on_hard_click, bg='#F44336', fg="white", 
                              cursor="hand2", borderwidth=0, highlightthickness=0, padx=10, pady=5)
        self.hard_button.pack(side="left", expand=True, fill="x", padx=(0, 5))
        
        self.medium_button = tk.Button(sr_buttons, text="Medium", command=self.on_medium_click, bg='#FFC107', fg="white", 
                                cursor="hand2", borderwidth=0, highlightthickness=0, padx=10, pady=5)
        self.medium_button.pack(side="left", expand=True, fill="x", padx=(0, 5))
        
        self.easy_button = tk.Button(sr_buttons, text="Easy", command=self.on_easy_click, bg='#4CAF50', fg="white", 
                               cursor="hand2", borderwidth=0, highlightthickness=0, padx=10, pady=5)
        self.easy_button.pack(side="left", expand=True, fill="x")
        
        # Load icons
        self.load_icons()
        
        # Icon buttons frame
        self.icon_buttons_frame = tk.Frame(self.content_frame, bg="#1e1e1e")
        
        # Add button
        self.add_icon_button = tk.Button(self.icon_buttons_frame, image=self.add_icon, bg='#1e1e1e', command=self.add_new_factcard,
                                 cursor="hand2", borderwidth=0, highlightthickness=0)
        self.add_icon_button.pack(side="left", padx=10)
        
        # Create edit button but don't pack it initially
        self.edit_icon_button = tk.Button(self.icon_buttons_frame, image=self.edit_icon, bg='#1e1e1e', command=self.edit_current_factcard,
                                  cursor="hand2", borderwidth=0, highlightthickness=0)
        
        # Create delete button but don't pack it initially
        self.delete_icon_button = tk.Button(self.icon_buttons_frame, image=self.delete_icon, bg='#1e1e1e', command=self.delete_current_factcard,
                                    cursor="hand2", borderwidth=0, highlightthickness=0)
        
        # Status label - always visible
        self.status_label = self.create_label(self.icon_buttons_frame, "", fg="#b66d20", 
                                        font=("Trebuchet MS", 10), side='right')
        self.status_label.pack_configure(pady=5, padx=10)
        
        # Add home and speaker buttons
        self.home_button = tk.Button(self.factcard_frame, image=self.home_icon, bg='#1e1e1e', bd=0, highlightthickness=0, 
                               cursor="hand2", activebackground='#1e1e1e', command=self.show_home_page)
        self.home_button.place(relx=0, rely=0, anchor="nw", x=5, y=5)
        
        self.speaker_button = tk.Button(self.factcard_frame, image=self.speaker_icon, bg='#1e1e1e', command=self.speak_text, 
                                  cursor="hand2", borderwidth=0, highlightthickness=0)
        self.speaker_button.place(relx=1.0, rely=0, anchor="ne", x=-5, y=5)
        
        # Add graph button
        self.graph_button = tk.Button(self.factcard_frame, image=self.graph_icon, bg='#1e1e1e', command=self.show_analytics, 
                                cursor="hand2", borderwidth=0, highlightthickness=0)
        self.graph_button.place(relx=1.0, rely=0, anchor="ne", x=-30, y=5)  # Position it to the left of speaker button
        
        # Bottom stats frame
        self.stats_frame = tk.Frame(self.root, bg="#1e1e1e")
        
        # Stats labels
        self.factcard_count_label = self.create_label(self.stats_frame, "Total Fact Cards: 0", 
                                            font=("Trebuchet MS", 9), side='left')
        self.factcard_count_label.pack_configure(padx=10)
        
        self.due_count_label = self.create_label(self.stats_frame, "Due today: 0", 
                                       font=("Trebuchet MS", 9), side='left')
        self.due_count_label.pack_configure(padx=10)
        
        self.coordinate_label = self.create_label(self.stats_frame, "Coordinates: ", 
                                        font=("Trebuchet MS", 9), side='right')
        self.coordinate_label.pack_configure(padx=10)
        
        # Initially disable the review buttons
        self.show_review_buttons(False)
    
    def load_icons(self):
        """Load all icons used in the application"""
        self.home_icon = ImageTk.PhotoImage(Image.open("C:/Users/gaura/OneDrive/PC-Desktop/GitHubDesktop/Random-Facts-Generator/Resources/Images/home.png").resize((20, 20), Image.Resampling.LANCZOS))
        self.speaker_icon = ImageTk.PhotoImage(Image.open("C:/Users/gaura/OneDrive/PC-Desktop/GitHubDesktop/Random-Facts-Generator/Resources/Images/speaker_icon.png").resize((20, 20), Image.Resampling.LANCZOS))
        self.add_icon = ImageTk.PhotoImage(Image.open("C:/Users/gaura/OneDrive/PC-Desktop/GitHubDesktop/Random-Facts-Generator/Resources/Images/add.png").resize((20, 20), Image.Resampling.LANCZOS))
        self.edit_icon = ImageTk.PhotoImage(Image.open("C:/Users/gaura/OneDrive/PC-Desktop/GitHubDesktop/Random-Facts-Generator/Resources/Images/edit.png").resize((20, 20), Image.Resampling.LANCZOS))
        self.delete_icon = ImageTk.PhotoImage(Image.open("C:/Users/gaura/OneDrive/PC-Desktop/GitHubDesktop/Random-Facts-Generator/Resources/Images/delete.png").resize((20, 20), Image.Resampling.LANCZOS))
        # Add graph icon
        self.graph_icon = ImageTk.PhotoImage(Image.open("C:/Users/gaura/OneDrive/PC-Desktop/GitHubDesktop/Random-Facts-Generator/Resources/Images/graph.png").resize((20, 20), Image.Resampling.LANCZOS))
    
    def bind_events(self):
        """Bind all event handlers"""
        self.title_bar.bind("<Button-1>", self.on_press)
        self.title_bar.bind("<B1-Motion>", self.on_drag)
        self.root.bind("<FocusIn>", lambda event: self.root.attributes('-alpha', 1.0))
        self.root.bind("<FocusOut>", lambda event: self.root.attributes('-alpha', 0.7))
        self.root.bind("<s>", self.set_static_position)
        self.category_dropdown.bind("<<ComboboxSelected>>", self.on_category_change)
    
    def apply_rounded_corners(self, radius=None):
        """Apply rounded corners to the window"""
        if radius is None:
            radius = self.CORNER_RADIUS
            
        hWnd = wintypes.HWND(int(self.root.frame(), 16))
        hRgn = ctypes.windll.gdi32.CreateRoundRectRgn(0, 0, self.root.winfo_width(), self.root.winfo_height(), radius, radius)
        ctypes.windll.user32.SetWindowRgn(hWnd, hRgn, True)
    
    # Database Methods
    def fetch_query(self, query, params=None):
        """Execute a SELECT query and return the results"""
        with pyodbc.connect(self.CONN_STR) as conn:
            with conn.cursor() as cursor:
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                return cursor.fetchall()
    
    def execute_update(self, query, params=None):
        """Execute an UPDATE/INSERT/DELETE query with no return value"""
        with pyodbc.connect(self.CONN_STR) as conn:
            with conn.cursor() as cursor:
                if params:
                    cursor.execute(query, params)
                else:
                    cursor.execute(query)
                conn.commit()
    
    def execute_query(self, query, params=None, fetch=True):
        """Legacy method for backward compatibility"""
        if fetch:
            return self.fetch_query(query, params)
        else:
            self.execute_update(query, params)
            return None
    
    def count_factcards(self):
        """Count total fact cards in the database"""
        return self.fetch_query("SELECT COUNT(*) FROM FactCards")[0][0]
    
    def update_ui(self):
        """Update UI elements periodically"""
        self.update_coordinates()
        if not self.is_home_page:
            self.update_factcard_count()
        self.root.after(100, self.update_ui)
    
    def update_factcard_count(self):
        """Update the fact card count display"""
        num_factcards = self.count_factcards()
        self.factcard_count_label.config(text=f"Total Fact Cards: {num_factcards}")
    
    def on_press(self, event):
        """Handle mouse press on title bar for dragging"""
        self.x_window, self.y_window = event.x, event.y
    
    def update_coordinates(self):
        """Update the coordinate display"""
        x, y = self.root.winfo_x(), self.root.winfo_y()
        self.coordinate_label.config(text=f"Coordinates: {x}, {y}")
    
    def on_drag(self, event):
        """Handle window dragging"""
        x, y = event.x_root - self.x_window, event.y_root - self.y_window
        self.root.geometry(f"+{x}+{y}")
        self.coordinate_label.config(text=f"Coordinates: {x}, {y}")
    
    def set_static_position(self, event=None):
        """Set window to a static position"""
        self.root.geometry(self.WINDOW_STATIC_POS)
        self.update_coordinates()
    
    def speak_text(self):
        """Speak the current fact card text"""
        text = self.factcard_label.cget("text")
        # Remove "Question: " or "Answer: " prefix if present
        if text.startswith("Question: "):
            text = text[10:]
        elif text.startswith("Answer: "):
            text = text[8:]
        
        engine = pyttsx3.init()
        engine.say(text)
        engine.runAndWait()
    
    def show_analytics(self):
        """Launch the analytics web application"""
        # Check if Flask server is already running
        if hasattr(self, 'flask_process') and self.flask_process.poll() is None:
            # Server is running, just open the browser
            webbrowser.open("http://localhost:5000")
        else:
            # Start the Flask server
            self.start_flask_server()
            # Wait a moment for the server to start
            self.root.after(1000, lambda: webbrowser.open("http://localhost:5000"))

    def start_flask_server(self):
        """Start the Flask server in a separate process"""
        # Path to the Flask app.py file
        flask_app_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "analytics_app.py")
        
        # Start Flask server
        if sys.platform.startswith('win'):
            self.flask_process = subprocess.Popen(["python", flask_app_path], 
                                               creationflags=subprocess.CREATE_NEW_PROCESS_GROUP)
        else:
            # Linux/Mac
            self.flask_process = subprocess.Popen(["python3", flask_app_path], 
                                               preexec_fn=os.setsid)
        
        # Register exit handler to close Flask server when the main app exits
        atexit.register(self.close_flask_server)

    def close_flask_server(self):
        """Close the Flask server when the main application exits"""
        if hasattr(self, 'flask_process') and self.flask_process.poll() is None:
            if sys.platform.startswith('win'):
                subprocess.call(['taskkill', '/F', '/T', '/PID', str(self.flask_process.pid)])
            else:
                # Linux/Mac
                os.killpg(os.getpgid(self.flask_process.pid), signal.SIGTERM)
    
    def get_due_factcard_count(self):
        """Get count of fact cards due for review today"""
        current_date = datetime.now().strftime('%Y-%m-%d')
        category = self.category_var.get()
        
        if category == "All Categories":
            query = "SELECT COUNT(*) FROM FactCards WHERE NextReviewDate <= ?"
            result = self.fetch_query(query, (current_date,))
        else:
            query = """
            SELECT COUNT(*) 
            FROM FactCards f
            JOIN Categories c ON f.CategoryID = c.CategoryID
            WHERE f.NextReviewDate <= ? AND c.CategoryName = ?
            """
            result = self.fetch_query(query, (current_date, category))
        
        return result[0][0] if result else 0
    
    def get_next_review_info(self):
        """Get information about the next review date after today"""
        current_date = datetime.now().strftime('%Y-%m-%d')
        category = self.category_var.get()
        
        if category == "All Categories":
            query = """
                SELECT MIN(NextReviewDate)
                FROM FactCards 
                WHERE NextReviewDate > ?
            """
            result = self.execute_query(query, (current_date,))
        else:
            query = """
                SELECT MIN(f.NextReviewDate)
                FROM FactCards f
                JOIN Categories c ON f.CategoryID = c.CategoryID
                WHERE f.NextReviewDate > ? AND c.CategoryName = ?
            """
            result = self.execute_query(query, (current_date, category))
        
        if result and result[0][0]:
            next_date = result[0][0]
            # Count fact cards due on the next date
            if category == "All Categories":
                query = """
                    SELECT COUNT(*)
                    FROM FactCards 
                    WHERE NextReviewDate = ?
                """
                count_result = self.execute_query(query, (next_date,))
            else:
                query = """
                    SELECT COUNT(*)
                    FROM FactCards f
                    JOIN Categories c ON f.CategoryID = c.CategoryID
                    WHERE f.NextReviewDate = ? AND c.CategoryName = ?
                """
                count_result = self.execute_query(query, (next_date, category))
            count = count_result[0][0] if count_result else 0
            return next_date, count
        return None, 0
    
    def toggle_question_answer(self):
        """Toggle between showing question and answer"""
        if self.current_factcard_id is None:
            return
        
        # Toggle between question and answer
        self.show_answer = not self.show_answer
        
        if self.show_answer:
            # Fetch the answer from the database
            query = "SELECT Answer FROM FactCards WHERE FactCardID = ?"
            answer = self.fetch_query(query, (self.current_factcard_id,))[0][0]
            self.factcard_label.config(text=f"Answer: {answer}", font=(self.NORMAL_FONT[0], self.adjust_font_size(answer)))
            self.show_answer_button.config(text="Show Question")
        else:
            # Show the question again
            query = "SELECT Question FROM FactCards WHERE FactCardID = ?"
            question = self.fetch_query(query, (self.current_factcard_id,))[0][0]
            self.factcard_label.config(text=f"Question: {question}", font=(self.NORMAL_FONT[0], self.adjust_font_size(question)))
            self.show_answer_button.config(text="Show Answer")
        
        # Keep mastery display updated
        self.update_mastery_display()
    
    def update_mastery_display(self):
        """Update the visual display of the mastery level for the current card"""
        if self.current_factcard_id:
            query = "SELECT Mastery FROM FactCards WHERE FactCardID = ?"
            mastery = self.fetch_query(query, (self.current_factcard_id,))[0][0]
            
            # Update the mastery progress in the UI
            mastery_percentage = int(mastery * 100)
            self.mastery_level_label.config(text=f"Mastery: {mastery_percentage}%")
            
            # Update progress bar
            self.mastery_progress["value"] = mastery_percentage
            
            # Change color based on mastery level
            if mastery < 0.3:
                self.mastery_level_label.config(fg=self.RED_COLOR)  # Red for low mastery
            elif mastery < 0.7:
                self.mastery_level_label.config(fg=self.YELLOW_COLOR)  # Yellow for medium mastery
            else:
                self.mastery_level_label.config(fg=self.GREEN_COLOR)  # Green for high mastery
        else:
            # No card selected
            self.mastery_level_label.config(text="Mastery: N/A")
            self.mastery_progress["value"] = 0
    
    def clear_status_after_delay(self, delay_ms=3000):
        """Clear the status message after a specified delay"""
        self.root.after(delay_ms, lambda: self.status_label.config(text=""))
    
    def fetch_due_factcard(self):
        """Fetch a fact card due for review"""
        category = self.category_var.get()
        current_date = datetime.now().strftime('%Y-%m-%d')
        
        # Reset the show_answer state for new fact card
        self.show_answer = False
        
        # Get fact cards due for review today or earlier
        if category == "All Categories":
            query = """
                SELECT TOP 1 FactCardID, Question, Answer, NextReviewDate, CurrentInterval, Mastery
                FROM FactCards
                WHERE NextReviewDate <= ?
                ORDER BY NextReviewDate, NEWID()
            """
            factcard = self.execute_query(query, (current_date,))
        else:
            query = """
                SELECT TOP 1 f.FactCardID, f.Question, f.Answer, f.NextReviewDate, f.CurrentInterval, f.Mastery
                FROM FactCards f
                JOIN Categories c ON f.CategoryID = c.CategoryID
                WHERE c.CategoryName = ? AND f.NextReviewDate <= ?
                ORDER BY f.NextReviewDate, NEWID()
            """
            factcard = self.execute_query(query, (category, current_date))
        
        if factcard:
            # We have a fact card due for review
            factcard_id = factcard[0][0]
            question = factcard[0][1]
            self.current_factcard_id = factcard_id
            
            # Show the question
            self.show_review_buttons(True)
            self.show_answer_button.config(state="normal")
            return f"Question: {question}"
        else:
            # No fact cards due for review
            self.current_factcard_id = None
            next_date, count = self.get_next_review_info()
            self.show_review_buttons(False)
            self.show_answer_button.config(state="disabled")
            
            if next_date:
                next_date_str = next_date.strftime('%Y-%m-%d') if isinstance(next_date, datetime) else next_date
                return f"No fact cards due for review today.\n\nNext review date: {next_date_str}\nFact cards due on that day: {count}"
            else:
                return "No fact cards found. Add some fact cards first!"
    
    def load_next_factcard(self):
        """Load the next due fact card"""
        factcard_text = self.fetch_due_factcard()
        if factcard_text:
            self.factcard_label.config(text=factcard_text, font=("Trebuchet MS", self.adjust_font_size(factcard_text)))
            self.update_mastery_display()  # Update the mastery display
        else:
            self.factcard_label.config(text="No fact cards found.", font=("Trebuchet MS", 12))
            self.mastery_level_label.config(text="Mastery: N/A")
            self.mastery_progress["value"] = 0
        self.update_due_count()
    
    def update_due_count(self):
        """Update the count of fact cards due today"""
        due_count = self.get_due_factcard_count()
        self.due_count_label.config(text=f"Due today: {due_count}")
    
    def show_review_buttons(self, show):
        """Show or hide the spaced repetition buttons"""
        state = "normal" if show else "disabled"
        self.hard_button.config(state=state)
        self.medium_button.config(state=state)
        self.easy_button.config(state=state)
        
        # Instead of disabling, completely hide or show the edit and delete buttons
        if show:
            # Show buttons if there's a fact card to review
            self.edit_icon_button.pack(side="left", padx=10)
            self.delete_icon_button.pack(side="left", padx=10)
        else:
            # Hide buttons if there's no fact card
            self.edit_icon_button.pack_forget()
            self.delete_icon_button.pack_forget()
    
    def update_factcard_schedule(self, difficulty):
        """Update the fact card's review schedule based on difficulty rating and adjust mastery level"""
        if not self.current_factcard_id:
            return
        
        # Disable buttons immediately to prevent multiple clicks
        self.show_review_buttons(False)
            
        # Calculate new mastery level and interval
        new_mastery, new_interval = self._calculate_new_mastery_and_interval(difficulty)
        
        # Calculate the next review date
        next_review_date = self._calculate_next_review_date(difficulty, new_interval)
        
        # Update the database
        self._update_factcard_in_database(next_review_date, new_interval, new_mastery)
        
        # Show feedback to the user
        self._show_schedule_feedback(difficulty, new_interval, new_mastery)
        
        # Load the next fact card after a short delay
        self.root.after(1000, self.load_next_factcard)
    
    def _calculate_new_mastery_and_interval(self, difficulty):
        """Calculate new mastery level and interval based on difficulty rating"""
        # Get current interval and mastery level
        query = "SELECT CurrentInterval, Mastery FROM FactCards WHERE FactCardID = ?"
        result = self.fetch_query(query, (self.current_factcard_id,))[0]
        current_interval, current_mastery = result[0], result[1]
        
        if difficulty == "Hard":
            # Decrease mastery when struggling (min 0.0)
            new_mastery = max(0.0, current_mastery - 0.1)
            new_interval = 1  # Reset interval
        elif difficulty == "Medium":
            # Small increase in mastery
            new_mastery = min(1.0, current_mastery + 0.05)
            # Adjust multiplier based on mastery level
            multiplier = 1.3 + (current_mastery * 0.4)  # ranges from 1.3 to 1.7
            new_interval = int(current_interval * multiplier)
        else:  # Easy
            # Larger increase in mastery
            new_mastery = min(1.0, current_mastery + 0.15)
            # Adjust multiplier based on mastery level
            multiplier = 2.0 + (current_mastery * 1.0)  # ranges from 2.0 to 3.0
            new_interval = int(current_interval * multiplier)
            
        return new_mastery, new_interval
    
    def _calculate_next_review_date(self, difficulty, interval):
        """Calculate the next review date based on difficulty and interval"""
        if difficulty == "Hard":
            # For Hard, set the next review date to TODAY
            return datetime.now().strftime('%Y-%m-%d')
        else:
            # For Medium and Easy, add the interval days
            return (datetime.now() + timedelta(days=interval)).strftime('%Y-%m-%d')
    
    def _update_factcard_in_database(self, next_review_date, new_interval, new_mastery):
        """Update the fact card in the database with new review schedule and mastery"""
        self.execute_update(
            """
            UPDATE FactCards 
            SET NextReviewDate = ?, CurrentInterval = ?, Mastery = ?, ViewCount = ViewCount + 1, LastReviewDate = GETDATE()
            WHERE FactCardID = ?
            """, 
            (next_review_date, new_interval, new_mastery, self.current_factcard_id)
        )
    
    def _show_schedule_feedback(self, difficulty, interval, mastery):
        """Show feedback to the user about the new schedule and mastery level"""
        mastery_percentage = int(mastery * 100)
        
        if difficulty == "Hard":
            feedback_text = f"Rated as {difficulty}. Next review today. Mastery: {mastery_percentage}%"
        else:
            feedback_text = f"Rated as {difficulty}. Next review in {interval} days. Mastery: {mastery_percentage}%"
        
        self.status_label.config(text=feedback_text, fg=self.STATUS_COLOR)
        
        # Schedule clearing the status after 3 seconds
        self.clear_status_after_delay(3000)
    
    def on_hard_click(self):
        self.update_factcard_schedule("Hard")
    
    def on_medium_click(self):
        self.update_factcard_schedule("Medium")
    
    def on_easy_click(self):
        self.update_factcard_schedule("Easy")
    
    def add_new_factcard(self):
        """Add a new fact card to the database"""
        # Create a popup window
        add_window = tk.Toplevel(self.root)
        add_window.title("Add New Fact Card")
        add_window.geometry(f"{self.POPUP_ADD_CARD_SIZE}{self.POPUP_POSITION}")
        add_window.configure(bg=self.BG_COLOR)
        
        # Get categories for dropdown
        categories = self.execute_query("SELECT CategoryName FROM Categories WHERE IsActive = 1")
        category_names = [cat[0] for cat in categories]
        
        # Create and place widgets
        tk.Label(add_window, text="Add New Fact Card", fg="white", bg="#1e1e1e", 
                font=("Trebuchet MS", 14, 'bold')).pack(pady=10)
        
        # Category selection
        cat_frame = tk.Frame(add_window, bg="#1e1e1e")
        cat_frame.pack(fill="x", padx=20, pady=5)
        
        tk.Label(cat_frame, text="Category:", fg="white", bg="#1e1e1e", 
                font=("Trebuchet MS", 10)).pack(side="left", padx=5)
        
        cat_var = tk.StringVar(add_window)
        cat_var.set(category_names[0] if category_names else "No Categories")
        
        cat_dropdown = ttk.Combobox(cat_frame, textvariable=cat_var, values=category_names, state="readonly", width=20)
        cat_dropdown.pack(side="left", padx=5, fill="x", expand=True)
        
        # Question
        q_frame = tk.Frame(add_window, bg="#1e1e1e")
        q_frame.pack(fill="x", padx=20, pady=5)
        
        tk.Label(q_frame, text="Question:", fg="white", bg="#1e1e1e", 
                font=("Trebuchet MS", 10)).pack(side="top", anchor="w", padx=5)
        
        question_text = tk.Text(q_frame, height=4, width=40, font=("Trebuchet MS", 10))
        question_text.pack(fill="x", padx=5, pady=5)
        
        # Answer
        a_frame = tk.Frame(add_window, bg="#1e1e1e")
        a_frame.pack(fill="x", padx=20, pady=5)
        
        tk.Label(a_frame, text="Answer:", fg="white", bg="#1e1e1e", 
                font=("Trebuchet MS", 10)).pack(side="top", anchor="w", padx=5)
        
        answer_text = tk.Text(a_frame, height=4, width=40, font=("Trebuchet MS", 10))
        answer_text.pack(fill="x", padx=5, pady=5)
        
        def save_factcard():
            category = cat_var.get()
            question = question_text.get("1.0", "end-1c").strip()
            answer = answer_text.get("1.0", "end-1c").strip()
            
            if not question or not answer:
                self.status_label.config(text="Question and answer are required!", fg="#ff0000")
                self.clear_status_after_delay(3000)
                return
            
            # Get category ID
            category_id = self.execute_query("SELECT CategoryID FROM Categories WHERE CategoryName = ?", (category,))[0][0]
            
            # Insert the new fact card - now including default Mastery of 0.0
            self.execute_query(
                """
                INSERT INTO FactCards (CategoryID, Question, Answer, NextReviewDate, CurrentInterval, Mastery, DateAdded) 
                VALUES (?, ?, ?, GETDATE(), 1, 0.0, GETDATE())
                """, 
                (category_id, question, answer), 
                fetch=False
            )
            
            add_window.destroy()
            self.status_label.config(text="New fact card added successfully!", fg="#4CAF50")
            self.clear_status_after_delay(3000)
            self.update_factcard_count()
            self.update_due_count()
            # If no current card is shown, load the newly added card
            if self.current_factcard_id is None:
                self.load_next_factcard()
        
        # Save button
        save_button = tk.Button(add_window, text="Save Fact Card", bg='#4CAF50', fg="white", 
                              command=save_factcard, cursor="hand2", borderwidth=0, 
                              highlightthickness=0, padx=10, pady=5,
                              font=("Trebuchet MS", 10, 'bold'))
        save_button.pack(pady=20)
    
    def edit_current_factcard(self):
        """Edit the current fact card"""
        if not self.current_factcard_id:
            return
        
        # Get current fact card data
        query = """
        SELECT f.Question, f.Answer, c.CategoryName, f.Mastery
        FROM FactCards f 
        JOIN Categories c ON f.CategoryID = c.CategoryID
        WHERE f.FactCardID = ?
        """
        data = self.fetch_query(query, (self.current_factcard_id,))[0]
        current_question, current_answer, current_category, current_mastery = data
        
        # Create a popup window
        edit_window = tk.Toplevel(self.root)
        edit_window.title("Edit Fact Card")
        edit_window.geometry(f"{self.POPUP_EDIT_CARD_SIZE}{self.POPUP_POSITION}")
        edit_window.configure(bg=self.BG_COLOR)
        
        # Get categories for dropdown
        categories = self.execute_query("SELECT CategoryName FROM Categories WHERE IsActive = 1")
        category_names = [cat[0] for cat in categories]
        
        # Create and place widgets
        tk.Label(edit_window, text="Edit Fact Card", fg="white", bg="#1e1e1e", 
                font=("Trebuchet MS", 14, 'bold')).pack(pady=10)
        
        # Category selection
        cat_frame = tk.Frame(edit_window, bg="#1e1e1e")
        cat_frame.pack(fill="x", padx=20, pady=5)
        
        tk.Label(cat_frame, text="Category:", fg="white", bg="#1e1e1e", 
                font=("Trebuchet MS", 10)).pack(side="left", padx=5)
        
        cat_var = tk.StringVar(edit_window)
        cat_var.set(current_category)
        
        cat_dropdown = ttk.Combobox(cat_frame, textvariable=cat_var, values=category_names, state="readonly", width=20)
        cat_dropdown.pack(side="left", padx=5, fill="x", expand=True)
        
        # Question
        q_frame = tk.Frame(edit_window, bg="#1e1e1e")
        q_frame.pack(fill="x", padx=20, pady=5)
        
        tk.Label(q_frame, text="Question:", fg="white", bg="#1e1e1e", 
                font=("Trebuchet MS", 10)).pack(side="top", anchor="w", padx=5)
        
        question_text = tk.Text(q_frame, height=4, width=40, font=("Trebuchet MS", 10))
        question_text.insert("1.0", current_question)
        question_text.pack(fill="x", padx=5, pady=5)
        
        # Answer
        a_frame = tk.Frame(edit_window, bg="#1e1e1e")
        a_frame.pack(fill="x", padx=20, pady=5)
        
        tk.Label(a_frame, text="Answer:", fg="white", bg="#1e1e1e", 
                font=("Trebuchet MS", 10)).pack(side="top", anchor="w", padx=5)
        
        answer_text = tk.Text(a_frame, height=4, width=40, font=("Trebuchet MS", 10))
        answer_text.insert("1.0", current_answer)
        answer_text.pack(fill="x", padx=5, pady=5)
        
        # Mastery level slider
        m_frame = tk.Frame(edit_window, bg="#1e1e1e")
        m_frame.pack(fill="x", padx=20, pady=5)
        
        tk.Label(m_frame, text=f"Mastery Level: {int(current_mastery * 100)}%", fg="white", bg="#1e1e1e", 
                font=("Trebuchet MS", 10)).pack(side="top", anchor="w", padx=5)
        
        mastery_var = tk.DoubleVar(edit_window, value=current_mastery)
        
        def update_mastery_label(val):
            mastery_val = int(float(val) * 100)
            m_frame.winfo_children()[0].config(text=f"Mastery Level: {mastery_val}%")
        
        mastery_slider = ttk.Scale(m_frame, from_=0.0, to=1.0, orient="horizontal",
                                variable=mastery_var, command=update_mastery_label)
        mastery_slider.pack(fill="x", padx=5, pady=5)
        
        def update_factcard():
            category = cat_var.get()
            question = question_text.get("1.0", "end-1c").strip()
            answer = answer_text.get("1.0", "end-1c").strip()
            mastery = mastery_var.get()
            
            if not question or not answer:
                self.status_label.config(text="Question and answer are required!", fg="#ff0000")
                self.clear_status_after_delay(3000)
                return
            
            # Get category ID
            category_id = self.execute_query("SELECT CategoryID FROM Categories WHERE CategoryName = ?", (category,))[0][0]
            
            # Update the fact card including mastery
            self.execute_query(
                """
                    UPDATE FactCards 
                    SET CategoryID = ?, Question = ?, Answer = ?, Mastery = ?, LastEditedDate = GETDATE()
                    WHERE FactCardID = ?
                    """, 
                    (category_id, question, answer, mastery, self.current_factcard_id), 
                    fetch=False
            )
            
            edit_window.destroy()
            self.status_label.config(text="Fact card updated successfully!", fg="#4CAF50")
            self.clear_status_after_delay(3000)
            
            # Refresh the current card display
            if self.show_answer:
                self.factcard_label.config(text=f"Answer: {answer}", font=("Trebuchet MS", self.adjust_font_size(answer)))
            else:
                self.factcard_label.config(text=f"Question: {question}", font=("Trebuchet MS", self.adjust_font_size(question)))
            
            # Update mastery display
            self.update_mastery_display()
        
        # Update button
        update_button = tk.Button(edit_window, text="Update Fact Card", bg='#2196F3', fg="white", 
                                command=update_factcard, cursor="hand2", borderwidth=0, 
                                highlightthickness=0, padx=10, pady=5,
                                font=("Trebuchet MS", 10, 'bold'))
        update_button.pack(pady=20)
    
    def delete_current_factcard(self):
        """Delete the current fact card"""
        if not self.current_factcard_id:
            return
        
        # Ask for confirmation
        if tk.messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this fact card?"):
            # Delete the fact card
            self.execute_query("DELETE FROM FactCards WHERE FactCardID = ?", (self.current_factcard_id,), fetch=False)
            self.status_label.config(text="Fact card deleted!", fg="#F44336")
            self.clear_status_after_delay(3000)
            self.update_factcard_count()
            self.update_due_count()
            # Load the next fact card
            self.load_next_factcard()
    
    def manage_categories(self):
        """Open a window to manage categories"""
        # Create the category management window
        cat_window = self._create_category_window()
        
        # Create the UI components
        add_frame, new_cat_entry = self._create_add_category_ui(cat_window)
        list_frame, cat_listbox, refresh_category_list = self._create_category_list_ui(cat_window)
        self._create_category_action_buttons(cat_window, cat_listbox, refresh_category_list)
        
        # Initialize the category list
        refresh_category_list()
    
    def _create_category_window(self):
        """Create the main category management window"""
        cat_window = tk.Toplevel(self.root)
        cat_window.title("Manage Categories")
        cat_window.geometry(self.POPUP_CATEGORIES_SIZE)
        cat_window.configure(bg=self.BG_COLOR)
        
        # Create header
        tk.Label(cat_window, text="Manage Categories", fg=self.TEXT_COLOR, bg=self.BG_COLOR, 
                font=self.TITLE_FONT).pack(pady=10)
        
        return cat_window
    
    def _create_add_category_ui(self, parent):
        """Create the UI for adding a new category"""
        # Add new category frame
        add_frame = tk.Frame(parent, bg=self.BG_COLOR)
        add_frame.pack(fill="x", padx=20, pady=10)
        
        tk.Label(add_frame, text="New Category:", fg=self.TEXT_COLOR, bg=self.BG_COLOR, 
                font=self.NORMAL_FONT).pack(side="left", padx=5)
        
        new_cat_entry = tk.Entry(add_frame, width=20, font=self.NORMAL_FONT)
        new_cat_entry.pack(side="left", padx=5, fill="x", expand=True)
        
        add_button = tk.Button(add_frame, text="Add", bg=self.GREEN_COLOR, fg=self.TEXT_COLOR, 
                            command=lambda: self._add_category(new_cat_entry), 
                            cursor="hand2", borderwidth=0, highlightthickness=0, padx=10)
        add_button.pack(side="left", padx=5)
        
        return add_frame, new_cat_entry
    
    def _add_category(self, entry_widget):
        """Handle adding a new category"""
        new_cat = entry_widget.get().strip()
        if not new_cat:
            return
        
        # Check if category already exists
        existing = self.fetch_query("SELECT COUNT(*) FROM Categories WHERE CategoryName = ?", (new_cat,))[0][0]
        if existing > 0:
            tk.messagebox.showinfo("Error", f"Category '{new_cat}' already exists!")
            return
        
        # Add the new category
        self.execute_update(
            "INSERT INTO Categories (CategoryName, Description) VALUES (?, '')", 
            (new_cat,)
        )
        
        entry_widget.delete(0, tk.END)
        
        # Refresh UI elements
        self.update_category_dropdown()
        return True  # Indicate success for refresh_category_list callback
    
    def _create_category_list_ui(self, parent):
        """Create the UI for displaying and managing the category list"""
        # Category list frame
        list_frame = tk.Frame(parent, bg=self.BG_COLOR)
        list_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        tk.Label(list_frame, text="Existing Categories:", fg=self.TEXT_COLOR, bg=self.BG_COLOR, 
                font=(self.NORMAL_FONT[0], self.NORMAL_FONT[1], 'bold')).pack(anchor="w", pady=5)
        
        # Scrollable list frame
        scroll_frame = tk.Frame(list_frame, bg=self.BG_COLOR)
        scroll_frame.pack(fill="both", expand=True)
        
        scrollbar = tk.Scrollbar(scroll_frame)
        scrollbar.pack(side="right", fill="y")
        
        cat_listbox = tk.Listbox(scroll_frame, height=15, width=30, font=self.NORMAL_FONT,
                              yscrollcommand=scrollbar.set, bg=self.LISTBOX_BG_COLOR, fg=self.TEXT_COLOR,
                              selectbackground=self.GREEN_COLOR, selectforeground=self.TEXT_COLOR)
        cat_listbox.pack(side="left", fill="both", expand=True)
        
        scrollbar.config(command=cat_listbox.yview)
        
        def refresh_category_list():
            cat_listbox.delete(0, tk.END)
            categories = self.fetch_query("SELECT CategoryName, CategoryID FROM Categories ORDER BY CategoryName")
            for cat in categories:
                cat_listbox.insert(tk.END, f"{cat[0]} (ID: {cat[1]})")
        
        return list_frame, cat_listbox, refresh_category_list
    
    def _create_category_action_buttons(self, parent, cat_listbox, refresh_callback):
        """Create action buttons for category management"""
        # Action buttons frame
        action_frame = tk.Frame(parent, bg=self.BG_COLOR)
        action_frame.pack(fill="x", padx=20, pady=10)
        
        # Rename button
        rename_button = tk.Button(action_frame, text="Rename", bg=self.BLUE_COLOR, fg=self.TEXT_COLOR, 
                                command=lambda: self._rename_category(cat_listbox, refresh_callback), 
                                cursor="hand2", borderwidth=0, highlightthickness=0, padx=10, pady=5)
        rename_button.pack(side="left", padx=5)
        
        # Delete button
        delete_button_cat = tk.Button(action_frame, text="Delete", bg=self.RED_COLOR, fg=self.TEXT_COLOR, 
                                    command=lambda: self._delete_category(cat_listbox, refresh_callback), 
                                    cursor="hand2", borderwidth=0, highlightthickness=0, padx=10, pady=5)
        delete_button_cat.pack(side="left", padx=5)
        
        # Close button
        close_button = tk.Button(parent, text="Close", bg=self.GRAY_COLOR, fg=self.TEXT_COLOR, 
                              command=parent.destroy, cursor="hand2", borderwidth=0, 
                              highlightthickness=0, padx=20, pady=5,
                              font=(self.NORMAL_FONT[0], self.NORMAL_FONT[1], 'bold'))
        close_button.pack(pady=15)
    
    def _rename_category(self, cat_listbox, refresh_callback):
        """Handle renaming a category"""
        selection = cat_listbox.curselection()
        if not selection:
            return
        
        # Extract category ID from selection text
        cat_text = cat_listbox.get(selection[0])
        cat_id = int(cat_text.split("ID: ")[1].strip(")"))
        
        # Get current name
        cat_name = self.fetch_query("SELECT CategoryName FROM Categories WHERE CategoryID = ?", (cat_id,))[0][0]
        
        # Ask for new name
        new_name = simpledialog.askstring("Rename Category", f"New name for '{cat_name}':", initialvalue=cat_name)
        if not new_name or new_name == cat_name:
            return
        
        # Check if the new name already exists
        existing = self.fetch_query(
            "SELECT COUNT(*) FROM Categories WHERE CategoryName = ? AND CategoryID != ?", 
            (new_name, cat_id)
        )[0][0]
        
        if existing > 0:
            tk.messagebox.showinfo("Error", f"Category '{new_name}' already exists!")
            return
        
        # Update the category
        self.execute_update(
            "UPDATE Categories SET CategoryName = ? WHERE CategoryID = ?", 
            (new_name, cat_id)
        )
        
        refresh_callback()
        self.update_category_dropdown()
    
    def _delete_category(self, cat_listbox, refresh_callback):
        """Handle deleting a category"""
        selection = cat_listbox.curselection()
        if not selection:
            return
        
        # Extract category ID from selection text
        cat_text = cat_listbox.get(selection[0])
        cat_id = int(cat_text.split("ID: ")[1].strip(")"))
        cat_name = cat_text.split(" (ID:")[0]
        
        # Check if category has fact cards
        card_count = self.fetch_query(
            "SELECT COUNT(*) FROM FactCards WHERE CategoryID = ?", 
            (cat_id,)
        )[0][0]
        
        if card_count > 0:
            if not tk.messagebox.askyesno(
                "Warning", 
                f"Category '{cat_name}' has {card_count} fact cards. " +
                "Deleting it will also delete all associated fact cards. Continue?"
            ):
                return
        
        # Delete the category and its fact cards
        self.execute_update("""
            BEGIN TRANSACTION;
            
            DELETE FROM FactCardTags WHERE FactCardID IN (SELECT FactCardID FROM FactCards WHERE CategoryID = ?);
            DELETE FROM FactCards WHERE CategoryID = ?;
            DELETE FROM Categories WHERE CategoryID = ?;
            
            COMMIT TRANSACTION;
        """, (cat_id, cat_id, cat_id))
        
        refresh_callback()
        self.update_category_dropdown()
        self.update_factcard_count()
        self.update_due_count()
    
    def load_categories(self):
        """Load categories for the dropdown"""
        query = "SELECT DISTINCT CategoryName FROM Categories WHERE IsActive = 1 ORDER BY CategoryName"
        categories = self.execute_query(query)
        category_names = [category[0] for category in categories] if categories else []
        category_names.insert(0, "All Categories")  # Add All Categories option
        return category_names
    
    def update_category_dropdown(self):
        """Update the category dropdown with current categories"""
        categories = self.load_categories()
        self.category_dropdown['values'] = categories
        # Keep current selection if it exists in new list, otherwise reset
        current_category = self.category_var.get()
        if current_category in categories:
            self.category_var.set(current_category)
        else:
            self.category_var.set("All Categories")
    
    def adjust_font_size(self, text):
        """Dynamically adjust font size based on text length"""
        return max(8, min(12, int(12 - (len(text) / 150))))
    
    def create_label(self, parent, text, fg="white", cursor=None, font=("Trebuchet MS", 7), side='left'):
        """Create a styled label"""
        label = tk.Label(parent, text=text, fg=fg, bg="#1e1e1e", font=font)
        if cursor:
            label.configure(cursor=cursor)
        label.pack(side=side)
        return label
    
    def on_category_change(self, event=None):
        """Handle category dropdown change"""
        self.load_next_factcard()
    
    def reset_to_welcome(self):
        """Reset to welcome screen"""
        self.factcard_label.config(text="Welcome to FactDari!", 
                              font=("Trebuchet MS", self.adjust_font_size("Welcome to FactDari!")))
        self.status_label.config(text="")
        self.show_review_buttons(False)
        self.show_answer_button.config(state="disabled")
        self.mastery_level_label.config(text="Mastery: N/A")
        self.mastery_progress["value"] = 0
        self.update_due_count()
    
    def show_home_page(self):
        """Show the home page with welcome message and start button"""
        self.is_home_page = True
        
        # Hide all fact card-related UI elements
        self.stats_frame.pack_forget()
        self.icon_buttons_frame.pack_forget()
        self.sr_frame.pack_forget()
        self.answer_mastery_frame.pack_forget()
        self.category_frame.pack_forget()
        
        # Update the welcome message
        self.factcard_label.config(text="Welcome to FactDari!\n\nYour Personal Knowledge Companion", 
                             font=self.LARGE_FONT,
                             wraplength=450, justify="center")
        
        # Show the slogan
        self.slogan_label.config(text="Strengthen your knowledge one fact at a time")
        self.slogan_label.pack(side="top", pady=5)
        
        # Show the start learning button
        self.start_button.pack(pady=20)
        
        # Apply rounded corners again after UI changes
        self.root.update_idletasks()
        self.apply_rounded_corners()
    
    def start_learning(self):
        """Switch from home page to learning interface"""
        self.is_home_page = False
        
        # Hide home page elements
        self.slogan_label.pack_forget()
        self.start_button.pack_forget()
        
        # Show all fact card-related UI elements
        self.category_frame.pack(side="right", padx=5, pady=3)
        self.answer_mastery_frame.pack(side="top", fill="x", pady=0)
        self.sr_frame.pack(side="top", fill="x", pady=5)
        self.icon_buttons_frame.pack(side="top", fill="x", pady=5)
        self.stats_frame.pack(side="bottom", fill="x", padx=10, pady=3)
        
        # Load the first fact card
        self.load_next_factcard()
        
        # Apply rounded corners again after UI changes
        self.root.update_idletasks()
        self.apply_rounded_corners()
    
    def run(self):
        """Start the application mainloop"""
        self.root.mainloop()


# Usage example
if __name__ == "__main__":
    app = FactDariApp()
    app.run()