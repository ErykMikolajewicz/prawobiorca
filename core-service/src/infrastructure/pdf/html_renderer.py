from datetime import datetime
from pathlib import Path

import anyio
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML

from src.app.dtos.applications import NewApplication

PDF_RESOURCES_DIR = Path(__file__).parent

templates_env = Environment(
    loader=FileSystemLoader(PDF_RESOURCES_DIR / "templates"),
    autoescape=True,
    trim_blocks=True,
    lstrip_blocks=True,
)


class HtmlApplicationRenderer:
    async def render(self, new_application: NewApplication, content: str) -> bytes:
        html_content = templates_env.get_template("application.html").render(
            current_date=datetime.now().strftime("%d.%m.%Y"),
            application=new_application,
            content=content,
        )
        html = HTML(string=html_content, base_url=PDF_RESOURCES_DIR.as_uri())

        return await anyio.to_thread.run_sync(html.write_pdf)
