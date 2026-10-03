import asyncio
import json
import os
import shutil
import sys
import time
import urllib.request
from dataclasses import asdict
from typing import Any, Dict, List, Tuple

import jinja2

# dodawanie katalogu głównego do ścieżki wyszukiwania modułów
CORE_SERVICE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(CORE_SERVICE_DIR)

# Automatyczne przełączenie do core-service/.venv, jeśli uruchomiono z poziomu root venv w IDE
CORE_VENV_PYTHON = os.path.join(
    CORE_SERVICE_DIR,
    ".venv",
    "Scripts" if sys.platform == "win32" else "bin",
    "python.exe" if sys.platform == "win32" else "python",
)
if os.path.exists(CORE_VENV_PYTHON) and os.path.abspath(sys.executable) != os.path.abspath(CORE_VENV_PYTHON):
    try:
        import openai  # noqa: F401
    except ImportError:
        import subprocess

        sys.exit(subprocess.run([CORE_VENV_PYTHON, *sys.argv]).returncode)

from src.app.dtos.applications import NewApplication  # noqa: E402
from src.infrastructure.ai_services.llm_chat import LlmChat  # noqa: E402
from src.infrastructure.ai_services.openai_client.connection import client  # noqa: E402
from src.infrastructure.pdf.html_renderer import HtmlApplicationRenderer  # noqa: E402
from src.shared.settings.ai_services import llm_service_settings  # noqa: E402

# KONFIGURACJA BENCHMARKU (DLA URUCHOMIENIA Z IDE LUB TERMINALA)

# 1. Nazwa modelu (DLA IDE): wpisz tutaj model, np. "gemma-2b-it" lub "qwen-2.5-7b-it"
#    Jeśli None: model zostanie pobrany z pliku .env lub flagi --model w CLI
CUSTOM_MODEL_NAME = None

# 2. Czyszczenie starych wyników: zmień na True, aby skasować folder benchmark_results przed startem
CLEANUP_OLD_RESULTS = True

SKIP_PDF = "--skip-pdf" in sys.argv

CLI_MODEL_NAME = CUSTOM_MODEL_NAME or llm_service_settings.MODEL_NAME
for i, arg in enumerate(sys.argv):
    if arg == "--model" and i + 1 < len(sys.argv):
        CLI_MODEL_NAME = sys.argv[i + 1]
        break

print(f"[KONFIGURACJA] Wybrany model: {CLI_MODEL_NAME}")

# wczytywanie przypadków testowych z pliku json
TEST_CASES_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "test_cases.json")
try:
    with open(TEST_CASES_PATH, "r", encoding="utf-8") as f:
        test_data = json.load(f)
        TEST_CASES = test_data.get("cases", [])
        DEFAULT_STUDENT = test_data.get("default_student", {})
except FileNotFoundError:
    print(f"[BŁĄD] Nie znaleziono pliku: {TEST_CASES_PATH}. Utwórz go przed uruchomieniem testów.")
    sys.exit(1)
except json.JSONDecodeError as e:
    print(f"[BŁĄD] Plik test_cases.json zawiera nieprawidłowy format JSON: {e}")
    sys.exit(1)

BENCHMARK_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "benchmark_results"))


def get_openvino_running_models(base_url: str) -> List[str]:
    try:
        req = urllib.request.Request(f"{base_url.rstrip('/')}/models", headers={"User-Agent": "compare-prompts"})
        with urllib.request.urlopen(req, timeout=1.0) as resp:
            if resp.status == 200:
                data = json.loads(resp.read().decode())
                return [m.get("id") for m in data.get("data", []) if m.get("id")]
    except Exception:
        pass
    return []


def ensure_openvino_container_ready(model_name: str) -> str:
    base_url = llm_service_settings.URL
    running_models = get_openvino_running_models(base_url)

    if model_name in running_models or any(model_name in r for r in running_models):
        print(f"[OPENVINO] Serwer na {base_url} działa i model '{model_name}' jest gotowy.\n")
        return model_name

    if running_models:
        print(f"[OPENVINO] Serwer działa, ale nie zgłasza '{model_name}' (dostępne modele: {running_models}).\n")
        return model_name

    print(f"\n[OPENVINO] Serwer na {base_url} nie odpowiada.")
    print("Upewnij się, że uruchomiono środowisko deweloperskie (np. 'just dev' lub 'python scripts/local/dev.py').\n")
    return model_name


def _prepare_prompts(
    case: Dict[str, Any],
    new_application: NewApplication,
    prompt_content: str,
    is_jinja_template: bool,
    template: jinja2.Template | None,
) -> Tuple[str, str]:
    articles_text = "\n\n".join([f"Paragraf {i + 1}:\n{art}" for i, art in enumerate(case.get("articles", []))])

    if is_jinja_template and template:
        system_prompt = template.render(
            **asdict(new_application),
            situation_description=new_application.description,
            pinned_articles=case.get("articles", []),
        )
        user_message = "Napisz formalne pismo na podstawie powyższych informacji."
    else:
        system_prompt = prompt_content
        user_message = f"""Dane studenta:
- Imię i nazwisko: {new_application.user_name}
- Numer albumu: {new_application.student_id}

Opis sytuacji studenta:
{new_application.description}

Znalezione paragrafy regulaminu:
{articles_text}

Napisz formalne pismo na podstawie powyższych informacji."""

    return system_prompt, user_message


async def test_prompt(
    prompt_content: str,
    prompt_version: str,
    is_jinja_template: bool = False,
    temperature: float = 0.8,
    model_override: str | None = None,
) -> List[Dict[str, Any]]:
    pdf_renderer = HtmlApplicationRenderer() if not SKIP_PDF else None

    # optymalizacja: kompilacja szablonu tylko raz przed pętlą
    template = jinja2.Template(prompt_content) if is_jinja_template else None
    prompt_summaries = []

    model_name = model_override or llm_service_settings.MODEL_NAME
    llm_chat = LlmChat(
        client=client,
        model_name=model_name,
        temperature=temperature,
        top_p=llm_service_settings.TOP_P,
        max_tokens=llm_service_settings.MAX_TOKENS,
    )

    for case in TEST_CASES:
        student_info = case.get("student", DEFAULT_STUDENT)
        test_name = f"{prompt_version}_{case['id']}"
        new_application = NewApplication(**student_info, description=case.get("situation", ""))

        system_prompt, user_message = _prepare_prompts(
            case, new_application, prompt_content, is_jinja_template, template
        )

        print(f"[{test_name}] Generowanie treści przez AI...")
        start_time = time.perf_counter()
        generation_time = 0.0
        content = ""
        error_msg = None

        try:
            content = await llm_chat.generate_text(system_prompt, user_message)

            end_time = time.perf_counter()
            generation_time = end_time - start_time
            print(f"[{test_name}] Czas generowania wniosku przez AI: {generation_time:.2f} s")
        except Exception as e:
            error_msg = repr(e)
            print(f"[{test_name}] Błąd podczas generowania: {error_msg}")
            content = f"Wystąpił błąd podczas generowania:\n{error_msg}"

        # zapisywanie jako tekst w folderze wyników benchmarku
        os.makedirs(BENCHMARK_DIR, exist_ok=True)
        with open(os.path.join(BENCHMARK_DIR, f"{test_name}.md"), "w", encoding="utf-8") as f:
            f.write(content)

        # renderowanie pdfa przy użyciu adaptera weasyprint / html
        if not error_msg and pdf_renderer:
            try:
                pdf_path = os.path.join(BENCHMARK_DIR, f"{test_name}.pdf")
                pdf = await pdf_renderer.render(new_application, content)
                with open(pdf_path, "wb") as f:
                    f.write(pdf)
                print(f"[{test_name}] Zapisano PDF: {pdf_path}")
            except Exception as e:
                print(f"[{test_name}] Błąd podczas renderowania PDF: {e}")

        # zbieranie statystyk
        prompt_summaries.append(
            {
                "test_name": test_name,
                "case_id": case["id"],
                "prompt_version": prompt_version,
                "temperature": temperature,
                "model_name": model_name,
                "generation_time_seconds": round(generation_time, 2) if not error_msg else 0.0,
                "content_length_chars": len(content),
                "error": error_msg,
            }
        )

    return prompt_summaries


async def main():
    if CLEANUP_OLD_RESULTS:
        print("Czyszczenie starych wyników z folderu benchmark_results...")
        if os.path.exists(BENCHMARK_DIR):
            shutil.rmtree(BENCHMARK_DIR)

    os.makedirs(BENCHMARK_DIR, exist_ok=True)

    ensure_openvino_container_ready(CLI_MODEL_NAME)

    test_configs = [
        {
            "path": "scripts/prompts_benchmark/archive/prompts_v1.md",
            "version": "V1_oryginalny",
            "is_jinja": False,
            "temp": 0.8,
        },
        {
            "path": "scripts/prompts_benchmark/archive/prompts_v2.md",
            "version": "V2_drugi",
            "is_jinja": False,
            "temp": 0.8,
        },
        {
            "path": "src/infrastructure/ai_services/prompts/application.md",
            "version": "V3_optymalny_szablon",
            "is_jinja": True,
            "temp": 0.8,
        },
        {
            "path": "src/infrastructure/ai_services/prompts/application.md",
            "version": "V3_optymalny_szablon_temp_0.7",
            "is_jinja": True,
            "temp": 0.7,
        },
        {
            "path": "scripts/prompts_benchmark/archive/prompts_v3.md",
            "version": "V4_temp_0.8_domyslna",
            "is_jinja": True,
            "temp": 0.8,
        },
        {
            "path": "scripts/prompts_benchmark/archive/prompts_v3.md",
            "version": "V4_temp_0.2_sztywna",
            "is_jinja": True,
            "temp": 0.2,
        },
    ]

    print(f"Rozpoczynam testowanie {len(test_configs)} promptów dla {len(TEST_CASES)} różnych przypadków...\n")

    benchmark_summary = []

    for config in test_configs:
        prompt_file = os.path.join(CORE_SERVICE_DIR, config["path"])
        with open(prompt_file, "r", encoding="utf-8") as f:
            prompt_content = f.read()

        # uruchamianie testów sekwencyjnie
        summaries = await test_prompt(
            prompt_content,
            config["version"],
            is_jinja_template=config["is_jinja"],
            temperature=config["temp"],
            model_override=CLI_MODEL_NAME,
        )
        benchmark_summary.extend(summaries)

    # zapisywanie podsumowania do pliku json
    summary_path = os.path.join(BENCHMARK_DIR, "summary.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(benchmark_summary, f, indent=2, ensure_ascii=False)

    print(f"\nGotowe! Wygenerowano pliki PDF oraz MD, a podsumowanie zapisano do {summary_path}")


if __name__ == "__main__":
    asyncio.run(main())
