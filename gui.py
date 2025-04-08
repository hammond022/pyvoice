import tkinter as tk
from tkinter import scrolledtext, simpledialog, messagebox
import threading
import queue
import speech_module
from telegram_module import TelegramBot

speech_queue = queue.Queue()
keywords = []
keyword_data = {}
telegram_bot = None

def initialize_telegram():
    global telegram_bot
    try:
        token = simpledialog.askstring("Telegram Bot", "Enter your Telegram bot token:")
        if token:
            telegram_bot = TelegramBot(token)
            update_terminal("Telegram bot initialized")
        else:
            update_terminal("Telegram bot initialization cancelled")
    except Exception as e:
        messagebox.showerror("Error", f"Failed to initialize Telegram bot: {str(e)}")
        update_terminal(f"Telegram bot initialization failed: {str(e)}")
        telegram_bot = None

def update_terminal(text):
    terminal.config(state=tk.NORMAL)
    terminal.insert(tk.END, text + "\n")
    terminal.config(state=tk.DISABLED)
    terminal.yview(tk.END)

def add_keyword_popup():
    popup = tk.Toplevel(root)
    popup.title("Add Keyword")
    popup.geometry("300x300")
    
    tk.Label(popup, text="Enter Keyword:").pack(pady=5)
    keyword_entry = tk.Entry(popup)
    keyword_entry.pack(pady=5)
    
    tk.Label(popup, text="Enter Telegram Chat ID:").pack(pady=5)
    chat_id_entry = tk.Entry(popup)
    chat_id_entry.pack(pady=5)
    
    tk.Label(popup, text="Enter Message:").pack(pady=5)
    message_entry = tk.Entry(popup)
    message_entry.pack(pady=5)
    
    def save_keyword():
        keyword = keyword_entry.get().strip().lower()
        chat_id = chat_id_entry.get().strip()
        message = message_entry.get().strip()
        if keyword and chat_id and message and keyword not in keywords:
            keywords.append(keyword)
            keyword_data[keyword] = {"chat_id": chat_id, "message": message}
            index = len(keywords)
            keyword_list.insert(tk.END, f"{index}. {keyword} - {chat_id} - {message}")
        popup.destroy()
    
    tk.Button(popup, text="Save", command=save_keyword).pack(pady=10)

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
    speech_thread = threading.Thread(target=speech_module.recognize_speech, args=(speech_queue,), daemon=True)
    speech_thread.start()
    speech_queue.put("Speech recognition started.")

def stop_speech_recognition():
    speech_queue.put("Speech recognition stopped.")

root = tk.Tk()
root.title("Keyword Speech Detector")
root.geometry("500x400")

tk.Label(root, text="LOGO", font=("Arial", 20)).pack(pady=5)

button_frame = tk.Frame(root)
button_frame.pack(pady=5)

telegram_button = tk.Button(button_frame, text="Setup Telegram", bg="white", fg="black", command=initialize_telegram)
telegram_button.pack(side=tk.LEFT, padx=5)

add_button = tk.Button(button_frame, text="Add keyword", bg="white", fg="black", command=add_keyword_popup)
add_button.pack(side=tk.LEFT, padx=5)

start_button = tk.Button(button_frame, text="Start", bg="white", fg="black", command=start_speech_recognition)
start_button.pack(side=tk.LEFT, padx=5)

stop_button = tk.Button(button_frame, text="Stop", bg="white", fg="black", command=stop_speech_recognition)
stop_button.pack(side=tk.LEFT, padx=5)

tk.Label(root, text="Added keywords:").pack(pady=5)
keyword_list = tk.Listbox(root, height=5, bg="white", fg="black")
keyword_list.pack(pady=5, fill=tk.BOTH, expand=True)

tk.Label(root, text="Terminal").pack(pady=5)
terminal = scrolledtext.ScrolledText(root, height=10, state=tk.DISABLED, bg="white", fg="black")
terminal.pack(pady=5, fill=tk.BOTH, expand=True)

root.after(100, process_speech_queue)
root.mainloop()