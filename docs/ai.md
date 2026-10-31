# Moduł AI (LLM Service)

Moduł odpowiada za generowanie oficjalnych pism i wniosków studenckich w formacie DOCX na podstawie danych sprawy, studenta i powiązanych artykułów prawnych.

## 1. Architektura i integracja

- **Endpointy** (`src/framework/api/endpoints/cases.py`):
  - `POST /api/cases/{caseId}/applications` przyjmuje `NewApplication` (`src/app/dtos/applications.py`), zapisuje wniosek ze statusem `IN_PROGRESS`, zleca generowanie w tle i zwraca `202` z identyfikatorem wniosku. Dla nieistniejącego lub nieopublikowanego szablonu zwraca `404`, dla błędnych wartości pól `422` z listą nazw pól.
  - `GET /api/cases/{caseId}/applications` zwraca listę wniosków sprawy (`ApplicationRepresentation`) ze statusem generowania.
  - `GET /api/cases/{caseId}/applications/{applicationId}/download-url` zwraca presigned URL do pliku DOCX. Dla wniosku, który nie ma statusu `GENERATED`, zwraca `409`.
  - `DELETE /api/cases/{caseId}/applications/{applicationId}` usuwa wniosek i jego plik.
- **Szablon wniosku:** `NewApplication` zawiera `templateId` opublikowanego szablonu (zarządzanego przez administratora), opis sytuacji (`description`) i wartości pól szablonu (`fieldValues`), walidowane przez `validate_field_values` (`src/domain/services/application_fields.py`). Szablon dostarcza instrukcje dla AI (`instructions`), definicje pól i plik DOCX w object storage. Wniosek przechowuje `template_id` (po usunięciu szablonu `NULL`) i kopię nazwy szablonu (`template_name`).
- **Nazwa wniosku:** pole `name` w `ApplicationRepresentation`, nadawane przez LLM na podstawie opisu sytuacji (prompt `prompts/application_name.md`) i zapisywane razem ze statusem `GENERATED`. Do tego czasu ma wartość `null`, a frontend pokazuje w jej miejscu nazwę szablonu.
- **Status generowania:** `ApplicationGenerationStatus` (`src/domain/value_objects/applications.py`): `IN_PROGRESS`, `GENERATED`, `FAILED`.
- **Use case'y** (`src/app/use_cases/applications.py`): `AddApplication` (zapis i zlecenie zadania), `GenerateApplication` (wykonywany przez worker), `FailApplicationGeneration`, `ListApplications`, `GetApplicationDownloadUrl`, `DeleteApplication`.
- **Zadanie w tle:** `generate_application` (`src/framework/workers/applications.py`), zlecane przez `PostgresApplicationGenerationScheduler` (`src/infrastructure/tasks/applications.py`) w tej samej transakcji, w której zapisywany jest wniosek.
- **Porty:** `src/app/ports/applications.py` (`ApplicationWriter`, `ApplicationRenderer`).
- **Adaptery:**
  - `ApplicationWriter` (`src/infrastructure/ai_services/application_writer.py`) – renderuje prompt Jinja2 (`src/infrastructure/ai_services/prompts/application.md`) z instrukcjami szablonu i danymi wniosku i generuje treść przez `LlmChat`; osobnym wywołaniem (`write_name`, prompt `src/infrastructure/ai_services/prompts/application_name.md`) generuje nazwę wniosku.
  - `LlmChat` (`src/infrastructure/ai_services/llm_chat.py`) – klient czatu przez API zgodne z OpenAI: na GCP Vertex AI Model-as-a-Service, on-premise i lokalnie kontener `llm-service` z OVMS (port 8083 na hoście / 8080 w klastrze).
  - `DocxApplicationRenderer` (`src/infrastructure/docx/docx_renderer.py`) – renderuje szablon DOCX pobrany z object storage (w `SandboxedEnvironment`) z wartościami pól, `current_date` i `paragraphs` (stałe `CURRENT_DATE_TEMPLATE_VARIABLE` i `CONTENT_TEMPLATE_VARIABLE`) i zwraca go jako `bytes`.
  - `ApplicationsRepository` (`src/infrastructure/relational_db/repositories/applications.py`) – tabela `applications` (wniosek należy do sprawy, usuwany kaskadowo razem z nią).
  - `S3ApplicationsStorage` (`src/infrastructure/object_storage/repository.py`) – pliki DOCX w object storage pod kluczem `applications/{id}`.
- **Konfiguracja:** Zmienne środowiskowe `LLM_SERVICE_*` (`src/shared/settings/ai_services.py`), wymagane jest tylko `LLM_SERVICE_URL` (bazowy URL API razem z `/v1`). Na GCP `LLM_SERVICE_USE_GOOGLE_AUTH=true` – klient uwierzytelnia się tokenem OAuth z Workload Identity (`src/infrastructure/ai_services/openai_client/google_auth.py`).

## 2. Szablony wniosków

Szablonami zarządza administrator, a zalogowany użytkownik widzi tylko szablony opublikowane. Use case'y dostają `Caller` i sprawdzają dostęp politykami z `src/domain/services/application_template_access.py` (`check_can_manage_application_templates`, `check_can_read_published_application_templates`).

- **Endpointy** (`src/framework/api/endpoints/application_templates.py`):
  - `GET /api/application-templates/published` zwraca opublikowane szablony (`PublishedApplicationTemplate`) z opisem i definicjami pól, bez instrukcji dla AI. Dostępny dla zalogowanego użytkownika.
  - `GET /api/application-templates/published/search` wyszukuje opublikowane szablony po opisie – patrz [Opisy szablonów](#5-opisy-szablonów).
  - `GET /api/application-templates` i `GET /api/application-templates/{templateId}` zwracają szablony (`ApplicationTemplateRepresentation`) niezależnie od statusu.
  - `POST /api/application-templates` przyjmuje nazwę szablonu, zapisuje go z domyślnymi instrukcjami i zwraca presigned POST do wgrania pliku DOCX.
  - `POST /api/application-templates/{templateId}/confirm-upload` pobiera plik z object storage, odczytuje jego zmienne, tworzy z nich domyślne pola i zmienia status na `DRAFT`. Plik jest pobierany i analizowany poza transakcją, a zmiana statusu jest warunkowa (`confirm_upload` aktualizuje tylko szablon w statusie `NOT_UPLOADED`). Zwraca `409`, jeśli wgranie było już potwierdzone (także równolegle) albo pliku nie ma w object storage, i `422` dla niepoprawnego szablonu DOCX.
  - `PUT /api/application-templates/{templateId}` zapisuje nazwę, instrukcje, opis i konfigurację pól (`ApplicationTemplateDetailsData`). Tylko dla statusu `DRAFT` (inaczej `409`), dla niepoprawnej konfiguracji pól albo suborganizacji podanej bez organizacji zwraca `422`.
  - `POST /api/application-templates/{templateId}/publish` publikuje szablon w statusie `DRAFT` z niepustymi instrukcjami (`is_ready_to_publish`, `src/domain/services/application_templates.py`, inaczej `409`).
  - `POST /api/application-templates/{templateId}/unpublish` przywraca opublikowanemu szablonowi status `DRAFT` (inaczej `409`).
  - `GET /api/application-templates/{templateId}/download-url` zwraca presigned URL do pliku DOCX (`409`, jeśli plik nie został wgrany). Frontend używa go do pobrania i podglądu szablonu.
  - `POST /api/application-templates/{templateId}/description-generation` zleca wygenerowanie opisu – patrz [Opisy szablonów](#5-opisy-szablonów).
  - `DELETE /api/application-templates/{templateId}` usuwa szablon i jego plik. Wygenerowane wnioski zostają, z `template_id` ustawionym na `NULL`.
- **Status:** `ApplicationTemplateStatus` (`src/domain/value_objects/application_templates.py`): `NOT_UPLOADED` → `DRAFT` ⇄ `PUBLISHED`.
- **Plik DOCX:** szablon Jinja2 dla docxtpl. Musi zawierać zmienną `paragraphs` (treść wygenerowana przez LLM), `current_date` jest wypełniana automatycznie. Nagłówek, adresat, zwrot grzecznościowy, zwrot końcowy i podpis są częścią szablonu – LLM ich nie generuje. Pozostałe zmienne stają się polami szablonu (`create_default_fields`, `src/domain/services/application_fields.py`).
- **Pola** (`ApplicationTemplateField`): nazwa zmiennej, etykieta, typ (`TEXT`, `NUMBER`, `SELECT`, `DATE`), `required`, `passToAi`, opcjonalnie wartość domyślna, `pattern` i `options`. Reguły konfiguracji (`validate_fields_config`):
  - zbiór pól musi odpowiadać zmiennym szablonu, bez duplikatów,
  - `pattern` (poprawny regex) tylko dla `TEXT`,
  - `options` wymagane dla `SELECT` i niedozwolone dla innych typów,
  - wartość domyślna musi przechodzić walidację pola.

  Wartości wpisane przez użytkownika waliduje `validate_field_values`: `NUMBER` – skończona liczba, `SELECT` – jedna z opcji, `DATE` – format `dd.mm.yyyy`, `TEXT` – pełne dopasowanie do `pattern`.
- **Instrukcje dla AI:** Markdown edytowany przez administratora. Nowy szablon dostaje domyślne instrukcje z `src/infrastructure/ai_services/prompts/application_template_instructions.md`.
- **Use case'y** (`src/app/use_cases/application_templates.py`): `ListApplicationTemplates`, `GetApplicationTemplate`, `ListPublishedApplicationTemplates`, `AddApplicationTemplate`, `ConfirmApplicationTemplateUpload`, `UpdateApplicationTemplate`, `PublishApplicationTemplate`, `UnpublishApplicationTemplate`, `DeleteApplicationTemplate`, `GetApplicationTemplateDownloadUrl`.
- **Porty:** `src/app/ports/application_templates.py` (`ApplicationTemplateInspector`, `ApplicationTemplateInstructionsProvider`).
- **Adaptery:**
  - `DocxTemplateInspector` (`src/infrastructure/docx/template_inspector.py`) – odczytuje zmienne szablonu DOCX (w `SandboxedEnvironment`) i jego tekst (akapity i komórki tabel) na potrzeby opisu.
  - `PromptsApplicationTemplateInstructionsProvider` (`src/infrastructure/ai_services/application_template_instructions.py`) – domyślne instrukcje dla AI.
  - `ApplicationTemplatesRepository` (`src/infrastructure/relational_db/repositories/application_templates.py`) – tabela `application_templates`.
  - `S3ApplicationTemplatesStorage` (`src/infrastructure/object_storage/repository.py`) – pliki DOCX w object storage pod kluczem `application_templates/{id}`.

## 3. Pipeline generowania wniosku

1. `core-service` zapisuje wniosek ze statusem `IN_PROGRESS` i w tej samej transakcji wstawia zadanie do kolejki Taskiq. Dane z formularza (`NewApplication`) trafiają wyłącznie do argumentów zadania, nie są zapisywane przy wniosku. Wiersz zadania jest usuwany po jego wykonaniu.
2. Worker pobiera szablon (instrukcje, pola i plik DOCX) oraz dokumenty przypięte do sprawy. Jeśli szablon został usunięty, nie jest już opublikowany albo wartości pól nie przechodzą `validate_field_values` dla jego aktualnej konfiguracji, wniosek dostaje status `FAILED`.
3. Renderowanie promptu w Jinja2: instrukcje szablonu, a po nich dane w blokach XML (`<dane_wniosku>` z polami oznaczonymi `passToAi`, `<opis_sytuacji>`, `<podstawa_prawna>`).
4. Inferencja LLM (generowanie merytorycznej treści uzasadnienia), a następnie osobne wywołanie generujące krótką nazwę wniosku.
5. Połączenie tekstu z szablonem DOCX i wygenerowanie dokumentu przez docxtpl.
6. Zapis nazwy, pliku w object storage i zmiana statusu na `GENERATED`. Frontend odpytuje listę wniosków, dopóki któryś ma status `IN_PROGRESS`, a gotowy plik pobiera przez presigned URL.

Obsługa błędów:
- Niedostępność LLM (`ServiceUnavailable`) ustawia status `FAILED` i ponawia zadanie (`SimpleRetryMiddleware`). Kolejna próba przywraca `IN_PROGRESS`.
- Po przekroczeniu limitu dostarczeń (`MAX_APPLICATION_GENERATION_DELIVERIES`) wniosek dostaje status `FAILED` bez kolejnej próby.
- Jeśli wniosek albo sprawa zostaną usunięte w trakcie generowania, worker kończy zadanie bez zapisu pliku.

## 4. Opisy regulacji

Administrator może zlecić wygenerowanie przez LLM ogólnego opisu regulacji (2–4 zdania: czego i kogo dotyczy dokument oraz jakie główne obszary reguluje, bez terminów, kwot i numerów jednostek). Opis ma posłużyć do wektorowego wyszukiwania właściwego aktu prawnego, dlatego razem z nim zapisywany jest jego wektor.

- **Status generowania:** `RegulationDescriptionStatus` (`src/domain/value_objects/regulations.py`): `NOT_REQUESTED`, `IN_PROGRESS`, `GENERATED`, `FAILED`, zwracany jako `descriptionStatus` w `RegulationRepresentation`.
- **Zlecenie przy dodaniu:** `POST /api/regulations` z `generateDescription: true` (tylko administrator, inaczej `403`) zapisuje regulację ze statusem opisu `IN_PROGRESS`. `PrepareRegulation` po ustawieniu `PREPARED` wstawia w tej samej transakcji zadanie generowania opisu – opis powstaje z sekcji zapisanych podczas przygotowania, bez ponownej ekstrakcji.
- **Ponowne wygenerowanie:** `POST /api/regulations/{regulationId}/description-generation` (tylko administrator) ustawia `IN_PROGRESS` i zleca zadanie. Zwraca `409`, jeśli regulacja nie jest przygotowana albo opis jest już generowany.
- **Zadanie w tle:** `generate_regulation_description` (`src/framework/workers/regulations.py`), use case `GenerateRegulationDescription`. Wejście dla LLM (`create_description_source`, `src/domain/services/regulation_description.py`) to nazwa dokumentu, spis treści z nagłówków sekcji (rozdziały i tytuły jednostek redakcyjnych bez ich numerów, maks. `MAX_DESCRIPTION_HEADINGS`) i początek tekstu (maks. `MAX_DESCRIPTION_BEGINNING_CHARS` znaków). Prompt: `src/infrastructure/ai_services/prompts/regulation_description.md`.
- **Wektor opisu:** kolumna `regulations.description_vector`, liczona przez worker, czyli na GCP przez instancję `embedding-batch-service`. Ręczna zmiana treści opisu (`PATCH /api/regulations/{regulationId}`) czyści wektor.
- **Wyszukiwanie po opisie:** `GET /api/regulations/search` (use case `SearchRegulations`) przyjmuje zapytanie w języku naturalnym (`query`) i minimalne podobieństwo (`threshold`) oraz te same filtry co lista regulacji (`scope`, `documentType`, `organizationId`, `suborganizationId`). Zapytanie jest zamieniane na wektor przez `embedding-service`, a wynik to lista `RegulationSearchResult` (regulacja i `score`, podobieństwo cosinusowe) posortowana malejąco po podobieństwie. Regulacje bez wektora opisu nie trafiają do wyników.
- **Obsługa błędów:** jak przy wnioskach – `ServiceUnavailable` ustawia `FAILED` i ponawia zadanie, po przekroczeniu `MAX_REGULATION_DESCRIPTION_GENERATION_DELIVERIES` opis zostaje w statusie `FAILED`.
- **Frontend:** checkbox „Wygeneruj opis przez AI” w dialogu dodawania regulacji i przycisk o tej samej nazwie w szczegółach przygotowanej regulacji (oba tylko dla administratora). W trakcie generowania pole opisu jest zablokowane, a lista regulacji jest odpytywana do zakończenia. Na stronie głównej formularz `RegulationsSearchForm` filtruje obie listy (publiczną i użytkownika) po opisie, pozwala wybrać próg istotności i kolejność (alfabetycznie albo wg trafności) i pokazuje podobieństwo przy każdej regulacji; parametry wyszukiwania są zapisywane w adresie strony.

## 5. Opisy szablonów

Administrator może zlecić wygenerowanie przez LLM krótkiego opisu szablonu wniosku (1–3 zdania: o co wnioskodawca prosi, do kogo kieruje pismo i w jakiej sytuacji z niego korzysta). Opis i jego wektor służą do wyszukiwania pasującego szablonu przez użytkownika, a sam opis jest też widoczny przy wyborze szablonu.

- **Status generowania:** `ApplicationTemplateDescriptionStatus` (`src/domain/value_objects/application_templates.py`): `NOT_REQUESTED`, `IN_PROGRESS`, `GENERATED`, `FAILED`, zwracany jako `descriptionStatus` w `ApplicationTemplateRepresentation`.
- **Zlecenie:** `POST /api/application-templates/{templateId}/description-generation` (use case `RegenerateApplicationTemplateDescription`, tylko administrator) ustawia `IN_PROGRESS` i w tej samej transakcji zleca zadanie. Zwraca `202`, `404` dla nieistniejącego szablonu i `409`, jeśli szablon nie jest w statusie `DRAFT` albo opis jest już generowany.
- **Zadanie w tle:** `generate_application_template_description` (`src/framework/workers/applications.py`), use case `GenerateApplicationTemplateDescription`. Wejście dla LLM (`create_description_source`, `src/domain/services/application_template_description.py`) to nazwa szablonu, instrukcje dla AI (maks. `MAX_DESCRIPTION_INSTRUCTIONS_CHARS` znaków), etykiety pól i tekst pliku DOCX pobranego z object storage (maks. `MAX_DESCRIPTION_CONTENT_CHARS` znaków). Prompt: `src/infrastructure/ai_services/prompts/application_template_description.md` – nakazuje pominąć ogólne wytyczne redakcyjne, wspólne dla domyślnych instrukcji wszystkich szablonów.
- **Porty i adaptery:** `ApplicationTemplateDescriptionWriter` (`src/app/ports/application_templates.py`, adapter `src/infrastructure/ai_services/application_template_description_writer.py`) i `ApplicationTemplateDescriptionGenerationScheduler` (`src/app/ports/tasks.py`, adapter `PostgresApplicationTemplateDescriptionGenerationScheduler` w `src/infrastructure/tasks/application_templates.py`).
- **Wektor opisu:** kolumna `application_templates.description_vector`, liczona przez worker. Ręczna zmiana treści opisu (`PUT /api/application-templates/{templateId}`) czyści wektor.
- **Wyszukiwanie po opisie:** `GET /api/application-templates/published/search` (use case `SearchPublishedApplicationTemplates`, zalogowany użytkownik) przyjmuje zapytanie (`query`), minimalne podobieństwo (`threshold`) i filtr organizacji (`organizationId`, `suborganizationId`). Zwraca listę `PublishedApplicationTemplateSearchResult` (szablon i `score`, podobieństwo cosinusowe) posortowaną malejąco po podobieństwie. Szablony bez wektora opisu i nieopublikowane nie trafiają do wyników.
- **Obsługa błędów:** jak przy opisach regulacji – błąd ustawia `FAILED` i ponawia zadanie, po przekroczeniu `MAX_APPLICATION_TEMPLATE_DESCRIPTION_GENERATION_DELIVERIES` opis zostaje w statusie `FAILED`.
- **Frontend:** w edytorze szablonu (`ApplicationTemplateEditor`) pole „Opis szablonu” i przycisk „Wygeneruj opis przez AI”, który najpierw zapisuje szkic. W trakcie generowania formularz jest zablokowany, a strona szablonu odpytuje go do zakończenia. W formularzu wniosku (`GeneratePdfForm`) pole „Czego dotyczy wniosek?” wyszukuje szablony z domyślnym progiem istotności. Lista wyboru dzieli się wtedy na szablony pasujące (wg trafności, z podobieństwem) i pozostałe, a pod listą widać opis wybranego szablonu.

## 6. Modele

| Środowisko | Model | Uwagi |
|---|---|---|
| **GCP** | `google/gemini-3.5-flash-lite` (Vertex AI) | Serverless, płatność za tokeny. Multi-region `eu` (`aiplatform.eu.rep.googleapis.com`), dane przetwarzane tylko w UE. Wymaga roli `roles/aiplatform.user` (`scripts/cloud/cloud_inith.sh`). |
| **On-premise** | `OpenVINO/Qwen3.6-35B-A3B-int4-ov` (OVMS, `qwen-3.6-35b`) | `deploy/local/llm-service.yaml`. Mixture of experts, ok. 3B aktywnych parametrów. |
| **Lokalnie** | `OpenVINO/Qwen3.5-9B-int4-ov` (OVMS, `qwen-3.5-9b`) | `scripts/local/dev.py`, lżejszy model do testów. |

Wcześniej testowane: `OpenVINO/Qwen2.5-7B-Instruct-int4-ov`, `OpenVINO/gemma-2b-it-int8-ov` (brak roli `system`, ubogi korpus polski), `OpenVINO/gemma-4-E4B-it-int8-ov` (`Segmentation fault` w OVMS 2026.3), `google/gemma-4-26b-a4b-it-maas` i `OpenVINO/gemma-4-26b-a4b-it-int4-ov` (zastąpione przez Gemini 3.5 Flash-Lite i Qwen 3.6 35B A3B – lepsze wyniki).

## 7. Testowanie E2E (weryfikacja ręczna)

Instrukcja weryfikacji całego przepływu użytkownika (logowanie -> sprawa -> regulamin -> generowanie i pobranie DOCX) znajduje się w [docs/tests/manual_e2e_test.md](tests/manual_e2e_test.md).