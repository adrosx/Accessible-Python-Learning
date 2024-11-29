def dlugosci_slow(lista_slow):
    dlugosci = []  # Tworzymy pustą listę na wyniki
    for slowo in lista_slow:  # Iterujemy przez każde słowo w liście
        dlugosci.append(len(slowo))  # Dodajemy długość słowa do listy wyników
    return dlugosci

# Wywołanie funkcji
print(dlugosci_slow(["Python", "programowanie", "quiz"]))  
# Powinno zwrócić [6, 13, 4]
