import tkinter as tk
from tkinter import scrolledtext, simpledialog
import threading
import queue
import speech_module

speech_queue = queue.Queue()
keywords = []
keyword_data = {}

def update_terminal(text):
    terminal.config(state=tk.NORMAL)
    terminal.insert(tk.END, text + "\n")
    terminal.config(state=tk.DISABLED)
    terminal.yview(tk.END)

def add_keyword_popup():
    popup = tk.Toplevel(root)
    popup.title("Add Keyword")
    popup.geometry("300x250")
    
    tk.Label(popup, text="Enter Keyword:").pack(pady=5)
    keyword_entry = tk.Entry(popup)
    keyword_entry.pack(pady=5)
    
    tk.Label(popup, text="Enter Phone Number:").pack(pady=5)
    phone_entry = tk.Entry(popup)
    phone_entry.pack(pady=5)
    
    tk.Label(popup, text="Enter Message:").pack(pady=5)
    message_entry = tk.Entry(popup)
    message_entry.pack(pady=5)
    
    def save_keyword():
        keyword = keyword_entry.get().strip().lower()
        phone = phone_entry.get().strip()
        message = message_entry.get().strip()
        if keyword and phone and message and keyword not in keywords:
            keywords.append(keyword)
            keyword_data[keyword] = {"phone": phone, "message": message}
            index = len(keywords)
            keyword_list.insert(tk.END, f"{index}. {keyword} - {phone} - {message}")
        popup.destroy()
    
    tk.Button(popup, text="Save", command=save_keyword).pack(pady=10)

def process_speech_queue():
    while not speech_queue.empty():
        text = speech_queue.get()
        update_terminal(text)
        if any(keyword in text for keyword in keywords):
            update_terminal("Keyword detected!")
    root.after(100, process_speech_queue)

def start_speech_recognition():
    speech_thread = threading.Thread(target=speech_module.recognize_speech, args=(speech_queue,), daemon=True)
    speech_thread.start()

def stop_speech_recognition():
    speech_queue.put("Speech recognition stopped.")

root = tk.Tk()
root.title("Keyword Speech Detector")
root.geometry("500x400")

tk.Label(root, text="LOGO", font=("Arial", 20)).pack(pady=5)

button_frame = tk.Frame(root)
button_frame.pack(pady=5)

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