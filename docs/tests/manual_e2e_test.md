# Test E2E (Frontend + Backend)

## 1. Logowanie
- **Login**: `PrawobiorcaTester`
- **Hasło**: `PrawobiorcaPassword1;`
- **Akcja**: Zaloguj

## 2. Nowa sprawa
- **Gdzie**: Moje sprawy
- **Input**: Wpisz nazwę (np. "Odwołanie od skreślenia")
- **Akcja**: Stwórz

## 3. Dokument prawny
- **Gdzie**: Publiczne regulacje
- **Wybierz**: `PWR - regulamin studiów.pdf` (jeśli jest)
- **Akcja**: Ustawić (lub >)

## 4. Wybór sprawy
- **Gdzie**: Bieżąca sprawa
- **Wybierz**: "Odwołanie od skreślenia" (nazwę z kroku 2)

## 5. Zapytanie
- **Gdzie**: Twoje zapytanie
- **Input**: Wpisz pytanie (np. "Ile mam dni na odwołanie się od decyzji o skreśleniu z listy studentów?")
- **Akcja**: Przeszukaj
- **Wybierz**: Fragment z największą wartością "Podobieństwo", kliknij "Dodaj do sprawy"

## 6. Generowanie Wniosku
- **Gdzie**: Widok szczegółów sprawy (Kontekst / Opis Wniosku)
- **Input**: Wypełnij dane studenta (imię i nazwisko, numer albumu w formacie 6 cyfr, wydział, semestr, tytuł zawodowy) i opisz sytuację (np. "Wnoszę o uchylenie decyzji o skreśleniu z listy studentów z powodu długotrwałej hospitalizacji w trakcie sesji.")
- **Akcja**: Kliknij "Generuj Wniosek (PDF)"
- **Rezultat**: Przeglądarka powinna pobrać gotowy plik PDF.
