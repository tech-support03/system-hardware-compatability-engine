import tkinter as tk

def get_resolution():
    root = tk.Tk()
    root.withdraw()
    width = root.winfo_screenwidth()
    height = root.winfo_screenheight()
    return f"{width}x{height}"

print(get_resolution())

