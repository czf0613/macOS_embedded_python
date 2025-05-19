import tkinter as tk

root = tk.Tk()
root.title("Hello World")
root.geometry("200x200")

try:
    print("tkinter已启动")
    root.mainloop()
except KeyboardInterrupt:
    print("KeyboardInterrupt")
    root.destroy()
