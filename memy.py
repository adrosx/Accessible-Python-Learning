import tkinter as tk
from PIL import Image, ImageTk
import random
import threading

# Przykładowe „ubrania” i „miejsca”, w których są porozrzucane
ubrania = ["sweter", "spodnie", "bluzka", "skarpetki", "koszulka", "szalik", "kapelusz"]
miejsca = ["krzesło", "kanapa", "podłoga", "biurko", "stół", "łóżko"]

# Przykładowe kategorie, gdzie powinny trafiać ubrania
kategorie = {
    "sweter": "szafa",
    "spodnie": "szafa",
    "bluzka": "szafa",
    "skarpetki": "kosz na bieliznę",
    "koszulka": "szafa",
    "szalik": "półka na dodatki",
    "kapelusz": "półka na dodatki"
}

# Flaga do kontroli przenoszenia
przenoszenie_aktywne = False
aktualna_akcja = 0  # Indeks do śledzenia liczby wykonanych akcji
serduszka = []  # Lista do przechowywania ID serduszek

# Funkcja do odtwarzania dźwięku w osobnym wątku
def play_sound(sound_file):
    def _play():
        player = vlc.MediaPlayer(sound_file)
        player.play()
    threading.Thread(target=_play, daemon=True).start()

# Funkcja do przenoszenia ubrań
def rozbierz_edyte():
    global przenoszenie_aktywne, aktualna_akcja
    przenoszenie_aktywne = True  # Włącz przenoszenie
    start_button.config(state="disabled")
    cancel_button.config(state="normal")
    aktualna_akcja = 0
    wykonaj_przenoszenie()  # Rozpocznij przenoszenie

def wykonaj_przenoszenie():
    global przenoszenie_aktywne, aktualna_akcja
    if not przenoszenie_aktywne or aktualna_akcja >= 5:
        result_label.config(text="Przenoszenie zakończone!" if przenoszenie_aktywne else "Przenoszenie anulowane! Edyta ogłasza strajk przenoszeniowy! 😆")
        start_button.config(state="normal")
        cancel_button.config(state="disabled")
        if przenoszenie_aktywne:
            play_sound("happy-outro-8110.mp3")  # Fanfary na zakończenie
            konfetti_efekt()
        return

    ubranie = random.choice(ubrania)
    miejsce = random.choice(miejsca)
    docelowe_miejsce = kategorie.get(ubranie, "brak kategorii")
    
    result_text = f"Znaleziono '{ubranie}' na '{miejsce}'. Przenoszenie do: {docelowe_miejsce}...\n"
    result_text += f"'{ubranie}' z '{miejsce}' trafiło do '{docelowe_miejsce}'!\nPlusia jest szczęśliwa! 😄"
    
    result_label.config(text=result_text)
    aktualna_akcja += 1

    # Przemieszczenie obrazka królika w losowe miejsce
    new_x = random.randint(0, 250)
    new_y = random.randint(0, 20)
    canvas.coords(rabbit_image_id, new_x, new_y)

    # Dodanie animowanych serduszek
    for _ in range(3):  # Dodajemy kilka serduszek
        heart_x = random.randint(50, 350)
        heart_y = random.randint(10, 50)
        heart_id = canvas.create_text(heart_x, heart_y, text="❤️", font=("Arial", 24))
        serduszka.append(heart_id)
        animate_heart(heart_id)

    # Efekt płonącego tekstu
    change_text_color()
    root.after(3000, wykonaj_przenoszenie)  # Wykonaj kolejną akcję po 3 sekundach

def animate_heart(heart_id):
    """Animacja unoszących się serduszek."""
    x, y = canvas.coords(heart_id)
    if y > 0:
        canvas.move(heart_id, 0, -1)
        root.after(50, lambda: animate_heart(heart_id))
    else:
        canvas.delete(heart_id)  # Usunięcie serduszka po animacji

def change_text_color():
    """Zmienia kolory tekstu jakby płonął."""
    colors = ["red", "orange", "yellow"]
    color = random.choice(colors)
    result_label.config(fg=color)
    if przenoszenie_aktywne:
        root.after(200, change_text_color)  # Zmiana koloru co 200 ms

def konfetti_efekt():
    """Efekt konfetti po zakończeniu przenoszenia."""
    for _ in range(20):  # Tworzymy 20 kawałków konfetti
        x = random.randint(0, 400)
        y = random.randint(0, 150)
        konfetti_id = canvas.create_text(x, y, text="🎉", font=("Arial", 16))
        animate_konfetti(konfetti_id)

def animate_konfetti(konfetti_id):
    """Animacja opadającego konfetti."""
    x, y = canvas.coords(konfetti_id)
    if y < 150:
        canvas.move(konfetti_id, 0, 2)
        root.after(50, lambda: animate_konfetti(konfetti_id))
    else:
        canvas.delete(konfetti_id)

def anuluj_przenoszenie():
    global przenoszenie_aktywne
    przenoszenie_aktywne = False  # Wyłącz przenoszenie
    play_sound("049269_funny-fanfare-2wav-65260.mp3")  # Dźwięk anulowania

def zakonczenie():
    messagebox.showinfo("Koniec", "Operacja zakończona – Edyta (czyli jej ubrania) są teraz (teoretycznie) w porządku!")

# Konfiguracja GUI
root = tk.Tk()
root.title("Rozbieranie Edyty – Wirtualny Porządkowy")
root.geometry("400x450")

# Nagłówek
header_label = tk.Label(root, text="Operacja 'Rozbieranie Edyty'", font=("Arial", 16))
header_label.pack(pady=10)

# Wczytanie i dodanie obrazka królika
canvas = tk.Canvas(root, width=400, height=150, bg="white")
canvas.pack()

rabbit_img = Image.open("rabbit.jpg")
rabbit_img = rabbit_img.resize((150, 150), Image.LANCZOS)  # Powiększenie królika
rabbit_photo = ImageTk.PhotoImage(rabbit_img)

rabbit_image_id = canvas.create_image(0, 0, anchor="nw", image=rabbit_photo)

# Przycisk "Rozpocznij"
start_button = tk.Button(root, text="Rozpocznij przenoszenie", command=rozbierz_edyte, font=("Arial", 12))
start_button.pack(pady=10)

# Pole tekstowe do wyników
result_label = tk.Label(root, text="", font=("Arial", 12), wraplength=350, justify="center")
result_label.pack(pady=10)

# Przycisk "Anuluj przenoszenie"
cancel_button = tk.Button(root, text="Anuluj przenoszenie", command=anuluj_przenoszenie, font=("Arial", 12), state="disabled")
cancel_button.pack(pady=10)

# Przycisk "Zakończ operację"
end_button = tk.Button(root, text="Zakończ operację", command=zakonczenie, font=("Arial", 12))
end_button.pack(pady=10)

root.mainloop()
