# Moduł AI (LLM Service)

Moduł odpowiada za generowanie oficjalnych pism i wniosków studenckich w formacie PDF na podstawie danych sprawy, studenta i powiązanych artykułów prawnych.

## 1. Architektura i integracja

- **Endpoint:** `POST /api/user/cases/{caseId}/application` (`src/framework/api/endpoints/cases.py`) – przyjmuje `NewApplication` (`src/app/dtos/applications.py`), zwraca plik PDF.
- **Use case:** `GenerateApplication` (`src/app/use_cases/applications.py`).
- **Porty:** `src/app/ports/applications.py` (`ApplicationWriter`, `ApplicationRenderer`).
- **Adaptery:**
  - `ApplicationWriter` (`src/infrastructure/ai_services/application_writer.py`) – renderuje prompt Jinja2 (`src/infrastructure/ai_services/prompts/application.md`) i generuje treść przez `LlmChat`.
  - `LlmChat` (`src/infrastructure/ai_services/llm_chat.py`) – klient czatu przez API zgodne z OpenAI: na GCP Vertex AI Model-as-a-Service, on-premise i lokalnie kontener `llm-service` z OVMS (port 8083 na hoście / 8080 w klastrze).
  - `HtmlApplicationRenderer` (`src/infrastructure/pdf/html_renderer.py`) – kompiluje szablon HTML (`src/infrastructure/pdf/templates/application.html`) do PDF i zwraca go jako `bytes`.
- **Konfiguracja:** Zmienne środowiskowe `LLM_SERVICE_*` (`src/shared/settings/ai_services.py`), wymagane jest tylko `LLM_SERVICE_URL` (bazowy URL API razem z `/v1`). Na GCP `LLM_SERVICE_USE_GOOGLE_AUTH=true` – klient uwierzytelnia się tokenem OAuth z Workload Identity (`src/infrastructure/ai_services/openai_client/google_auth.py`).

## 2. Pipeline generowania wniosku

1. Pobranie danych studenta i opisu sytuacji z formularza (`NewApplication`) oraz dokumentów przypiętych do sprawy.
2. Renderowanie promptu w Jinja2 z danymi w blokach XML (`<dane_studenta>`, `<opis_sytuacji>`, `<podstawa_prawna>`).
3. Inferencja LLM (generowanie merytorycznej treści uzasadnienia).
4. Połączenie tekstu z szablonem HTML i wygenerowanie dokumentu PDF przez WeasyPrint. Wniosek nie jest zapisywany, trafia bezpośrednio do przeglądarki.

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
uv run python scripts/prompts_benchmark/compare_prompts.py --model qwen-3.5-9b --skip-pdf

# Uruchomienie z IDE:
# Ustaw zmienną CUSTOM_MODEL_NAME na początku pliku compare_prompts.py.
```

Wyniki zapisywane są w `scripts/prompts_benchmark/benchmark_results/` w formatach `.md`, `.pdf` oraz `summary.json`.

## 5. Testowanie E2E (weryfikacja ręczna)

Instrukcja weryfikacji całego przepływu użytkownika (logowanie -> sprawa -> regulamin -> generowanie PDF) znajduje się w [docs/tests/manual_e2e_test.md](tests/manual_e2e_test.md).