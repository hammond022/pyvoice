import tkinter as tk
from tkinter import scrolledtext, simpledialog, messagebox, ttk
import threading
import queue
import speech_module
from telegram_module import TelegramBot
from users import UserAuth
from config import save_config, load_config

speech_queue = queue.Queue()
telegram_bot = None
root = None
terminal = None
keyword_list = None

# Load saved configuration
saved_token, keywords, keyword_data = load_config()

# Add UI constants and styles at the top after imports
COLORS = {
    'primary': '#1a73e8',
    'primary_dark': '#1557b0',
    'error': '#ea4335',
    'success': '#34a853',
    'background': '#f0f2f5',
    'surface': '#ffffff',
    'text': '#202124',
    'text_secondary': '#5f6368'
}

class ModernButton(tk.Button):
    def __init__(self, master, **kwargs):
        kwargs['relief'] = 'flat'
        kwargs['cursor'] = 'hand2'
        kwargs['font'] = ('Segoe UI', 10)
        kwargs['pady'] = 8
        kwargs['padx'] = 15
        super().__init__(master, **kwargs)
        self.bind('<Enter>', self.on_enter)
        self.bind('<Leave>', self.on_leave)
        
    def on_enter(self, e):
        if self['state'] != 'disabled':
            self.configure(background=self.darken_color(self['background']))
            
    def on_leave(self, e):
        if self['state'] != 'disabled':
            self.configure(background=self.original_color)
            
    def configure(self, **kwargs):
        if 'background' in kwargs:
            self.original_color = kwargs['background']
        super().configure(**kwargs)
        
    @staticmethod
    def darken_color(hex_color):
        """Darken a hex color by 20%"""
        # Remove the '#' if present
        hex_color = hex_color.lstrip('#')
        
        # Convert hex to RGB
        rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        
        # Darken by reducing each component by 20%
        darkened = tuple(max(0, int(x * 0.8)) for x in rgb)
        
        # Convert back to hex
        return f"#{darkened[0]:02x}{darkened[1]:02x}{darkened[2]:02x}"

class ModernEntry(tk.Entry):
    def __init__(self, master, **kwargs):
        kwargs['relief'] = 'flat'
        kwargs['font'] = ('Segoe UI', 10)
        kwargs['bg'] = COLORS['surface']
        super().__init__(master, **kwargs)
        self.configure(highlightthickness=1, highlightbackground='#e0e0e0')
        self.bind('<FocusIn>', self.on_focus_in)
        self.bind('<FocusOut>', self.on_focus_out)
        
    def on_focus_in(self, e):
        self.configure(highlightbackground=COLORS['primary'], highlightcolor=COLORS['primary'])
        
    def on_focus_out(self, e):
        self.configure(highlightbackground='#e0e0e0', highlightcolor='#e0e0e0')

def initialize_telegram():
    global telegram_bot, saved_token
    try:
        token = simpledialog.askstring("Telegram Bot", "Enter your Telegram bot token:", initialvalue=saved_token or "")
        if token:
            # Clean the token
            token = token.strip().replace('\n', '').replace('\r', '')
            telegram_bot = TelegramBot(token)
            saved_token = token
            save_config(telegram_token=token)
            update_terminal("Telegram bot initialized")
        else:
            update_terminal("Telegram bot initialization cancelled")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to initialize Telegram bot: {str(e)}")
        update_terminal(f"Telegram bot initialization failed: {str(e)}")
        telegram_bot = None

def update_terminal(text):
    global terminal
    if terminal is not None:
        terminal.config(state=tk.NORMAL)
        terminal.insert(tk.END, text + "\n")
        terminal.config(state=tk.DISABLED)
        terminal.yview(tk.END)

def add_keyword_popup():
    popup = tk.Toplevel(root)
    popup.title("Add Keyword")
    popup.geometry("400x450")
    popup.configure(bg=COLORS['background'])
    
    main_frame = tk.Frame(popup, bg=COLORS['surface'],
                         highlightbackground='#e0e0e0',
                         highlightthickness=1)
    main_frame.pack(padx=20, pady=20, fill=tk.BOTH, expand=True)
    
    tk.Label(main_frame, text="Enter Keyword:", bg=COLORS['surface'], fg=COLORS['text']).pack(pady=5)
    keyword_entry = ModernEntry(main_frame)
    keyword_entry.pack(pady=5)
    
    tk.Label(main_frame, text="Enter Telegram Chat ID:", bg=COLORS['surface'], fg=COLORS['text']).pack(pady=5)
    chat_id_entry = ModernEntry(main_frame)
    chat_id_entry.pack(pady=5)
    
    tk.Label(main_frame, text="Enter Message:", bg=COLORS['surface'], fg=COLORS['text']).pack(pady=5)
    message_entry = ModernEntry(main_frame)
    message_entry.pack(pady=5)
    
    def save_keyword():
        keyword = keyword_entry.get().strip().lower()
        chat_id = chat_id_entry.get().strip().replace('\n', '').replace('\r', '')
        message = message_entry.get().strip().replace('\n', ' ').replace('\r', ' ')
        
        if not chat_id.lstrip('-').isdigit():
            messagebox.showerror("Error", "Chat ID must be a number")
            return
            
        if keyword and chat_id and message and keyword not in keywords:
            keywords.append(keyword)
            keyword_data[keyword] = {"chat_id": chat_id, "message": message}
            index = len(keywords)
            keyword_list.insert(tk.END, f"{index}. {keyword} - {chat_id} - {message}")
            save_config(keywords=keywords, keyword_data=keyword_data)
            popup.destroy()
        else:
            if keyword in keywords:
                messagebox.showerror("Error", "This keyword already exists")
            else:
                messagebox.showerror("Error", "All fields are required")
    
    ModernButton(main_frame, text="Save", background=COLORS['primary'], foreground='white', command=save_keyword).pack(pady=10)

def edit_keyword_popup(selected_keyword):
    if not selected_keyword:
        return
        
    keyword = selected_keyword.split(" - ")[0].split(". ")[1]
    if keyword not in keyword_data:
        return
        
    popup = tk.Toplevel(root)
    popup.title("Edit Keyword")
    popup.geometry("400x450")
    popup.configure(bg=COLORS['background'])
    
    main_frame = tk.Frame(popup, bg=COLORS['surface'],
                         highlightbackground='#e0e0e0',
                         highlightthickness=1)
    main_frame.pack(padx=20, pady=20, fill=tk.BOTH, expand=True)
    
    data = keyword_data[keyword]
    
    tk.Label(main_frame, text="Edit Keyword:", bg=COLORS['surface'], fg=COLORS['text']).pack(pady=5)
    keyword_entry = ModernEntry(main_frame)
    keyword_entry.insert(0, keyword)
    keyword_entry.pack(pady=5)
    
    tk.Label(main_frame, text="Edit Telegram Chat ID:", bg=COLORS['surface'], fg=COLORS['text']).pack(pady=5)
    chat_id_entry = ModernEntry(main_frame)
    chat_id_entry.insert(0, data["chat_id"])
    chat_id_entry.pack(pady=5)
    
    tk.Label(main_frame, text="Edit Message:", bg=COLORS['surface'], fg=COLORS['text']).pack(pady=5)
    message_entry = ModernEntry(main_frame)
    message_entry.insert(0, data["message"])
    message_entry.pack(pady=5)
    
    def save_edited_keyword():
        new_keyword = keyword_entry.get().strip().lower()
        chat_id = chat_id_entry.get().strip().replace('\n', '').replace('\r', '')
        message = message_entry.get().strip().replace('\n', ' ').replace('\r', ' ')
        
        if not chat_id.lstrip('-').isdigit():
            messagebox.showerror("Error", "Chat ID must be a number")
            return
            
        if new_keyword and chat_id and message:
            # Update or create new keyword
            if new_keyword != keyword:
                if new_keyword in keywords:
                    messagebox.showerror("Error", "This keyword already exists")
                    return
                keywords.remove(keyword)
                keywords.append(new_keyword)
                del keyword_data[keyword]
            
            keyword_data[new_keyword] = {"chat_id": chat_id, "message": message}
            
            # Refresh keyword list
            keyword_list.delete(0, tk.END)
            for i, kw in enumerate(keywords, 1):
                data = keyword_data[kw]
                keyword_list.insert(tk.END, f"{i}. {kw} - {data['chat_id']} - {data['message']}")
            
            save_config(keywords=keywords, keyword_data=keyword_data)
            popup.destroy()
        else:
            messagebox.showerror("Error", "All fields are required")
    
    ModernButton(main_frame, text="Save", background=COLORS['primary'], foreground='white', command=save_edited_keyword).pack(pady=10)

def process_speech_queue():
    while not speech_queue.empty():
        text = speech_queue.get()
        update_terminal(text)
        for keyword in keywords:
            if keyword in text.lower():
                update_terminal(f"Keyword detected: {keyword}")
                if telegram_bot:
                    data = keyword_data[keyword]
                    if telegram_bot.send_message(data["chat_id"], data["message"]):
                        update_terminal(f"Telegram message sent for keyword: {keyword}")
                    else:
                        update_terminal(f"Failed to send Telegram message for: {keyword}")
    root.after(100, process_speech_queue)

def start_speech_recognition():
    global telegram_bot, saved_token
    # Initialize telegram bot if not already initialized
    if not telegram_bot and saved_token:
        try:
            telegram_bot = TelegramBot(saved_token.strip())
            update_terminal("Telegram bot initialized")
        except Exception as e:
            update_terminal(f"Failed to initialize Telegram bot: {str(e)}")

    speech_thread = threading.Thread(target=speech_module.recognize_speech, args=(speech_queue,), daemon=True)
    speech_thread.start()
    speech_queue.put("Speech recognition started.")

def stop_speech_recognition():
    speech_queue.put("Speech recognition stopped.")

class LoginWindow:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("AVAACS Login")
        self.window.geometry("400x500")
        self.window.configure(bg=COLORS['background'])
        self.user_auth = UserAuth()
        self.logged_in_user = None

        # Center content
        main_frame = tk.Frame(self.window, bg=COLORS['background'])
        main_frame.place(relx=0.5, rely=0.5, anchor="center")

        # Logo and title
        tk.Label(main_frame, text="AVAACS", 
                font=("Segoe UI", 32, "bold"),
                bg=COLORS['background'], 
                fg=COLORS['primary']).pack(pady=(0, 5))
        
        tk.Label(main_frame, text="Login to continue",
                font=("Segoe UI", 12),
                bg=COLORS['background'], 
                fg=COLORS['text_secondary']).pack(pady=(0, 20))

        # Login form with shadow effect
        form_frame = tk.Frame(main_frame, bg=COLORS['surface'],
                            highlightbackground='#e0e0e0',
                            highlightthickness=1)
        form_frame.pack(padx=30, pady=30)

        tk.Label(form_frame, text="Username",
                font=("Segoe UI", 10),
                bg=COLORS['surface'],
                fg=COLORS['text']).pack(anchor="w", pady=(15, 5))
        self.username = ModernEntry(form_frame, width=30)
        self.username.pack(pady=(0, 15))

        tk.Label(form_frame, text="Password",
                font=("Segoe UI", 10),
                bg=COLORS['surface'],
                fg=COLORS['text']).pack(anchor="w", pady=(0, 5))
        self.password = ModernEntry(form_frame, show="•", width=30)
        self.password.pack(pady=(0, 20))

        login_btn = ModernButton(form_frame, text="Login",
                               background=COLORS['primary'],
                               foreground='white',
                               width=25,
                               command=self.login)
        login_btn.pack(pady=(0, 15))

        self.window.bind('<Return>', lambda e: self.login())
        
    def login(self):
        user = self.user_auth.authenticate(self.username.get(), self.password.get())
        if user:
            self.logged_in_user = user
            self.window.destroy()
            self.start_main_app()
        else:
            messagebox.showerror("Error", "Invalid credentials")

    def start_main_app(self):
        global root
        root = tk.Tk()
        setup_main_window(self.logged_in_user)

def logout():
    global root
    root.destroy()
    login = LoginWindow()
    login.window.mainloop()

def open_github():
    import webbrowser
    webbrowser.open('https://github.com/hammond022/pyvoice')

def show_about_dialog():
    about = tk.Toplevel(root)
    about.title("About AVAACS")
    about.geometry("600x400")
    about.configure(bg=COLORS['background'])
    about.resizable(False, False)
    
    main_frame = tk.Frame(about, bg=COLORS['surface'],
                         highlightbackground='#e0e0e0',
                         highlightthickness=1)
    main_frame.pack(padx=20, pady=20, fill=tk.BOTH, expand=True)

    # Title
    tk.Label(main_frame, text="AVAACS",
            font=("Segoe UI", 24, "bold"),
            bg=COLORS['surface'],
            fg=COLORS['primary']).pack(pady=(15, 5))
            
    tk.Label(main_frame, text="Version 1.0.0",
            font=("Segoe UI", 10),
            bg=COLORS['surface'],
            fg=COLORS['text_secondary']).pack()
            
    # Description
    description = """
    Advanced Voice-Activated Alert and Communication System
    
    AVAACS is a tool that listens for specific keywords
    and triggers Telegram notifications when they are detected.
    """
    
    tk.Label(main_frame, text=description,
            font=("Segoe UI", 10),
            bg=COLORS['surface'],
            fg=COLORS['text'],
            justify=tk.CENTER).pack(pady=(20, 10))
    
    # GitHub link
    link_label = tk.Label(main_frame, 
                         text="View on GitHub",
                         font=("Segoe UI", 10, "underline"),
                         bg=COLORS['surface'],
                         fg=COLORS['primary'],
                         cursor="hand2")
    link_label.pack(pady=(0, 20))
    link_label.bind("<Button-1>", lambda e: open_github())
    
    # Copyright
    tk.Label(main_frame, text="Our Lady of Fatima University, 2025",
            font=("Segoe UI", 9),
            bg=COLORS['surface'],
            fg=COLORS['text_secondary']).pack()


def setup_main_window(user):
    global root, terminal, keyword_list, telegram_bot, saved_token
    root.title("AVAACS - Keyword Speech Detector")
    root.geometry("800x600")
    root.configure(bg=COLORS['background'])

    main_container = tk.Frame(root, bg=COLORS['background'])
    main_container.pack(padx=20, pady=20, fill=tk.BOTH, expand=True)

    # Header with gradient effect
    header_frame = tk.Frame(main_container, bg=COLORS['background'])
    header_frame.pack(fill=tk.X, pady=(0, 20))
    
    # Add about button to the right side of header
    about_btn = ModernButton(header_frame, text="i",
                         background=COLORS['surface'],
                         foreground=COLORS['primary'],
                         font=('Segoe UI', 12, 'bold'),
                         pady=4,
                         padx=12,
                         command=show_about_dialog)
    about_btn.pack(side=tk.RIGHT, pady=(5, 0))
    
    tk.Label(header_frame, text="AVAACS",
            font=("Segoe UI", 32, "bold"),
            bg=COLORS['background'],
            fg=COLORS['primary']).pack(pady=(0, 5))
            
    tk.Label(header_frame,
            text="Advanced Voice-Activated Alert and Communication System",
            font=("Segoe UI", 12),
            bg=COLORS['background'],
            fg=COLORS['text_secondary']).pack()

    # Modern button toolbar
    button_frame = tk.Frame(main_container, bg=COLORS['background'])
    button_frame.pack(fill=tk.X, pady=(0, 20))

    if user.is_admin:
        ModernButton(button_frame, text="Setup Telegram",
                    background=COLORS['primary'],
                    foreground='white',
                    command=initialize_telegram).pack(side=tk.LEFT, padx=5)

        ModernButton(button_frame, text="Add Keyword",
                    background=COLORS['primary'],
                    foreground='white',
                    command=add_keyword_popup).pack(side=tk.LEFT, padx=5)

    ModernButton(button_frame, text="Start Recognition",
                background=COLORS['success'],
                foreground='white',
                command=start_speech_recognition).pack(side=tk.LEFT, padx=5)

    ModernButton(button_frame, text="Stop Recognition",
                background=COLORS['error'],
                foreground='white',
                command=stop_speech_recognition).pack(side=tk.LEFT, padx=5)

    ModernButton(button_frame, text="Logout",
                background=COLORS['text_secondary'],
                foreground='white',
                command=logout).pack(side=tk.RIGHT, padx=5)

    # Keywords section
    keywords_frame = tk.LabelFrame(main_container, text="Keywords",
                                 bg=COLORS['surface'],
                                 fg=COLORS['primary'],
                                 font=("Segoe UI", 11, "bold"))
    keywords_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))

    # Custom listbox styling
    keyword_list = tk.Listbox(keywords_frame,
                             bg=COLORS['surface'],
                             fg=COLORS['text'],
                             font=("Segoe UI", 10),
                             selectmode=tk.SINGLE,
                             activestyle='none',
                             highlightthickness=1,
                             highlightbackground='#e0e0e0',
                             selectbackground='#e8f0fe',
                             selectforeground=COLORS['primary'])
    keyword_list.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

    if user.is_admin:
        keyword_list.bind('<Double-Button-1>', lambda e: edit_keyword_popup(keyword_list.get(keyword_list.curselection())))

    # Load saved keywords into list
    for i, kw in enumerate(keywords, 1):
        data = keyword_data[kw]
        keyword_list.insert(tk.END, f"{i}. {kw} - {data['chat_id']} - {data['message']}")
    
    # Initialize telegram bot if token exists
    if saved_token and user.is_admin:
        # Clean any saved token before using
        saved_token = saved_token.strip().replace('\n', '').replace('\r', '')
        try:
            telegram_bot = TelegramBot(saved_token)
            update_terminal("Telegram bot initialized from saved token")
        except Exception as e:
            update_terminal(f"Failed to initialize saved bot: {str(e)}")
            saved_token = None
            telegram_bot = None

    # Terminal section
    terminal_frame = tk.LabelFrame(main_container, text="Terminal",
                                 bg=COLORS['surface'],
                                 fg=COLORS['primary'],
                                 font=("Segoe UI", 11, "bold"))
    terminal_frame.pack(fill=tk.BOTH, expand=True)

    terminal = scrolledtext.ScrolledText(terminal_frame,
                                       height=8,
                                       bg=COLORS['surface'],
                                       fg=COLORS['text'],
                                       font=("Consolas", 10),
                                       padx=10,
                                       pady=10,
                                       wrap=tk.WORD)
    terminal.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
    terminal.config(state=tk.DISABLED)

    root.after(100, process_speech_queue)
    root.mainloop()

if __name__ == "__main__":
    login = LoginWindow()
    login.window.mainloop()