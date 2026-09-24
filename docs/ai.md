# Moduł AI (LLM Service)

Moduł odpowiada za generowanie oficjalnych pism i wniosków studenckich w formacie PDF na podstawie danych sprawy, studenta i powiązanych artykułów prawnych.

## 1. Architektura i integracja

- **Interfejs (`Port`):** `src/app/interfaces/pdf_generation.py` (`LLMClient`)
- **Adaptery:**
  - `OpenVINOClient` (`src/infrastructure/ai/openvino_client.py`) – domyślny, łączy się z kontenerem `llm-service` (port 8083, API OpenAI).
  - `OllamaClient` (`src/infrastructure/ai/ollama_client.py`) – alternatywny dla kart graficznych NVIDIA (port 11434).
- **Przełącznik w `.env`:** `LLM_PROVIDER=openvino` lub `LLM_PROVIDER=ollama`. Fabryka w `src/framework/dependencies/pdf_generation.py` automatycznie inicjalizuje odpowiedniego klienta.

## 2. Pipeline generowania wniosku

1. Pobranie danych studenta (`StudentData`) oraz artykułów powiązanych ze sprawą.
2. Renderowanie promptu w Jinja2 (`src/shared/resources/prompts/system_prompt.md`) z danymi w blokach XML (`<dane_studenta>`, `<opis_sytuacji>`, `<podstawa_prawna>`).
3. Inferencja LLM (generowanie merytorycznej treści uzasadnienia).
4. Połączenie tekstu z szablonem HTML (`application_template.html`) i wygenerowanie dokumentu PDF przez WeasyPrint (`HTMLToPDFRenderer`).

## 3. Przetestowane modele

| Model | Status | Pamięć RAM | Uwagi |
|---|---|---|---|
| **`OpenVINO/Qwen2.5-7B-Instruct-int4-ov`** | **Domyślny (rekomendowany)** | ~4.5 GB | Oficjalny model Intela, pełne wsparcie ChatML (`system`/`user`), wysoka kultura polszczyzny urzędowej. |
| **`OpenVINO/gemma-2b-it-int8-ov`** | Awaryjny / fallback | ~2.0 GB | Pobrany lokalnie; brak roli `system`, ubogi korpus polski (czeskie słowa), ucinanie tekstu przy temp. < 0.7. |
| **`OpenVINO/gemma-4-E4B-it-int8-ov`** | Odrzucony | - | Model multimodalny (VLM); błąd `Segmentation fault` (139) w OVMS 2026.3. |

## 4. Narzędzie testowe (benchmark promptów)

Skrypt `core-service/tests/unit/ai/compare_prompts.py` umożliwia testowanie jakości promptów i temperatur na przygotowanych sprawach testowych (`test_cases.json`):

```bash
# Uruchomienie z terminala:
uv run python tests/unit/ai/compare_prompts.py --openvino --model qwen-2.5-7b-it

# Uruchomienie z IDE:
# Ustaw zmienne DEFAULT_LLM_PROVIDER oraz CUSTOM_MODEL_NAME na początku pliku compare_prompts.py.
```

Wyniki zapisywane są w `tests/unit/ai/benchmark_results/` w formatach `.md`, `.pdf` oraz `summary.json`.

## 5. Testowanie E2E (weryfikacja ręczna)

Instrukcja weryfikacji całego przepływu użytkownika (logowanie -> sprawa -> regulamin -> generowanie PDF) znajduje się w [docs/tests/manual_e2e_test.md](tests/manual_e2e_test.md).