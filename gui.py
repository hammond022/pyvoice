import tkinter as tk
from tkinter import scrolledtext, simpledialog, messagebox, ttk
import threading
import queue
import speech_module
from telegram_module import TelegramBot
from users import UserAuth
from config import save_config, load_config
import logging

speech_queue = queue.Queue()
telegram_bot = None
root = None
terminal = None
keyword_list = None
terminal_logging_enabled = True

recognition_thread = None
recognition_stop_event = None

saved_token, keywords, keyword_data = load_config()


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
        self._original_color = kwargs.get('background') or self.cget('background')
        self._is_hovering = False
        self.bind('<Enter>', self.on_enter)
        self.bind('<Leave>', self.on_leave)
        
    def on_enter(self, e):
        if self['state'] != 'disabled' and not self._is_hovering:
            self._is_hovering = True
            super().configure(background=self.darken_color(self._original_color))
            
    def on_leave(self, e):
        if self['state'] != 'disabled':
            self._is_hovering = False
            super().configure(background=self._original_color)
            
    def configure(self, cnf=None, **kwargs):
        if not self._is_hovering:
            if 'background' in (cnf or {}) or 'background' in kwargs:
                self._original_color = kwargs.get('background') or cnf.get('background')
        super().configure(cnf or {}, **kwargs)
        
    config = configure

    @staticmethod
    def darken_color(hex_color):
        """Darken a hex color by 20%"""
      
        hex_color = hex_color.lstrip('#')
        
      
        rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        
      
        darkened = tuple(max(0, int(x * 0.8)) for x in rgb)
        
       
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

    # Center all widgets in main_frame
    main_frame.grid_rowconfigure((0,1,2,3,4,5,6,7,8), weight=1)
    main_frame.grid_columnconfigure(0, weight=1)

    data = keyword_data[keyword]

    # Centered label and entry for keyword
    tk.Label(main_frame, text="Edit Keyword:", bg=COLORS['surface'], fg=COLORS['text'], anchor="center", justify="center").grid(row=0, column=0, pady=(20,5), sticky="ew")
    keyword_entry = ModernEntry(main_frame, justify="center")
    keyword_entry.insert(0, keyword)
    keyword_entry.grid(row=1, column=0, pady=(0,15), padx=40, sticky="ew")

    # Centered label and entry for chat id
    tk.Label(main_frame, text="Edit Telegram Chat ID:", bg=COLORS['surface'], fg=COLORS['text'], anchor="center", justify="center").grid(row=2, column=0, pady=5, sticky="ew")
    chat_id_entry = ModernEntry(main_frame, justify="center")
    chat_id_entry.insert(0, data["chat_id"])
    chat_id_entry.grid(row=3, column=0, pady=(0,15), padx=40, sticky="ew")

    # Centered label and entry for message
    tk.Label(main_frame, text="Edit Message:", bg=COLORS['surface'], fg=COLORS['text'], anchor="center", justify="center").grid(row=4, column=0, pady=5, sticky="ew")
    message_entry = ModernEntry(main_frame, justify="center")
    message_entry.insert(0, data["message"])
    message_entry.grid(row=5, column=0, pady=(0,15), padx=40, sticky="ew")

    def save_edited_keyword():
        new_keyword = keyword_entry.get().strip().lower()
        chat_id = chat_id_entry.get().strip().replace('\n', '').replace('\r', '')
        message = message_entry.get().strip().replace('\n', ' ').replace('\r', ' ')
        
        if not chat_id.lstrip('-').isdigit():
            messagebox.showerror("Error", "Chat ID must be a number")
            return
            
        if new_keyword and chat_id and message:
   
            if new_keyword != keyword:
                if new_keyword in keywords:
                    messagebox.showerror("Error", "This keyword already exists")
                    return
                keywords.remove(keyword)
                keywords.append(new_keyword)
                del keyword_data[keyword]
            
            keyword_data[new_keyword] = {"chat_id": chat_id, "message": message}
            
       
            keyword_list.delete(0, tk.END)
            for i, kw in enumerate(keywords, 1):
                data = keyword_data[kw]
                keyword_list.insert(tk.END, f"{i}. {kw} - {data['chat_id']} - {data['message']}")
            
            save_config(keywords=keywords, keyword_data=keyword_data)
            popup.destroy()
        else:
            messagebox.showerror("Error", "All fields are required")
    
    def remove_keyword():
        if messagebox.askyesno("Confirm Delete", f"Are you sure you want to delete the keyword '{keyword}'?"):
            keywords.remove(keyword)
            del keyword_data[keyword]
            
       
            keyword_list.delete(0, tk.END)
            for i, kw in enumerate(keywords, 1):
                data = keyword_data[kw]
                keyword_list.insert(tk.END, f"{i}. {kw} - {data['chat_id']} - {data['message']}")
            
            save_config(keywords=keywords, keyword_data=keyword_data)
            update_terminal(f"Keyword '{keyword}' removed")
            popup.destroy()


    button_frame = tk.Frame(main_frame, bg=COLORS['surface'])
    button_frame.grid(row=6, column=0, pady=20, sticky="ew")
    button_frame.grid_columnconfigure((0,1), weight=1)

    ModernButton(button_frame, text="Save", 
                background=COLORS['primary'], 
                foreground='white',
                command=save_edited_keyword).grid(row=0, column=0, padx=10, sticky="ew")
                
    ModernButton(button_frame, text="Remove",
                background=COLORS['error'],
                foreground='white',
                command=remove_keyword).grid(row=0, column=1, padx=10, sticky="ew")

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
    global telegram_bot, saved_token, recognition_thread, recognition_stop_event
    if recognition_thread and recognition_thread.is_alive():
        update_terminal("Speech recognition is already running.")
        return

    if not telegram_bot and saved_token:
        try:
            telegram_bot = TelegramBot(saved_token.strip())
            update_terminal("Telegram bot initialized")
        except Exception as e:
            update_terminal(f"Failed to initialize Telegram bot: {str(e)}")

    recognition_stop_event = threading.Event()
    recognition_thread = threading.Thread(
        target=speech_module.recognize_speech,
        args=(speech_queue, recognition_stop_event),
        daemon=True
    )
    recognition_thread.start()
    speech_queue.put("Speech recognition started.")

def stop_speech_recognition():
    global recognition_stop_event, recognition_thread
    if recognition_stop_event and recognition_thread and recognition_thread.is_alive():
        recognition_stop_event.set()
        recognition_thread.join(timeout=2)
        speech_queue.put("Speech recognition stopped.")
    else:
        speech_queue.put("Speech recognition is not running.")

class LoginWindow:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("AVAACS Login")
        self.window.geometry("400x500")
        self.window.configure(bg=COLORS['background'])
        self.user_auth = UserAuth()
        self.logged_in_user = None

   
        main_frame = tk.Frame(self.window, bg=COLORS['background'])
        main_frame.place(relx=0.5, rely=0.5, anchor="center")

   
        tk.Label(main_frame, text="AVAACS", 
                font=("Segoe UI", 32, "bold"),
                bg=COLORS['background'], 
                fg=COLORS['primary']).pack(pady=(0, 5))
        
        tk.Label(main_frame, text="Login to continue",
                font=("Segoe UI", 12),
                bg=COLORS['background'], 
                fg=COLORS['text_secondary']).pack(pady=(0, 20))

      
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
    global terminal_logging_enabled
    about = tk.Toplevel(root)
    about.title("About AVAACS")
    about.geometry("600x400")
    about.configure(bg=COLORS['background'])
    about.resizable(False, False)
    
    main_frame = tk.Frame(about, bg=COLORS['surface'],
                         highlightbackground='#e0e0e0',
                         highlightthickness=1)
    main_frame.pack(padx=20, pady=20, fill=tk.BOTH, expand=True)

   
    tk.Label(main_frame, text="AVAACS",
            font=("Segoe UI", 24, "bold"),
            bg=COLORS['surface'],
            fg=COLORS['primary']).pack(pady=(15, 5))
            
    tk.Label(main_frame, text="Version 1.0.0",
            font=("Segoe UI", 10),
            bg=COLORS['surface'],
            fg=COLORS['text_secondary']).pack()
            
   
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
    
  
    link_label = tk.Label(main_frame, 
                         text="View on GitHub",
                         font=("Segoe UI", 10, "underline"),
                         bg=COLORS['surface'],
                         fg=COLORS['primary'],
                         cursor="hand2")
    link_label.pack(pady=(0, 20))
    link_label.bind("<Button-1>", lambda e: open_github())
    
   
    logging_var = tk.BooleanVar(value=terminal_logging_enabled)
    logging_frame = tk.Frame(main_frame, bg=COLORS['surface'])
    logging_frame.pack(pady=(10, 20))
    
    tk.Checkbutton(logging_frame, 
                   text="Enable Verbose Logging",
                   variable=logging_var,
                   bg=COLORS['surface'],
                   fg=COLORS['text'],
                   command=lambda: toggle_terminal_logging(logging_var.get())).pack()

  
    tk.Label(main_frame, text="Our Lady of Fatima University, 2025",
            font=("Segoe UI", 9),
            bg=COLORS['surface'],
            fg=COLORS['text_secondary']).pack()


class TerminalHandler(logging.Handler):
    def __init__(self, terminal_widget):
        super().__init__()
        self.terminal = terminal_widget
        
    def emit(self, record):
        if not terminal_logging_enabled:
            return
        msg = self.format(record)
        def _update():
            self.terminal.config(state=tk.NORMAL)
            self.terminal.insert(tk.END, msg + "\n")
            self.terminal.config(state=tk.DISABLED)
            self.terminal.yview(tk.END)
        if self.terminal:
            self.terminal.after(0, _update)

def toggle_terminal_logging(enabled):
    global terminal_logging_enabled
    terminal_logging_enabled = enabled
    if terminal:
        update_terminal(f"Terminal logging {'enabled' if enabled else 'disabled'}")

def setup_main_window(user):
    global root, terminal, keyword_list, telegram_bot, saved_token
    root.title("AVAACS - Keyword Speech Detector")
    root.geometry("800x600")
    root.configure(bg=COLORS['background'])

    main_container = tk.Frame(root, bg=COLORS['background'])
    main_container.pack(padx=20, pady=20, fill=tk.BOTH, expand=True)


    header_frame = tk.Frame(main_container, bg=COLORS['background'])
    header_frame.pack(fill=tk.X, pady=(0, 20))
    
 
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

    
    keywords_frame = tk.LabelFrame(main_container, text="Keywords",
                                 bg=COLORS['surface'],
                                 fg=COLORS['primary'],
                                 font=("Segoe UI", 11, "bold"))
    keywords_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))


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

  
    for i, kw in enumerate(keywords, 1):
        data = keyword_data[kw]
        keyword_list.insert(tk.END, f"{i}. {kw} - {data['chat_id']} - {data['message']}")
    
    
    if saved_token and user.is_admin:
       
        saved_token = saved_token.strip().replace('\n', '').replace('\r', '')
        try:
            telegram_bot = TelegramBot(saved_token)
            update_terminal("Telegram bot initialized from saved token")
        except Exception as e:
            update_terminal(f"Failed to initialize saved bot: {str(e)}")
            saved_token = None
            telegram_bot = None

  
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

    
    terminal_handler = TerminalHandler(terminal)
    terminal_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logging.getLogger().addHandler(terminal_handler)
    logging.getLogger().setLevel(logging.INFO)

    root.after(100, process_speech_queue)
    root.mainloop()

if __name__ == "__main__":
    login = LoginWindow()
    login.window.mainloop()