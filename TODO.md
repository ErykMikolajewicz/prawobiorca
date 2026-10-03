# MOJA LISTA ZADAŃ (TODO LIST):

Lista kroków do wdrożenia obsługi szablonów, silnika Jinja2, Clean Architecture oraz integracji modelu AI Gemma 4 (OpenVINO).

## Legenda statusów
- `DONE` — funkcja zaimplementowana i dostępna
- `TODO` — funkcja planowana

---

### UKOŃCZONE KROKI (1-5)
- `DONE` **Krok 1:** Instalacja i konfiguracja środowiska Jinja2.
- `DONE` **Krok 2:** Utworzenie szablonu Markdown i obsługa danych użytkownika w promptach.
- `DONE` **Krok 3:** Refaktoryzacja całego modułu generowania (Clean Architecture: Porty, Use Case, Adaptery).
- `DONE` **Krok 4:** Renderowanie metadanych PDF (dane studenta) przy użyciu Jinja2.
- `DONE` **Krok 5:** Dynamiczne wnioski za pomocą HTML i CSS (WeasyPrint - `HTMLToPDFRenderer` + `szablon_wniosku.html`).

---

### Krok 6: Integracja serwera LLM OpenVINO (OpenAI-compatible na localhost:8083)
- `DONE` **Adapter OpenAI/OpenVINO:** Zaimplementowano `OpenVINOClient` w `core-service/src/infrastructure/ai/openvino_client.py` łączący się z OpenVINO Model Server na `http://localhost:8083/v1`.
- `DONE` **Konfiguracja .env:** Dodano zmienne środowiskowe (`LLM_PROVIDER`, `OPENVINO_*`, `OLLAMA_*`) pozwalające na płynne przełączanie między OpenVINO i Ollama.
- `DONE` **Wpięcie w zależności FastAPI:** Zaktualizowano `get_llm_client()` w `src/framework/dependencies/pdf_generation.py` o dynamiczny wybór adaptera.
- `DONE` **Weryfikacja promptów i architektury:** Przeprowadzono benchmarki promptów w `core-service/tests/unit/ai/compare_prompts.py`, udokumentowano ograniczenia modeli w `docs/ai.md`.
- `TODO` **Finalny dobór modelu pod serwer koła:** Ustalenie limitów RAM serwera z autorem projektu i zatwierdzenie finalnej wagi modelu (wariant 3B vs 7B INT4).

---

### Krok 7: Frontend (`prawobiorca-frontend`)
- `DONE` **Pobieranie PDF:** Obsługa automatycznego pobierania wygenerowanego pliku PDF z backendu.
- `TODO` **Wskaźnik ładowania:** Dodanie stanu ładowania (spinner / disabled button) w `GeneratePdfForm.vue` na czas generowania tekstu przez LLM i tworzenia DOCX.
- `TODO` **Pola danych studenta:** Umożliwienie wprowadzania/edycji danych studenta (imię, nazwisko, nr indeksu, wydział) w formularzu generowania wniosku.
- `DONE` **Powiadomienia o statusie:** Pokazywanie powiadomień sukcesu/błędu (Element Plus notification/message) po zakończeniu generowania.