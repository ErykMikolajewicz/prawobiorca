import os

from jinja2 import Environment, FileSystemLoader

# Dynamicznie ustalamy ścieżkę do katalogu resources/prompts/ relative do tego pliku
# os.path.dirname(os.path.abspath(__file__)) -> app/shared/config/
# Drugi dirname -> app/shared/
SHARED_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROMPTS_DIR = os.path.join(SHARED_DIR, "resources", "prompts")
TEMPLATES_DIR = os.path.join(SHARED_DIR, "resources", "templates")


# Konfigurujemy środowisko Jinja2
# autoescape=False, ponieważ generujemy czysty tekst (Markdown) dla LLM, a nie HTML.
jinja_env = Environment(
    loader=FileSystemLoader(PROMPTS_DIR),
    autoescape=False,  # noqa: S701
    trim_blocks=True,
    lstrip_blocks=True,
)

jinja_html_env = Environment(
    loader=FileSystemLoader(TEMPLATES_DIR),
    autoescape=True,
    trim_blocks=True,
    lstrip_blocks=True,
)
