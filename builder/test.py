import tkinter as tk
import asyncio
import sqlite3

root = tk.Tk()
root.title("Hello World")
root.geometry("200x200")

try:
    root.mainloop()
except KeyboardInterrupt:
    root.destroy()
