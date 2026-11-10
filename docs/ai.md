# Moduł AI (LLM Service)

Moduł odpowiada za generowanie oficjalnych pism i wniosków studenckich w formacie DOCX na podstawie danych sprawy, studenta i powiązanych artykułów prawnych.

## 1. Architektura i integracja

- **Endpointy** (`src/core_service/framework/api/endpoints/cases.py`):
  - `POST /api/cases/{caseId}/applications` przyjmuje `NewApplication` (`src/core_service/application/dtos/applications.py`), zapisuje wniosek ze statusem `IN_PROGRESS`, zleca generowanie w tle i zwraca `202` z identyfikatorem wniosku. Dla nieistniejącego lub nieopublikowanego szablonu zwraca `404`, dla błędnych wartości pól `422` z listą nazw pól.
  - `GET /api/cases/{caseId}/applications` zwraca listę wniosków sprawy (`ApplicationRepresentation`) ze statusem generowania.
  - `GET /api/cases/{caseId}/applications/{applicationId}/download-url` zwraca presigned URL do pliku DOCX. Dla wniosku, który nie ma statusu `GENERATED`, zwraca `409`.
  - `DELETE /api/cases/{caseId}/applications/{applicationId}` usuwa wniosek i jego plik.
- **Szablon wniosku:** `NewApplication` zawiera `templateId` opublikowanego szablonu (zarządzanego przez administratora), opis sytuacji (`description`) i wartości pól szablonu (`fieldValues`), walidowane przez `ApplicationTemplate.validate_field_values` (`src/core_service/domain/entities/application_template.py`). Szablon dostarcza instrukcje dla AI (`instructions`), definicje pól i plik DOCX w object storage. Wniosek przechowuje `template_id` (po usunięciu szablonu `NULL`) i kopię nazwy szablonu (`template_name`).
- **Nazwa wniosku:** pole `name` w `ApplicationRepresentation`, nadawane przez LLM na podstawie opisu sytuacji (prompt `prompts/application_name.md`) i zapisywane razem ze statusem `GENERATED`. Do tego czasu ma wartość `null`, a frontend pokazuje w jej miejscu nazwę szablonu.
- **Status generowania:** `ApplicationGenerationStatus` (`src/core_service/domain/value_objects/applications.py`): `IN_PROGRESS`, `GENERATED`, `FAILED`.
- **Use case'y** (`src/core_service/application/use_cases/applications.py`): `AddApplication` (zapis i zlecenie zadania), `GenerateApplication` (wykonywany przez worker), `FailApplicationGeneration`, `ListApplications`, `GetApplicationDownloadUrl`, `DeleteApplication`.
- **Zadanie w tle:** `generate_application` (`src/core_service/framework/workers/applications.py`), zlecane przez `PostgresApplicationGenerationScheduler` (`src/core_service/infrastructure/tasks/applications.py`) w tej samej transakcji, w której zapisywany jest wniosek.
- **Porty:** `src/core_service/application/ports/applications.py` (`ApplicationWriter`, `ApplicationRenderer`).
- **Adaptery:**
  - `ApplicationWriter` (`src/core_service/infrastructure/ai_services/application_writer.py`) – renderuje prompt Jinja2 (`src/core_service/infrastructure/ai_services/prompts/application.md`) z instrukcjami szablonu i danymi wniosku i generuje treść przez `LlmChat`; osobnym wywołaniem (`write_name`, prompt `src/core_service/infrastructure/ai_services/prompts/application_name.md`) generuje nazwę wniosku.
  - `LlmChat` (`src/core_service/infrastructure/ai_services/llm_chat.py`) – klient czatu przez API zgodne z OpenAI: na GCP Vertex AI Model-as-a-Service, on-premise i lokalnie kontener `llm` z OVMS (port 8083 na hoście / 8080 w klastrze).
  - `DocxApplicationRenderer` (`src/core_service/infrastructure/docx/docx_renderer.py`) – renderuje szablon DOCX pobrany z object storage (w `SandboxedEnvironment`) z wartościami pól, `current_date` i `paragraphs` (stałe `CURRENT_DATE_TEMPLATE_VARIABLE` i `CONTENT_TEMPLATE_VARIABLE`) i zwraca go jako `bytes`.
  - `SqlaApplicationsRepository` (`src/core_service/infrastructure/relational_db/repositories/applications.py`) – tabela `applications` (wniosek należy do sprawy, usuwany kaskadowo razem z nią).
  - `S3ApplicationsStorage` (`src/core_service/infrastructure/object_storage/repository.py`) – pliki DOCX w object storage pod kluczem `applications/{id}`.
- **Konfiguracja:** Zmienne środowiskowe `LLM_SERVICE_*` (`src/core_service/shared/settings/ai_services.py`), wymagane jest tylko `LLM_SERVICE_URL` (bazowy URL API razem z `/v1`). Na GCP `LLM_SERVICE_USE_GOOGLE_AUTH=true` – klient uwierzytelnia się tokenem OAuth z Workload Identity (`src/core_service/infrastructure/ai_services/openai_client/google_auth.py`).

## 2. Szablony wniosków

Szablonami zarządza administrator, a zalogowany użytkownik widzi tylko szablony opublikowane. Use case'y dostają `Caller` i sprawdzają dostęp politykami z `src/core_service/domain/services/application_template_access.py` (`check_can_manage_application_templates`, `check_can_read_published_application_templates`).

- **Endpointy** (`src/core_service/framework/api/endpoints/application_templates.py`):
  - `GET /api/application-templates/published` zwraca opublikowane szablony (`PublishedApplicationTemplate`) z opisem i definicjami pól, bez instrukcji dla AI. Dostępny dla zalogowanego użytkownika.
  - `GET /api/application-templates/published/search` wyszukuje opublikowane szablony po nazwie, opcjonalnie wspomagane opisem – patrz [Opisy szablonów](#5-opisy-szablonow).
  - `GET /api/application-templates` i `GET /api/application-templates/{templateId}` zwracają szablony (`ApplicationTemplateRepresentation`) niezależnie od statusu.
  - `POST /api/application-templates` przyjmuje nazwę szablonu, zapisuje go z domyślnymi instrukcjami i zwraca presigned POST do wgrania pliku DOCX.
  - `POST /api/application-templates/{templateId}/confirm-upload` pobiera plik z object storage, odczytuje jego zmienne, tworzy z nich domyślne pola i zmienia status na `DRAFT`. Plik jest pobierany i analizowany poza transakcją, a zmianę statusu wykonuje `ApplicationTemplate.confirm_upload` na szablonie zablokowanym w transakcji (`SELECT ... FOR UPDATE`), więc przechodzi tylko szablon w statusie `NOT_UPLOADED`. Zwraca `409`, jeśli wgranie było już potwierdzone (także równolegle) albo pliku nie ma w object storage, i `422` dla niepoprawnego szablonu DOCX.
  - `PUT /api/application-templates/{templateId}` zapisuje nazwę, instrukcje, opis i konfigurację pól (`ApplicationTemplateDetailsData`). Tylko dla statusu `DRAFT` (inaczej `409`), dla niepoprawnej konfiguracji pól albo suborganizacji podanej bez organizacji zwraca `422`.
  - `POST /api/application-templates/{templateId}/publish` publikuje szablon w statusie `DRAFT` z niepustymi instrukcjami (`ApplicationTemplate.publish`, inaczej `409`).
  - `POST /api/application-templates/{templateId}/unpublish` przywraca opublikowanemu szablonowi status `DRAFT` (inaczej `409`).
  - `GET /api/application-templates/{templateId}/download-url` zwraca presigned URL do pliku DOCX (`409`, jeśli plik nie został wgrany). Frontend używa go do pobrania i podglądu szablonu.
  - `POST /api/application-templates/{templateId}/description-generation` zleca wygenerowanie opisu – patrz [Opisy szablonów](#5-opisy-szablonow).
  - `DELETE /api/application-templates/{templateId}` usuwa szablon i jego plik. Wygenerowane wnioski zostają, z `template_id` ustawionym na `NULL`.
- **Status:** `ApplicationTemplateStatus` (`src/core_service/domain/value_objects/application_templates.py`): `NOT_UPLOADED` → `DRAFT` ⇄ `PUBLISHED`. Przejścia i reguły szablonu są metodami encji `ApplicationTemplate` (`src/core_service/domain/entities/application_template.py`).
- **Plik DOCX:** szablon Jinja2 dla docxtpl. Musi zawierać zmienną `paragraphs` (treść wygenerowana przez LLM), `current_date` jest wypełniana automatycznie. Nagłówek, adresat, zwrot grzecznościowy, zwrot końcowy i podpis są częścią szablonu – LLM ich nie generuje. Pozostałe zmienne stają się polami szablonu (`ApplicationTemplate.confirm_upload`).
- **Pola** (`ApplicationTemplateField`): nazwa zmiennej, etykieta, typ (`TEXT`, `NUMBER`, `SELECT`, `DATE`), `required`, `passToAi`, opcjonalnie wartość domyślna, `pattern` i `options`. Reguły konfiguracji (`ApplicationTemplate.update_details` i `ApplicationTemplateField.check_config`):
  - zbiór pól musi odpowiadać zmiennym szablonu, bez duplikatów,
  - `pattern` (poprawny regex) tylko dla `TEXT`,
  - `options` wymagane dla `SELECT` i niedozwolone dla innych typów,
  - wartość domyślna musi przechodzić walidację pola.

  Wartości wpisane przez użytkownika waliduje `ApplicationTemplate.validate_field_values` (dla pojedynczego pola `ApplicationTemplateField.accepts`): `NUMBER` – skończona liczba, `SELECT` – jedna z opcji, `DATE` – format `dd.mm.yyyy`, `TEXT` – pełne dopasowanie do `pattern`.
- **Instrukcje dla AI:** Markdown edytowany przez administratora. Nowy szablon dostaje domyślne instrukcje z `src/core_service/infrastructure/ai_services/prompts/application_template_instructions.md`.
- **Use case'y** (`src/core_service/application/use_cases/application_templates.py`): `ListApplicationTemplates`, `GetApplicationTemplate`, `ListPublishedApplicationTemplates`, `AddApplicationTemplate`, `ConfirmApplicationTemplateUpload`, `UpdateApplicationTemplate`, `PublishApplicationTemplate`, `UnpublishApplicationTemplate`, `DeleteApplicationTemplate`, `GetApplicationTemplateDownloadUrl`.
- **Porty:** `src/core_service/application/ports/application_templates.py` (`ApplicationTemplateInspector`, `ApplicationTemplateInstructionsProvider`).
- **Adaptery:**
  - `DocxTemplateInspector` (`src/core_service/infrastructure/docx/template_inspector.py`) – odczytuje zmienne szablonu DOCX (w `SandboxedEnvironment`) i jego tekst (akapity i komórki tabel) na potrzeby opisu.
  - `PromptsApplicationTemplateInstructionsProvider` (`src/core_service/infrastructure/ai_services/application_template_instructions.py`) – domyślne instrukcje dla AI.
  - `SqlaApplicationTemplatesRepository` (`src/core_service/infrastructure/relational_db/repositories/application_templates.py`) – tabela `application_templates`.
  - `S3ApplicationTemplatesStorage` (`src/core_service/infrastructure/object_storage/repository.py`) – pliki DOCX w object storage pod kluczem `application_templates/{id}`.

## 3. Pipeline generowania wniosku

1. `core` zapisuje wniosek ze statusem `IN_PROGRESS` i w tej samej transakcji wstawia zadanie do kolejki Taskiq. Dane z formularza (`NewApplication`) trafiają wyłącznie do argumentów zadania, nie są zapisywane przy wniosku. Wiersz zadania jest usuwany po jego wykonaniu.
2. Worker pobiera szablon (instrukcje, pola i plik DOCX) oraz dokumenty przypięte do sprawy. Jeśli szablon został usunięty, nie jest już opublikowany albo wartości pól nie przechodzą `ApplicationTemplate.validate_field_values` dla jego aktualnej konfiguracji, wniosek dostaje status `FAILED`.
3. Renderowanie promptu w Jinja2: instrukcje szablonu, a po nich dane w blokach XML (`<dane_wniosku>` z polami oznaczonymi `passToAi`, `<opis_sytuacji>`, `<podstawa_prawna>`).
4. Inferencja LLM (generowanie merytorycznej treści uzasadnienia), a następnie osobne wywołanie generujące krótką nazwę wniosku.
5. Połączenie tekstu z szablonem DOCX i wygenerowanie dokumentu przez docxtpl.
6. Zapis nazwy, pliku w object storage i zmiana statusu na `GENERATED`. Frontend odpytuje listę wniosków, dopóki któryś ma status `IN_PROGRESS`, a gotowy plik pobiera przez presigned URL.

Obsługa błędów:
- Niedostępność LLM (`ServiceUnavailable`) ustawia status `FAILED` i ponawia zadanie z rosnącym opóźnieniem (`SmartRetryMiddleware`, opóźnienie realizowane przez `locked_until` w `task_messages`). Kolejna próba przywraca `IN_PROGRESS`.
- Po przekroczeniu limitu dostarczeń (`MAX_APPLICATION_GENERATION_DELIVERIES`) wniosek dostaje status `FAILED` bez kolejnej próby.
- Jeśli wniosek albo sprawa zostaną usunięte w trakcie generowania, worker kończy zadanie bez zapisu pliku.

## 4. Opisy regulacji

Administrator może zlecić wygenerowanie przez LLM ogólnego opisu regulacji (2–4 zdania: czego i kogo dotyczy dokument oraz jakie główne obszary reguluje, bez terminów, kwot i numerów jednostek). Opis ma posłużyć do wektorowego wyszukiwania właściwego aktu prawnego, dlatego razem z nim zapisywany jest jego wektor.

- **Status generowania:** `DescriptionStatus` (`src/core_service/domain/value_objects/descriptions.py`, wspólny dla regulacji i szablonów): `NOT_REQUESTED`, `IN_PROGRESS`, `GENERATED`, `FAILED`, zwracany jako `descriptionStatus` w `RegulationRepresentation`. Przejścia między statusami są metodami encji `Regulation` (`src/core_service/domain/entities/regulation.py`), wspólnymi z szablonami przez `Describable` (`src/core_service/domain/entities/describable.py`).
- **Zlecenie przy dodaniu:** `POST /api/regulations` z `generateDescription: true` (tylko administrator, inaczej `403`) zapisuje regulację ze statusem opisu `IN_PROGRESS`. `PrepareRegulation` po ustawieniu `PREPARED` wstawia w tej samej transakcji zadanie generowania opisu – opis powstaje z sekcji zapisanych podczas przygotowania, bez ponownej ekstrakcji.
- **Ponowne wygenerowanie:** `POST /api/regulations/{regulationId}/description-generation` (tylko administrator) ustawia `IN_PROGRESS` i zleca zadanie. Zwraca `409`, jeśli regulacja nie jest przygotowana albo opis jest już generowany.
- **Zadanie w tle:** `generate_regulation_description` (`src/core_service/framework/workers/regulations.py`), use case `GenerateRegulationDescription`. Wejście dla LLM (`create_description_source`, `src/core_service/domain/services/regulation_description.py`) to nazwa dokumentu, spis treści z nagłówków sekcji (rozdziały i tytuły jednostek redakcyjnych bez ich numerów, maks. `MAX_DESCRIPTION_HEADINGS`) i początek tekstu (maks. `MAX_DESCRIPTION_BEGINNING_CHARS` znaków). Prompt: `src/core_service/infrastructure/ai_services/prompts/regulation_description.md`.
- **Wektor opisu:** kolumna `regulations.description_vector`, liczona przez worker dla opisu z LLM, czyli na GCP przez instancję `embedding-batch`. Ręczna zmiana treści opisu (`PATCH /api/regulations/{regulationId}`, use case `UpdateRegulation`) przelicza wektor synchronicznie przez `embedding`, poza transakcją, tak samo jak przy szablonach. Gdy usługa jest niedostępna, zapis kończy się błędem `503`, a regulacja pozostaje bez zmian. Usunięcie opisu czyści wektor.
- **Wyszukiwanie po opisie:** `GET /api/regulations/search` (use case `SearchRegulations`) przyjmuje zapytanie w języku naturalnym (`query`) i minimalne podobieństwo (`threshold`) oraz te same filtry co lista regulacji (`scope`, `documentType`, `organizationId`, `suborganizationId`). Zapytanie jest zamieniane na wektor przez `embedding`, a wynik to lista `RegulationSearchResult` (regulacja i `score`, podobieństwo cosinusowe) posortowana malejąco po podobieństwie. Regulacje bez wektora opisu nie trafiają do wyników.
- **Obsługa błędów:** jak przy wnioskach – `ServiceUnavailable` ustawia `FAILED` i ponawia zadanie, po przekroczeniu `MAX_REGULATION_DESCRIPTION_GENERATION_DELIVERIES` opis zostaje w statusie `FAILED`.
- **Frontend:** checkbox „Wygeneruj opis przez AI” w dialogu dodawania regulacji i przycisk o tej samej nazwie w szczegółach przygotowanej regulacji (oba tylko dla administratora). W trakcie generowania pole opisu jest zablokowane, a lista regulacji jest odpytywana do zakończenia. Na stronie głównej formularz `RegulationsSearchForm` filtruje obie listy (publiczną i użytkownika) po opisie, pozwala wybrać próg istotności i kolejność (alfabetycznie albo wg trafności) i pokazuje podobieństwo przy każdej regulacji; parametry wyszukiwania są zapisywane w adresie strony.

## 5. Opisy szablonów

Administrator może zlecić wygenerowanie przez LLM krótkiego opisu szablonu wniosku (1–3 zdania: o co wnioskodawca prosi, do kogo kieruje pismo i w jakiej sytuacji z niego korzysta). Opis i jego wektor służą do wyszukiwania pasującego szablonu przez użytkownika, a sam opis jest też widoczny przy wyborze szablonu.

- **Status generowania:** `DescriptionStatus` (`src/core_service/domain/value_objects/descriptions.py`): `NOT_REQUESTED`, `IN_PROGRESS`, `GENERATED`, `FAILED`, zwracany jako `descriptionStatus` w `ApplicationTemplateRepresentation`. Przejścia między statusami są metodami encji `ApplicationTemplate` (`src/core_service/domain/entities/application_template.py`).
- **Zlecenie:** `POST /api/application-templates/{templateId}/description-generation` (use case `RegenerateApplicationTemplateDescription`, tylko administrator) ustawia `IN_PROGRESS` i w tej samej transakcji zleca zadanie. Zwraca `202`, `404` dla nieistniejącego szablonu i `409`, jeśli szablon nie jest w statusie `DRAFT` albo opis jest już generowany.
- **Zadanie w tle:** `generate_application_template_description` (`src/core_service/framework/workers/applications.py`), use case `GenerateApplicationTemplateDescription`. Wejście dla LLM (`ApplicationTemplate.create_description_source`, `src/core_service/domain/entities/application_template.py`) to nazwa szablonu, instrukcje dla AI (maks. `MAX_DESCRIPTION_INSTRUCTIONS_CHARS` znaków), etykiety pól i tekst pliku DOCX pobranego z object storage (maks. `MAX_DESCRIPTION_CONTENT_CHARS` znaków). Prompt: `src/core_service/infrastructure/ai_services/prompts/application_template_description.md` – nakazuje pominąć ogólne wytyczne redakcyjne, wspólne dla domyślnych instrukcji wszystkich szablonów.
- **Porty i adaptery:** `ApplicationTemplateDescriptionWriter` (`src/core_service/application/ports/application_templates.py`, adapter `src/core_service/infrastructure/ai_services/application_template_description_writer.py`) i `ApplicationTemplateDescriptionGenerationScheduler` (`src/core_service/application/ports/tasks.py`, adapter `PostgresApplicationTemplateDescriptionGenerationScheduler` w `src/core_service/infrastructure/tasks/application_templates.py`).
- **Wektor opisu:** kolumna `application_templates.description_vector`, liczona przez worker dla opisu z LLM. Ręczna zmiana treści opisu (`PUT /api/application-templates/{templateId}`, use case `UpdateApplicationTemplate`) przelicza wektor synchronicznie przez `embedding`, poza transakcją, więc na GCP zapis może czekać na cold start usługi. Gdy usługa jest niedostępna, zapis kończy się błędem `503`, a szablon pozostaje bez zmian. Usunięcie opisu czyści wektor.
- **Wyszukiwanie szablonów:** `GET /api/application-templates/published/search` (use case `SearchPublishedApplicationTemplates`, zalogowany użytkownik) przyjmuje zapytanie (`query`), flagę wyszukiwania wspomaganego AI (`aiAssisted`) i filtr organizacji (`organizationId`, `suborganizationId`). Zwraca opublikowane szablony (`PublishedApplicationTemplate`) w kolejności rankingu, bez score'ów.
  - **Fuzzy po nazwie** (domyślnie): `word_similarity` z `pg_trgm` na nazwach bez polskich znaków (`unaccent`), z progiem `TEMPLATE_NAME_SIMILARITY_THRESHOLD`, malejąco po podobieństwie.
  - **Hybryda** (`aiAssisted` i zapytanie zawierające spację, czyli co najmniej jedno skończone słowo – `is_semantic_search_query` w `src/core_service/domain/services/application_templates.py`): całe zapytanie jest embeddowane, a score to `TEMPLATE_NAME_SCORE_WEIGHT · podobieństwo nazwy + (1 − TEMPLATE_NAME_SCORE_WEIGHT) · podobieństwo cosinusowe opisu`. Szablon bez wektora opisu ma podobieństwo cosinusowe 0. Bez progu, zwracane jest `HYBRID_TEMPLATE_SEARCH_LIMIT` najlepszych wyników.
- **Obsługa błędów:** jak przy opisach regulacji – błąd ustawia `FAILED` i ponawia zadanie, po przekroczeniu `MAX_APPLICATION_TEMPLATE_DESCRIPTION_GENERATION_DELIVERIES` opis zostaje w statusie `FAILED`.
- **Frontend:** w edytorze szablonu (`ApplicationTemplateEditor`) pole „Opis szablonu” i przycisk „Wygeneruj opis przez AI”, który najpierw zapisuje szkic. W trakcie generowania formularz jest zablokowany, a strona szablonu odpytuje go do zakończenia. W formularzu wniosku (`GeneratePdfForm`) pole „Rodzaj wniosku” wysyła zapytanie po przerwie w pisaniu (domyślny `debounce` komponentu `el-select`), w trakcie wyszukiwania pokazuje stan ładowania, a szablony wyświetla w kolejności zwróconej przez backend. Gdy wyszukiwanie się nie powiedzie, pokazuje komunikat błędu i pełną listę szablonów. Przełącznik „Wyszukiwanie AI” włącza tryb hybrydowy. Opis szablonu jest widoczny w podpowiedzi przy opcji.

## 6. Modele

| Środowisko | Model | Uwagi |
|---|---|---|
| **GCP** | `google/gemini-3.5-flash-lite` (Vertex AI) | Serverless, płatność za tokeny. Multi-region `eu` (`aiplatform.eu.rep.googleapis.com`), dane przetwarzane tylko w UE. Wymaga roli `roles/aiplatform.user` (`scripts/cloud/cloud_inith.sh`). |
| **On-premise** | `OpenVINO/Qwen3.6-35B-A3B-int4-ov` (OVMS, `qwen-3.6-35b`) | `deploy/local/llm.yaml`. Mixture of experts, ok. 3B aktywnych parametrów. |
| **Lokalnie** | `OpenVINO/Qwen3.5-9B-int4-ov` (OVMS, `qwen-3.5-9b`) | `apps/core/scripts/dev.py`, lżejszy model do testów. |

Wcześniej testowane: `OpenVINO/Qwen2.5-7B-Instruct-int4-ov`, `OpenVINO/gemma-2b-it-int8-ov` (brak roli `system`, ubogi korpus polski), `OpenVINO/gemma-4-E4B-it-int8-ov` (`Segmentation fault` w OVMS 2026.3), `google/gemma-4-26b-a4b-it-maas` i `OpenVINO/gemma-4-26b-a4b-it-int4-ov` (zastąpione przez Gemini 3.5 Flash-Lite i Qwen 3.6 35B A3B – lepsze wyniki).

## 7. Testowanie E2E (weryfikacja ręczna)

Instrukcja weryfikacji całego przepływu użytkownika (logowanie -> sprawa -> regulamin -> generowanie i pobranie DOCX) znajduje się w [docs/tests/manual_e2e_test.md](tests/manual_e2e_test.md).