import tkinter as tk
from tkinter import messagebox, ttk, filedialog
import requests
from io import BytesIO
from PIL import Image, ImageTk
import os
from datetime import datetime

class TaskManagerApp:

    def __init__(self, root):
        self.root = root
        self.root.title("✨ Menedżer Zadań Edyty ✨")
        self.tasks = []
        self.image_paths = []  # Lista do przechowywania ścieżek do obrazków
        self.load_image_links()  # Wczytanie linków do obrazków przy starcie aplikacji
        self.setup_ui()
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TMenubutton", font=("Arial", 12), background="#ffffff", foreground="#000000", padding=5, relief="flat")
        style.map("TMenubutton", background=[("active", "#d9d9d9")])

    def setup_ui(self):
        """Tworzy interfejs użytkownika z listą zadań i polami wejściowymi."""
        # Główna ramka aplikacji
        frame = tk.Frame(self.root, padx=10, pady=10, bg="#f7f7f9")
        frame.grid(row=0, column=0)

        # === Lista zadań ===
        self.task_list = ttk.Treeview(
            frame,
            columns=("priority", "start", "end", "description", "duration"),  # Dodajemy kolumnę 'duration'
            show="headings",  # Wyświetlamy tylko nagłówki
            height=15
        )
        self.task_list.grid(row=0, column=0, columnspan=4, pady=10)

        # Nagłówki kolumn
        self.task_list.heading("priority", text="Priorytet")
        self.task_list.heading("start", text="Czas startu")
        self.task_list.heading("end", text="Czas końca")
        self.task_list.heading("description", text="Opis")  # Nagłówek kolumny 'Opis'
        self.task_list.heading("duration", text="Czas trwania")
        self.task_list.column("duration", width=100, anchor="center")

        # Ustawienia kolumn
        self.task_list.column("priority", width=100, anchor="center")
        self.task_list.column("start", width=100, anchor="center")
        self.task_list.column("end", width=100, anchor="center")
        self.task_list.column("description", width=200, anchor="w")  # Szersza kolumna, wyrównanie do lewej
        self.task_list.bind("<Double-1>", self.show_task_details)  # Podwójne kliknięcie pokazuje szczegóły

        # === Pola wejściowe ===
        # Nazwa zadania
        tk.Label(frame, text="Nazwa zadania:", font=("Arial", 10), bg="#f7f7f9").grid(row=1, column=0, sticky="w")
        self.task_name_entry = tk.Entry(frame, font=("Arial", 12), bg="#ffffff")
        self.task_name_entry.grid(row=1, column=1, columnspan=3, padx=5, pady=5, sticky="we")

        # Priorytet zadania
        tk.Label(frame, text="Priorytet:", font=("Arial", 10), bg="#f7f7f9").grid(row=2, column=0, sticky="w")
        self.priority_var = tk.StringVar(value="Wybierz priorytet")
        self.priority_menu = ttk.OptionMenu(frame, self.priority_var, "Wybierz priorytet", "Wysoki", "Średni", "Niski")
        self.priority_menu.grid(row=2, column=1, columnspan=3, padx=5, pady=5, sticky="we")

        # Czas startu
        tk.Label(frame, text="Czas startu:", font=("Arial", 10), bg="#f7f7f9").grid(row=3, column=0, sticky="w")
        self.start_hour = tk.StringVar(value="00")
        self.start_minute = tk.StringVar(value="00")
        ttk.OptionMenu(frame, self.start_hour, *[f"{i:02}" for i in range(24)]).grid(row=3, column=1, sticky="w", padx=5)
        ttk.OptionMenu(frame, self.start_minute, *[f"{i:02}" for i in range(0, 60, 5)]).grid(row=3, column=2, sticky="w", padx=5)

        # Czas końca
        tk.Label(frame, text="Czas końca:", font=("Arial", 10), bg="#f7f7f9").grid(row=4, column=0, sticky="w")
        self.end_hour = tk.StringVar(value="00")
        self.end_minute = tk.StringVar(value="00")
        ttk.OptionMenu(frame, self.end_hour, *[f"{i:02}" for i in range(24)]).grid(row=4, column=1, sticky="w", padx=5)
        ttk.OptionMenu(frame, self.end_minute, *[f"{i:02}" for i in range(0, 60, 5)]).grid(row=4, column=2, sticky="w", padx=5)

        # === Przyciski akcji ===
        action_frame = tk.Frame(frame, bg="#f7f7f9")  # Ramka na przyciski
        action_frame.grid(row=5, column=0, columnspan=4, pady=10)

        tk.Button(action_frame, text="➕ Dodaj zadanie", bg="#4caf50", fg="white", font=("Arial", 12), command=self.add_task).grid(row=0, column=0, padx=10)
        tk.Button(action_frame, text="📊 Pokaż statystyki", bg="#2196f3", fg="white", font=("Arial", 12), command=self.show_statistics).grid(row=0, column=1, padx=10)
        tk.Button(action_frame, text="🗑️ Usuń zadanie", bg="#f44336", fg="white", font=("Arial", 12), command=self.remove_task).grid(row=0, column=2, padx=10)

        # Ramka dla sterowania timerem
        timer_frame = tk.Frame(frame, bg="#f7f7f9")
        timer_frame.grid(row=6, column=0, columnspan=4, pady=10)

        tk.Button(timer_frame, text="▶ Start", bg="#4caf50", fg="white", font=("Arial", 12), command=self.start_task).grid(row=0, column=0, padx=10)
        tk.Button(timer_frame, text="⏸ Pauza", bg="#ff9800", fg="white", font=("Arial", 12), command=self.pause_task).grid(row=0, column=1, padx=10)
        tk.Button(timer_frame, text="⏹ Stop", bg="#f44336", fg="white", font=("Arial", 12), command=self.stop_task).grid(row=0, column=2, padx=10)

        # === Galeria obrazków ===
        self.add_gallery()

    def add_task(self):
        """Dodaje zadanie do listy."""
        name = self.task_name_entry.get()
        priority = self.priority_var.get()
        start_time = f"{self.start_hour.get()}:{self.start_minute.get()}"
        end_time = f"{self.end_hour.get()}:{self.end_minute.get()}"

        # Walidacja danych
        if not name or priority not in ["Wysoki", "Średni", "Niski"]:
            messagebox.showwarning("Błąd", "Wprowadź poprawne dane i wybierz priorytet!")
            return

        if not self.validate_time_order(start_time, end_time):
            messagebox.showwarning("Błąd", "Czas końca musi być późniejszy niż czas startu!")
            return

        # Krótki opis
        short_description = name if len(name) <= 20 else name[:17] + "..."  # Skracamy opis do 20 znaków

        # Dodanie zadania do listy
        self.tasks.append({
            "name": name,
            "priority": priority,
            "start": start_time,
            "end": end_time,
            "description": short_description
        })
        self.task_name_entry.delete(0, tk.END)
        self.priority_var.set("Wybierz priorytet")
        self.start_hour.set("00")
        self.start_minute.set("00")
        self.end_hour.set("00")
        self.end_minute.set("00")
        self.refresh_task_list()

    def show_task_details(self, event):
        """Pokazuje szczegóły wybranego zadania."""
        selected_item = self.task_list.focus()  # Pobiera zaznaczone zadanie
        if not selected_item:
            return

        # Pobieramy dane zaznaczonego wiersza
        item_data = self.task_list.item(selected_item, "values")
        if item_data:
            priority, start, end, description = item_data
            messagebox.showinfo(
                "Szczegóły zadania",
                f"Priorytet: {priority}\nCzas startu: {start}\nCzas końca: {end}\nOpis: {description}"
            )

    def remove_task(self):
        """Usuwa wybrane zadanie."""
        selected_index = self.task_listbox.curselection()
        if not selected_index:
            messagebox.showwarning("Błąd", "Wybierz zadanie!")
            return
        del self.tasks[selected_index[0]]
        self.refresh_task_list()

    def refresh_task_list(self):
        """Odświeża listę zadań w GUI."""
        self.task_list.delete(*self.task_list.get_children())  # Czyści listę
        for task in self.tasks:
            self.task_list.insert(
                "",
                "end",
                values=(task["priority"], task["start"], task["end"], task["description"])  # Dodajemy opis
            )

    def show_statistics(self):
        """Wyświetla statystyki zadań."""
        stats = {"Wysoki": 0, "Średni": 0, "Niski": 0}
        for task in self.tasks:
            if task["priority"] in stats:
                stats[task["priority"]] += 1

        if sum(stats.values()) == 0:
            messagebox.showwarning("Brak danych", "Nie ma żadnych zadań do pokazania w statystykach.")
            return

        stats_text = "\n".join([f"{k}: {v}" for k, v in stats.items()])
        messagebox.showinfo("Statystyki", stats_text)

    def add_gallery(self):
        """Dodaje galerię obrazków."""
        gallery_label = tk.Label(
            self.root,
            text="🐱 Galeria Edyty 🐱",
            font=("Arial", 14, "bold"),
            fg="#4caf50",
            bg="#f7f7f9",
            anchor="w"
        )
        gallery_label.grid(row=0, column=2, sticky="ne", padx=10, pady=10)  # Po prawej stronie na górze

        button_frame = tk.Frame(self.root, bg="#f7f7f9")
        button_frame.grid(row=3, column=0, columnspan=3, pady=10)

        tk.Button(
            button_frame,
            text="➕ Dodaj Obrazek",
            bg="#4caf50",
            fg="white",
            font=("Arial", 12),
            command=self.add_image
        ).grid(row=0, column=0, padx=5)

        tk.Button(
            button_frame,
            text="🗑️ Usuń Obrazek",
            bg="#f44336",
            fg="white",
            font=("Arial", 12),
            command=self.remove_image
        ).grid(row=0, column=1, padx=5)

        self.gallery_frame = tk.Frame(self.root, bg="#f7f7f9")
        self.gallery_frame.grid(row=2, column=0, columnspan=3)

        self.refresh_gallery()

    def refresh_gallery(self):
        """Odświeża galerię obrazków."""
        for widget in self.gallery_frame.winfo_children():
            widget.destroy()

        for i, image_path in enumerate(self.image_paths):
            image = self.load_image(image_path)
            if image:
                photo = ImageTk.PhotoImage(image)
                btn = tk.Button(self.gallery_frame, image=photo, command=lambda path=image_path: self.show_image_popup(path))
                btn.image = photo
                btn.grid(row=i // 3, column=i % 3, padx=5, pady=5)

    def load_image(self, image_path):
        """Ładuje obraz i zachowuje proporcje."""
        try:
            if image_path.startswith("http"):
                response = requests.get(image_path)
                response.raise_for_status()
                image = Image.open(BytesIO(response.content))
            else:
                image = Image.open(image_path)
            image.thumbnail((100, 100), Image.Resampling.LANCZOS)
            return image
        except Exception as e:
            print(f"Błąd ładowania obrazka {image_path}: {e}")
            return None

    def load_image_links(self):
        """Wczytuje linki do obrazków z pliku zdjecia.txt."""
        if os.path.exists("zdjecia.txt"):
            with open("zdjecia.txt", "r") as file:
                self.image_paths = [line.strip() for line in file.readlines()]
        else:
            self.image_paths = []

    def add_image(self):
        """Dodaje nowy obrazek."""
        add_window = tk.Toplevel(self.root)
        add_window.title("Dodaj obrazek")
        add_window.geometry("400x200")
        add_window.configure(bg="#f7f7f9")
        add_window.grab_set()

        tk.Label(add_window, text="Dodaj obrazek z URL lub dysku:", font=("Arial", 12), bg="#f7f7f9").pack(pady=10)
        url_entry = tk.Entry(add_window, width=40, font=("Arial", 12))
        url_entry.pack(pady=5)

        def add_from_url():
            image_url = url_entry.get().strip()
            if image_url.startswith("http"):
                self.image_paths.append(image_url)
                with open("zdjecia.txt", "a") as file:
                    file.write(image_url + "\n")
                self.refresh_gallery()
                add_window.destroy()
            else:
                messagebox.showwarning("Błąd", "Podany link jest niepoprawny!")

        def browse_file():
            file_path = filedialog.askopenfilename(filetypes=[("Obrazy", "*.jpg *.jpeg *.png *.webp")])
            if file_path:
                self.image_paths.append(file_path)
                with open("zdjecia.txt", "a") as file:
                    file.write(file_path + "\n")
                self.refresh_gallery()
                add_window.destroy()

        tk.Button(add_window, text="Dodaj URL", bg="#4caf50", fg="white", font=("Arial", 12), command=add_from_url).pack(pady=5)
        tk.Button(add_window, text="Przeglądaj", bg="#2196f3", fg="white", font=("Arial", 12), command=browse_file).pack(pady=5)

    def show_image_popup(self, image_path):
        """Pokazuje pełny obrazek w osobnym oknie, ale w rozmiarze dopasowanym do ekranu."""
        popup = tk.Toplevel(self.root)
        popup.title("Podgląd obrazka")
        popup.configure(bg="#f7f7f9")

        # Pobierz wymiary ekranu
        screen_width = self.root.winfo_screenwidth()
        screen_height = self.root.winfo_screenheight()
        max_width = screen_width - 100  # Zostaw trochę miejsca na ramki
        max_height = screen_height - 100

        try:
            if image_path.startswith("http"):
                # Pobierz obraz z URL
                response = requests.get(image_path)
                response.raise_for_status()
                image = Image.open(BytesIO(response.content))
            else:
                # Wczytaj obraz z dysku
                image = Image.open(image_path)

            # Dopasuj obraz do rozmiaru ekranu
            image.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)

            # Utwórz PhotoImage z dopasowanego obrazu
            photo = ImageTk.PhotoImage(image)
            label = tk.Label(popup, image=photo, bg="#f7f7f9")
            label.image = photo  # Zachowaj referencję do obrazu
            label.pack(padx=10, pady=10)

        except Exception as e:
            print(f"Błąd ładowania obrazka: {e}")
            tk.Label(popup, text="Nie udało się załadować obrazka.", bg="#f7f7f9", font=("Arial", 12)).pack(pady=20)

    def remove_image(self):
        """Usuwa wybrane zdjęcia z galerii."""
        if not self.image_paths:
            messagebox.showwarning("Błąd", "Brak obrazków do usunięcia!")
            return

        remove_window = tk.Toplevel(self.root)
        remove_window.title("Usuń Obrazek")
        remove_window.geometry("600x400")
        remove_window.configure(bg="#f7f7f9")
        remove_window.grab_set()

        tk.Label(remove_window, text="Zaznacz obrazki do usunięcia:", font=("Arial", 14), bg="#f7f7f9").pack(pady=10)
        gallery_frame = tk.Frame(remove_window, bg="#f7f7f9")
        gallery_frame.pack()

        selected_images = []
        for i, image_path in enumerate(self.image_paths):
            image = self.load_image(image_path)
            if image:
                photo = ImageTk.PhotoImage(image)
                frame = tk.Frame(gallery_frame, bg="#f7f7f9", padx=5, pady=5)
                frame.grid(row=i // 3, column=i % 3)

                label = tk.Label(frame, image=photo, bg="#ffffff", relief="solid", bd=1)
                label.image = photo
                label.pack()
                checkbox_var = tk.BooleanVar()
                checkbox = tk.Checkbutton(frame, variable=checkbox_var, bg="#f7f7f9")
                checkbox.pack()
                selected_images.append((checkbox_var, image_path))

        def confirm_removal():
            to_remove = [path for var, path in selected_images if var.get()]
            if not to_remove:
                messagebox.showwarning("Błąd", "Nie zaznaczono żadnych obrazków do usunięcia!")
                return

            self.image_paths = [path for path in self.image_paths if path not in to_remove]
            with open("zdjecia.txt", "w") as file:
                file.writelines([path + "\n" for path in self.image_paths])

            self.refresh_gallery()
            remove_window.destroy()

        tk.Button(remove_window, text="Usuń", bg="#f44336", fg="white", font=("Arial", 12), command=confirm_removal).pack(pady=10)

    def start_task(self):
        """Startuje wybrane zadanie."""
        pass

    def pause_task(self):
        """Pauzuje wybrane zadanie."""
        pass

    def stop_task(self):
        """Zatrzymuje wybrane zadanie."""
        pass


if __name__ == "__main__":
    root = tk.Tk()
    app = TaskManagerApp(root)
    root.mainloop()
