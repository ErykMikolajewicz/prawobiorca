import asyncio
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.request
from typing import Any, Dict, List, Tuple

import jinja2
from dotenv import load_dotenv

load_dotenv()

# dodawanie katalogu głównego do ścieżki wyszukiwania modułów
CORE_SERVICE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
REPO_ROOT = os.path.dirname(CORE_SERVICE_DIR)
sys.path.append(CORE_SERVICE_DIR)

from src.app.dtos.user import StudentData  # noqa: E402
from src.infrastructure.ai.openvino_client import OpenVINOClient  # noqa: E402
from src.infrastructure.pdf.html_renderer import HTMLToPDFRenderer  # noqa: E402

# KONFIGURACJA BENCHMARKU (DLA URUCHOMIENIA Z IDE LUB TERMINALA)

# 1. Silnik AI: "openvino" lub "ollama" (lub flaga w terminalu: --openvino / --ollama)
DEFAULT_LLM_PROVIDER = "openvino"

# 2. Nazwa modelu (DLA IDE): wpisz tutaj model, np. "gemma-2b-it" lub "qwen-2.5-3b-it"
#    Jeśli None: model zostanie pobrany z pliku .env lub flagi --model w CLI
CUSTOM_MODEL_NAME = "qwen-2.5-7b-it"

# 3. Czyszczenie starych wyników: zmień na True, aby skasować folder benchmark_results przed startem
CLEANUP_OLD_RESULTS = True


if "--ollama" in sys.argv:
    LLM_PROVIDER = "ollama"
elif "--openvino" in sys.argv:
    LLM_PROVIDER = "openvino"
else:
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", DEFAULT_LLM_PROVIDER).lower()

CLI_MODEL_NAME = CUSTOM_MODEL_NAME
for i, arg in enumerate(sys.argv):
    if arg == "--model" and i + 1 < len(sys.argv):
        CLI_MODEL_NAME = sys.argv[i + 1]
        break

print(f"[KONFIGURACJA] Wybrany silnik AI: {LLM_PROVIDER.upper()}")
if CLI_MODEL_NAME:
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


def get_openvino_downloaded_models() -> List[str]:
    if not shutil.which("podman"):
        return []
    try:
        res = subprocess.run(
            ["podman", "run", "--rm", "-v", "llm-model:/models", "alpine", "ls", "-1", "/models/OpenVINO"],
            capture_output=True,
            text=True,
            timeout=5,
        )
        if res.returncode == 0:
            return [d.strip() for d in res.stdout.splitlines() if d.strip() and not d.endswith(".lfswip")]
    except Exception:
        pass
    return []


def ensure_openvino_container_ready(model_name: str) -> str:
    base_url = os.getenv("OPENVINO_BASE_URL", "http://localhost:8083/v1")
    running_models = get_openvino_running_models(base_url)

    # Jeśli żądany model już działa na serwerze
    if model_name in running_models:
        print(f"[OPENVINO] Serwer na {base_url} działa i model '{model_name}' jest gotowy.\n")
        return model_name

    # Sprawdzenie pobranych modeli w wolumenie Podmana
    downloaded_dirs = get_openvino_downloaded_models()

    dir_to_model = {
        "gemma-2b-it-int8-ov": "gemma-2b-it",
        "Qwen2.5-7B-Instruct-int4-ov": "qwen-2.5-7b-it",
        "Qwen2.5-Coder-3B-Instruct-int4-ov": "qwen-2.5-coder-3b-it",
    }
    model_to_dir = {v: k for k, v in dir_to_model.items()}

    expected_dir = model_to_dir.get(model_name, model_name)
    is_downloaded = expected_dir in downloaded_dirs

    # Jeśli wybrany model nie jest pobrany lokalnie, szukamy zainstalowanego fallbacku
    if not is_downloaded:
        fallback_model = None
        if running_models:
            fallback_model = running_models[0]
        else:
            for d in downloaded_dirs:
                if d in dir_to_model:
                    fallback_model = dir_to_model[d]
                    break

        if fallback_model:
            print(f"\n[OPENVINO INFO] Wybrany model '{model_name}' nie jest jeszcze pobrany lokalnie.")
            print(f"[OPENVINO INFO] Używam już zainstalowanego i gotowego modelu: '{fallback_model}'.\n")
            model_name = fallback_model
            if model_name in running_models:
                return model_name

    if not shutil.which("podman"):
        print("[OSTRZEŻENIE] Brak narzędzia 'podman' w systemie. Uruchom serwer OpenVINO ręcznie.")
        return model_name

    print(f"[OPENVINO] Port 8083 nie odpowiada lub brak modelu '{model_name}'. Przygotowanie kontenera w Podmanie...")

    if "7b" in model_name.lower():
        source_model = os.getenv("OPENVINO_SOURCE_MODEL", "OpenVINO/Qwen2.5-7B-Instruct-int4-ov")
    elif "gemma" in model_name.lower():
        source_model = "OpenVINO/gemma-2b-it-int8-ov"
    else:
        source_model = os.getenv("OPENVINO_SOURCE_MODEL", f"OpenVINO/{model_name}")

    ps_res = subprocess.run(["podman", "ps", "-a", "--format", "{{.Names}}"], capture_output=True, text=True)
    existing_containers = ps_res.stdout.splitlines()

    if "llm-service" in existing_containers:
        inspect_res = subprocess.run(
            ["podman", "inspect", "llm-service", "--format", "{{.Args}}"],
            capture_output=True,
            text=True,
        )
        if f"--model_name={model_name}" in inspect_res.stdout:
            print("[OPENVINO] Uruchamianie istniejącego kontenera 'llm-service'...")
            subprocess.run(["podman", "start", "llm-service"], check=False, capture_output=True)
        else:
            print(f"[OPENVINO] Kontener 'llm-service' miał inny model. Przeładowywanie na '{model_name}'...")
            subprocess.run(["podman", "rm", "-f", "llm-service"], check=False, capture_output=True)
            existing_containers.remove("llm-service")

    if "llm-service" not in existing_containers:
        dri_args = "--device /dev/dri" if os.path.exists("/dev/dri") else ""
        cmd = (
            f"podman run -d --name llm-service -p 127.0.0.1:8083:8080 {dri_args} -v llm-model:/models "
            f"docker.io/openvino/model_server:2026.3-gpu "
            f"--source_model={source_model} --model_name={model_name} "
            f"--model_repository_path=/models --task=text_generation --target_device=AUTO --rest_port=8080"
        )
        subprocess.run(cmd, shell=True, check=True)

    print(f"[OPENVINO] Oczekiwanie na pełną inicjalizację modelu '{model_name}'...")
    for i in range(60):
        time.sleep(2)
        if model_name in get_openvino_running_models(base_url):
            print(f"[OPENVINO] Sukces! Serwer OpenVINO i model '{model_name}' są gotowe do pracy.\n")
            return model_name
        if i > 0 and i % 5 == 0:
            print(f"  ... oczekiwanie na załadowanie modelu ({i * 2}s)...")

    print("[OSTRZEŻENIE] Przekroczono limit czasu oczekiwania na start serwera. Rozpoczynam testy...\n")
    return model_name



def _prepare_prompts(
    case: Dict[str, Any],
    student_data: StudentData,
    prompt_content: str,
    is_jinja_template: bool,
    template: jinja2.Template | None,
) -> Tuple[str, str]:
    articles_text = "\n\n".join([f"Paragraf {i + 1}:\n{art}" for i, art in enumerate(case["articles"])])

    if is_jinja_template and template:
        system_prompt = template.render(
            **student_data.model_dump(),
            situation_description=case["situation"],
            pinned_articles=case["articles"],
        )
        user_message = "Napisz formalne pismo na podstawie powyższych informacji."
    else:
        system_prompt = prompt_content
        user_message = f"""Dane studenta:
- Imię i nazwisko: {student_data.user_name}
- Numer albumu: {student_data.student_id}

Opis sytuacji studenta:
{case["situation"]}

Znalezione paragrafy regulaminu:
{articles_text}

Napisz formalne pismo na podstawie powyższych informacji."""

    return system_prompt, user_message


async def test_prompt(
    prompt_content: str,
    prompt_version: str,
    backend: str = "ollama",
    is_jinja_template: bool = False,
    temperature: float = 0.8,
    model_override: str | None = None,
) -> List[Dict[str, Any]]:
    pdf_renderer = HTMLToPDFRenderer()

    # optymalizacja: kompilacja szablonu tylko raz przed pętlą
    template = jinja2.Template(prompt_content) if is_jinja_template else None
    prompt_summaries = []

    if backend == "ollama":
        try:
            import ollama
        except ImportError:
            print("[BŁĄD] Wybrano backend Ollama, ale biblioteka 'ollama' nie jest zainstalowana w środowisku.")
            sys.exit(1)
        model_name = model_override or os.getenv("OLLAMA_MODEL_NAME", "qwen2.5:3b")
        ollama_client = ollama.AsyncClient()
    else:
        model_name = model_override or os.getenv("OPENVINO_MODEL_NAME", "qwen-2.5-3b-it")
        openvino_client = OpenVINOClient(model_name=model_name, temperature=temperature)

    for case in TEST_CASES:
        student_info = case.get("student", DEFAULT_STUDENT)
        test_name = f"{prompt_version}_{case['id']}"
        student_data = StudentData(**student_info)

        system_prompt, user_message = _prepare_prompts(case, student_data, prompt_content, is_jinja_template, template)

        print(f"[{test_name}] Generowanie treści przez AI...")
        start_time = time.perf_counter()
        generation_time = 0.0
        content = ""
        error_msg = None

        try:
            if backend == "ollama":
                response = await ollama_client.chat(
                    model=model_name,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message},
                    ],
                    options={"temperature": temperature},
                )
                content = response["message"]["content"].strip()
            else:
                # openvino client ma własną obsługę temperatury zainicjalizowaną w konstruktorze
                content = await openvino_client.generate_text(system_prompt, user_message)

            end_time = time.perf_counter()
            generation_time = end_time - start_time
            print(f"[{test_name}] Czas generowania wniosku przez AI: {generation_time:.2f} s")
        except Exception as e:
            error_msg = str(e)
            print(f"[{test_name}] Błąd podczas generowania: {error_msg}")
            content = f"Wystąpił błąd podczas generowania:\n{error_msg}"

        # zapisywanie jako tekst w folderze wyników benchmarku
        os.makedirs(BENCHMARK_DIR, exist_ok=True)
        with open(os.path.join(BENCHMARK_DIR, f"{test_name}.md"), "w", encoding="utf-8") as f:
            f.write(content)

        # renderowanie pdfa przy użyciu adaptera fpdf
        if not error_msg:
            try:
                pdf_path = os.path.join(BENCHMARK_DIR, f"{test_name}.pdf")
                await pdf_renderer.render_pdf(
                    applicant_data=student_data,
                    recipient_info="Sz. P. Dziekan\nPolitechnika Wrocławska",
                    title=case["title"],
                    content=content,
                    output_path=pdf_path,
                )
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
                "backend": backend,
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

    global CLI_MODEL_NAME
    if LLM_PROVIDER == "openvino":
        target_model = CLI_MODEL_NAME or os.getenv("OPENVINO_MODEL_NAME", "qwen-2.5-7b-it")
        CLI_MODEL_NAME = ensure_openvino_container_ready(target_model)


    test_configs = [
        {
            "path": "core-service/src/shared/resources/prompts/archive/prompts_v1.md",
            "version": "V1_oryginalny",
            "is_jinja": False,
            "temp": 0.8,
        },
        {
            "path": "core-service/src/shared/resources/prompts/archive/prompts_v2.md",
            "version": "V2_drugi",
            "is_jinja": False,
            "temp": 0.8,
        },
        {
            "path": "core-service/src/shared/resources/prompts/system_prompt.md",
            "version": "V3_optymalny_szablon",
            "is_jinja": True,
            "temp": 0.8,
        },
        {
            "path": "core-service/src/shared/resources/prompts/system_prompt.md",
            "version": "V3_optymalny_szablon_temp_0.7",
            "is_jinja": True,
            "temp": 0.7,
        },
        {
            "path": "core-service/src/shared/resources/prompts/archive/prompts_v3.md",
            "version": "V4_temp_0.8_domyslna",
            "is_jinja": True,
            "temp": 0.8,
        },
        {
            "path": "core-service/src/shared/resources/prompts/archive/prompts_v3.md",
            "version": "V4_temp_0.2_sztywna",
            "is_jinja": True,
            "temp": 0.2,
        },
    ]

    print(f"Rozpoczynam testowanie {len(test_configs)} promptów dla {len(TEST_CASES)} różnych przypadków...\n")

    benchmark_summary = []

    for config in test_configs:
        prompt_file = os.path.join(REPO_ROOT, config["path"]) if not os.path.isabs(config["path"]) else config["path"]
        with open(prompt_file, "r", encoding="utf-8") as f:
            prompt_content = f.read()

        # uruchamianie testów sekwencyjnie
        summaries = await test_prompt(
            prompt_content,
            config["version"],
            backend=LLM_PROVIDER,
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
