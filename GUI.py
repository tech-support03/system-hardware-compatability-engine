import tkinter as tk
from tkinter import scrolledtext

def get_resolution():
    root = tk.Tk()
    root.withdraw()
    width = root.winfo_screenwidth()
    height = root.winfo_screenheight()
    return f"{width}x{height}"

def run_check(event=None):
    game = game_entry.get()
    if game.strip() == "":
        output_box.insert(tk.END, "Please enter a game name.\n\n")
        return
#add all the ai stuff actual back end
    output_box.insert(tk.END, f"Checking compatibility for: {game}\n")
    output_box.insert(tk.END, "Fetching game data...\n")
    output_box.insert(tk.END, "Comparing with system specs...\n")
    output_box.insert(tk.END, "Done. Results will appear here.\n\n")


def show_specs():
#idk add the psutil stuff
    cpu=0
    ram=0
    gpu=0
    resolution=get_resolution()
    os_info=0
    storage=0
    output_box.insert(tk.END, "---SYSTEM SPECS---\n")
    output_box.insert(tk.END, f"CPU: {cpu}\n")
    output_box.insert(tk.END, f"RAM: {ram} GB\n")
    output_box.insert(tk.END, f"GPU: {gpu}\n")
    output_box.insert(tk.END, f"Resolution: {resolution}\n")
    output_box.insert(tk.END, f"OS: {os_info}\n")
    output_box.insert(tk.END, f"Storage: {storage} GB\n\n")

def main():
    window = tk.Tk()
    window.title("System Hardware Compatibilty Checker")
    window.geometry("900x600")

    window.configure(bg="black")

    title = tk.Label(window, text="System Hardware Compatibilty Checker",
                     font=("Arial", 18), fg="white", bg="black")
    title.pack(pady=10)

    input_frame = tk.Frame(window, bg="black")
    input_frame.pack(pady=10)

    game_label = tk.Label(input_frame, text="Enter Game Name:", fg="white", bg="black")
    game_label.grid(row=0, column=0, padx=5)

    global game_entry
    game_entry = tk.Entry(input_frame, width=40)
    game_entry.grid(row=0, column=1, padx=5)
    game_entry.focus_set()

    window.bind("<Return>", run_check)

    press_label = tk.Label(window, text="Press Enter to check compatibility",
                           fg="white", bg="black")
    press_label.pack(pady=10)

    specs_btn = tk.Button(window, text="Show System Specs", command=show_specs)
    specs_btn.pack(pady=5)

    global output_box
    output_box = scrolledtext.ScrolledText(window, width=100, height=20,
                                           bg="black", fg="white",
                                           insertbackground="white")
    output_box.pack(pady=10)

    window.mainloop()

game_entry = None
output_box = None

main()
