# Moduł AI (LLM Service)

Moduł odpowiada za generowanie oficjalnych pism i wniosków studenckich w formacie DOCX na podstawie danych sprawy, studenta i powiązanych artykułów prawnych.

## 1. Architektura i integracja

- **Endpointy** (`src/framework/api/endpoints/cases.py`):
  - `POST /api/user/cases/{caseId}/application` przyjmuje `NewApplication` (`src/app/dtos/applications.py`), zapisuje wniosek ze statusem `IN_PROGRESS`, zleca generowanie w tle i zwraca `202` z identyfikatorem wniosku.
  - `GET /api/user/cases/{caseId}/applications` zwraca listę wniosków sprawy (`ApplicationRepresentation`) ze statusem generowania.
  - `GET /api/user/cases/applications/{applicationId}/download-url` zwraca presigned URL do pliku DOCX. Dla wniosku, który nie ma statusu `GENERATED`, zwraca `409`.
  - `DELETE /api/user/cases/applications/{applicationId}` usuwa wniosek i jego plik.
- **Typ wniosku:** `ApplicationType` (`src/domain/value_objects/applications.py`), pole `applicationType` w `NewApplication`, domyślnie `OTHER`. Każdy typ ma własny prompt (`prompts/applications/{typ}.md`) i szablon DOCX (`templates/applications/{typ}.docx`), gdzie `{typ}` to wartość enuma małymi literami. Dodanie nowego typu: wartość w enumie, oba pliki oraz etykieta we frontendzie (`prawobiorca-frontend/src/domain/applications.ts`).
- **Status generowania:** `ApplicationGenerationStatus` (`src/domain/value_objects/applications.py`): `IN_PROGRESS`, `GENERATED`, `FAILED`.
- **Use case'y** (`src/app/use_cases/applications.py`): `AddApplication` (zapis i zlecenie zadania), `GenerateApplication` (wykonywany przez worker), `FailApplicationGeneration`, `ListApplications`, `GetApplicationDownloadUrl`, `DeleteApplication`.
- **Zadanie w tle:** `generate_application` (`src/framework/workers/applications.py`), zlecane przez `PostgresApplicationGenerationScheduler` (`src/infrastructure/tasks/applications.py`) w tej samej transakcji, w której zapisywany jest wniosek.
- **Porty:** `src/app/ports/applications.py` (`ApplicationWriter`, `ApplicationRenderer`).
- **Adaptery:**
  - `ApplicationWriter` (`src/infrastructure/ai_services/application_writer.py`) – renderuje prompt Jinja2 (`src/infrastructure/ai_services/prompts/applications/{typ}.md`) i generuje treść przez `LlmChat`.
  - `LlmChat` (`src/infrastructure/ai_services/llm_chat.py`) – klient czatu przez API zgodne z OpenAI: na GCP Vertex AI Model-as-a-Service, on-premise i lokalnie kontener `llm-service` z OVMS (port 8083 na hoście / 8080 w klastrze).
  - `DocxApplicationRenderer` (`src/infrastructure/docx/docx_renderer.py`) – renderuje szablon DOCX (`src/infrastructure/docx/templates/applications/{typ}.docx`) i zwraca go jako `bytes`.
  - `ApplicationsRepository` (`src/infrastructure/relational_db/repositories/applications.py`) – tabela `applications` (wniosek należy do sprawy, usuwany kaskadowo razem z nią).
  - `S3ApplicationsStorage` (`src/infrastructure/object_storage/repository.py`) – pliki DOCX w object storage pod kluczem `applications/{id}`.
- **Konfiguracja:** Zmienne środowiskowe `LLM_SERVICE_*` (`src/shared/settings/ai_services.py`), wymagane jest tylko `LLM_SERVICE_URL` (bazowy URL API razem z `/v1`). Na GCP `LLM_SERVICE_USE_GOOGLE_AUTH=true` – klient uwierzytelnia się tokenem OAuth z Workload Identity (`src/infrastructure/ai_services/openai_client/google_auth.py`).

## 2. Pipeline generowania wniosku

1. `core-service` zapisuje wniosek ze statusem `IN_PROGRESS` i w tej samej transakcji wstawia zadanie do kolejki Taskiq. Dane z formularza (`NewApplication`) trafiają wyłącznie do argumentów zadania, nie są zapisywane przy wniosku. Wiersz zadania jest usuwany po jego wykonaniu.
2. Worker pobiera dokumenty przypięte do sprawy.
3. Renderowanie promptu w Jinja2 z danymi w blokach XML (`<dane_studenta>`, `<opis_sytuacji>`, `<podstawa_prawna>`).
4. Inferencja LLM (generowanie merytorycznej treści uzasadnienia).
5. Połączenie tekstu z szablonem DOCX i wygenerowanie dokumentu przez docxtpl.
6. Zapis pliku w object storage i zmiana statusu na `GENERATED`. Frontend odpytuje listę wniosków, dopóki któryś ma status `IN_PROGRESS`, a gotowy plik pobiera przez presigned URL.

Obsługa błędów:
- Niedostępność LLM (`ServiceUnavailable`) ustawia status `FAILED` i ponawia zadanie (`SimpleRetryMiddleware`). Kolejna próba przywraca `IN_PROGRESS`.
- Po przekroczeniu limitu dostarczeń (`MAX_APPLICATION_GENERATION_DELIVERIES`) wniosek dostaje status `FAILED` bez kolejnej próby.
- Jeśli wniosek albo sprawa zostaną usunięte w trakcie generowania, worker kończy zadanie bez zapisu pliku.

## 3. Modele

| Środowisko | Model | Uwagi |
|---|---|---|
| **GCP** | `google/gemma-4-26b-a4b-it-maas` (Vertex AI MaaS) | Serverless, płatność za tokeny. Wymaga włączenia modelu w Model Garden i roli `roles/aiplatform.user` (`scripts/cloud/cloud_inith.sh`). |
| **On-premise** | `OpenVINO/gemma-4-26b-a4b-it-int4-ov` (OVMS, `gemma-4-26b`) | `deploy/local/llm-service.yaml`. |
| **Lokalnie** | `OpenVINO/Qwen3.5-9B-int4-ov` (OVMS, `qwen-3.5-9b`) | `scripts/local/dev.py`, lżejszy model do testów. |

Wcześniej testowane: `OpenVINO/Qwen2.5-7B-Instruct-int4-ov`, `OpenVINO/gemma-2b-it-int8-ov` (brak roli `system`, ubogi korpus polski), `OpenVINO/gemma-4-E4B-it-int8-ov` (`Segmentation fault` w OVMS 2026.3).

## 4. Narzędzie testowe (benchmark promptów)

Skrypt `core-service/scripts/prompts_benchmark/compare_prompts.py` umożliwia testowanie jakości promptów i temperatur na przygotowanych sprawach testowych (`test_cases.json`):

```bash
just compare-prompts

# Uruchomienie z flagami CLI:
uv run python scripts/prompts_benchmark/compare_prompts.py --model qwen-3.5-9b --skip-docx

# Uruchomienie z IDE:
# Ustaw zmienną CUSTOM_MODEL_NAME na początku pliku compare_prompts.py.
```

Wyniki zapisywane są w `scripts/prompts_benchmark/benchmark_results/` w formatach `.md`, `.docx` oraz `summary.json`.

## 5. Testowanie E2E (weryfikacja ręczna)

Instrukcja weryfikacji całego przepływu użytkownika (logowanie -> sprawa -> regulamin -> generowanie i pobranie DOCX) znajduje się w [docs/tests/manual_e2e_test.md](tests/manual_e2e_test.md).