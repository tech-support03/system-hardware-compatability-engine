import tkinter as tk
from tkinter import scrolledtext

def run_check():
    game = game_entry.get()
    if game.strip() == "":
        output_box.insert(tk.END, "Please enter a game name.\n\n")
        return

    output_box.insert(tk.END, f"Checking compatibility for: {game}\n")
    output_box.insert(tk.END, "Fetching game data...\n")
    output_box.insert(tk.END, "Comparing with system specs...\n")
    output_box.insert(tk.END, "Done. Results will appear here.\n\n")

def main():
    window = tk.Tk()
    window.title("System Hardware Compatibilty Checker")
    window.geometry("900x600")

    window.configure(bg="black")

    title = tk.Label(window, text="System Hardware Compatibilty Checker", font=("Arial", 18), fg="white", bg="black")
    title.pack(pady=10)

    input_frame = tk.Frame(window, bg="black")
    input_frame.pack(pady=10)

    game_label = tk.Label(input_frame, text="Enter Game Name:", fg="white", bg="black")
    game_label.grid(row=0, column=0, padx=5)

    global game_entry
    game_entry = tk.Entry(input_frame, width=40)
    game_entry.grid(row=0, column=1, padx=5)

    check_btn = tk.Button(window, text="Check Compatibility", command=run_check)
    check_btn.pack(pady=10)

    global output_box
    output_box = scrolledtext.ScrolledText(window, width=100, height=20, bg="black", fg="white", insertbackground="white")
    output_box.pack(pady=10)

    window.mainloop()

game_entry = None
output_box = None

main()
