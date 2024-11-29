import tkinter as tk
from tkinter import filedialog, messagebox
import random

# Motywy
themes = {
    "dark": {
        "bg": "#2e3440",
        "text": "#d8dee9",
        "button": "#81a1c1",
        "hover": "#5e81ac",
        "textbox_bg": "#3b4252",
        "textbox_text": "#eceff4",
    },
    "light": {
        "bg": "#eceff4",
        "text": "#2e3440",
        "button": "#88c0d0",
        "hover": "#81a1c1",
        "textbox_bg": "#ffffff",
        "textbox_text": "#2e3440",
    },
}

current_theme = "dark"  # Domyślny motyw


def apply_theme():
    theme = themes[current_theme]
    root.configure(bg=theme["bg"])
    text_box.configure(
        bg=theme["textbox_bg"], fg=theme["textbox_text"], insertbackground=theme["textbox_text"]
    )
    for button in buttons:
        button.config(
            bg=theme["button"],
            fg=theme["text"],
            activebackground=theme["hover"],
            activeforeground=theme["text"],
            bd=0,
            font=("Helvetica", 11),
        )


def toggle_theme():
    global current_theme
    current_theme = "light" if current_theme == "dark" else "dark"
    apply_theme()


# Funkcje aplikacji
def load_file():
    global code
    file_path = filedialog.askopenfilename(filetypes=[("Python files", "*.py")])
    if file_path:
        with open(file_path, "r", encoding="utf-8") as f:
            code = f.readlines()
        text_box.delete(1.0, tk.END)
        text_box.insert(tk.END, "".join(code))


def save_file():
    file_path = filedialog.asksaveasfilename(defaultextension=".py", filetypes=[("Python files", "*.py")])
    if file_path:
        with open(file_path, "w", encoding="utf-8") as f:
            f.writelines(text_box.get(1.0, tk.END).splitlines(keepends=True))


def introduce_indentation_errors():
    global code
    code = text_box.get(1.0, tk.END).splitlines(keepends=True)  # Pobieramy aktualny tekst
    if not code:
        messagebox.showerror("Błąd", "Najpierw wczytaj kod lub wpisz coś w polu tekstowym!")
        return

    # Randomowa liczba linii do popsucia
    lines_to_break = random.randint(2, len(code))

    # Randomowe wcięcia na podanej liczbie linii
    for i in range(lines_to_break):
        random_spaces = " " * random.randint(1, 5)  # Losowa liczba spacji (1-5)
        code[i] = random_spaces + code[i].lstrip()
    text_box.delete(1.0, tk.END)
    text_box.insert(tk.END, "".join(code))


def copy_to_clipboard():
    root.clipboard_clear()
    root.clipboard_append(text_box.get(1.0, tk.END))
    root.update()


def introduce_string_errors():
    global code
    code = text_box.get(1.0, tk.END).splitlines(keepends=True)  # Pobieramy aktualny tekst
    if not code:
        messagebox.showerror("Błąd", "Najpierw wczytaj kod lub wpisz coś w polu tekstowym!")
        return

    broken_code = []
    for line in code:
        if '"' in line:
            broken_code.append(line.replace('"', "'"))
        elif "'" in line:
            broken_code.append(line.replace("'", '"'))
        else:
            broken_code.append(line)
    text_box.delete(1.0, tk.END)
    text_box.insert(tk.END, "".join(broken_code))


def introduce_bracket_errors():
    global code
    code = text_box.get(1.0, tk.END).splitlines(keepends=True)  # Pobieramy aktualny tekst
    if not code:
        messagebox.showerror("Błąd", "Najpierw wczytaj kod lub wpisz coś w polu tekstowym!")
        return

    broken_code = []
    for line in code:
        line = line.replace("(", "[").replace(")", "]")
        broken_code.append(line)
    text_box.delete(1.0, tk.END)
    text_box.insert(tk.END, "".join(broken_code))


# GUI
root = tk.Tk()
root.title("Zepsuty Kod Maker PRO 9000")
root.geometry("900x600")

# Główne okno tekstowe
text_box = tk.Text(root, wrap=tk.WORD, font=("Courier", 12), height=20, width=80)
text_box.pack(pady=(10, 20), padx=10)

# Kontrolki
controls_frame = tk.Frame(root)
controls_frame.pack(pady=10)

buttons = []

load_button = tk.Button(controls_frame, text="Wczytaj plik", command=load_file)
load_button.grid(row=0, column=0, padx=5)
buttons.append(load_button)

chaos_button = tk.Button(controls_frame, text="Dodaj losowe wcięcia", command=introduce_indentation_errors)
chaos_button.grid(row=0, column=1, padx=5)
buttons.append(chaos_button)

string_button = tk.Button(controls_frame, text="Zepsuj cudzysłowy", command=introduce_string_errors)
string_button.grid(row=0, column=2, padx=5)
buttons.append(string_button)

bracket_button = tk.Button(controls_frame, text="Zamień nawiasy", command=introduce_bracket_errors)
bracket_button.grid(row=0, column=3, padx=5)
buttons.append(bracket_button)

copy_button = tk.Button(controls_frame, text="Kopiuj kod", command=copy_to_clipboard)
copy_button.grid(row=0, column=4, padx=5)
buttons.append(copy_button)

save_button = tk.Button(controls_frame, text="Zapisz plik", command=save_file)
save_button.grid(row=0, column=5, padx=5)
buttons.append(save_button)

theme_button = tk.Button(controls_frame, text="Zmień motyw", command=toggle_theme)
theme_button.grid(row=0, column=6, padx=5)
buttons.append(theme_button)

# Aplikuj motyw
apply_theme()

root.mainloop()
