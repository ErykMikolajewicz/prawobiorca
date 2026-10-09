# Test E2E (Frontend + Backend)

## 1. Logowanie
- **Login**: `PrawobiorcaTester`
- **Hasło**: `PrawobiorcaPassword1;`
- **Akcja**: Zaloguj

## 2. Szablon wniosku
- **Pomiń**: Jeśli jest już opublikowany szablon wniosku (`PrawobiorcaTester` jest administratorem)
- **Gdzie**: Panel boczny, "Szablony wniosków"
- **Akcja**: Kliknij "Dodaj szablon", wybierz plik DOCX ze zmienną `paragraphs`, kliknij "Dodaj"
- **Akcja**: Otwórz dodany szablon, skonfiguruj pola, kliknij "Zapisz i opublikuj"
- **Rezultat**: Szablon ma status "Opublikowany"

## 3. Nowa sprawa
- **Gdzie**: Moje sprawy
- **Input**: Wpisz nazwę (np. "Odwołanie od skreślenia")
- **Akcja**: Stwórz

## 4. Dokument prawny
- **Gdzie**: Publiczne regulacje
- **Wybierz**: `PWR - regulamin studiów.pdf` (jeśli jest)
- **Akcja**: Ustawić (lub >)

## 5. Wybór sprawy
- **Gdzie**: Panel boczny, lista "Moje sprawy"
- **Sprawdź**: "Odwołanie od skreślenia" (nazwa z kroku 3) ma wypełnioną pinezkę, czyli jest aktywna. Inną sprawę ustawia się jako aktywną kliknięciem jej pinezki

## 6. Zapytanie
- **Gdzie**: Twoje zapytanie
- **Input**: Wpisz pytanie (np. "Ile mam dni na odwołanie się od decyzji o skreśleniu z listy studentów?")
- **Akcja**: Przeszukaj
- **Wybierz**: Fragment z największą wartością "Podobieństwo", kliknij "Dodaj do sprawy"

## 7. Generowanie Wniosku
- **Gdzie**: Widok szczegółów sprawy (Kontekst / Opis Wniosku)
- **Input**: Wybierz opublikowany szablon wniosku, wypełnij jego pola i opisz sytuację (np. "Wnoszę o uchylenie decyzji o skreśleniu z listy studentów z powodu długotrwałej hospitalizacji w trakcie sesji.")
- **Akcja**: Kliknij "Generuj Wniosek (DOCX)"
- **Rezultat**: Pojawia się komunikat, że wniosek jest generowany, a na liście "Wygenerowane Wnioski" pojawia się wniosek ze statusem "Generowanie". Po zakończeniu generowania status znika, a przycisk "Pobierz" staje się aktywny.
- **Akcja**: Kliknij "Pobierz"
- **Rezultat**: Przeglądarka powinna pobrać gotowy plik DOCX.
