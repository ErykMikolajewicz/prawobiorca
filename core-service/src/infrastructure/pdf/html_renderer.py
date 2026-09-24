import os
from datetime import datetime

import anyio

from src.app.dtos.user import StudentData
from src.app.interfaces.pdf_generation import PDFRenderer
from src.shared.config.jinja import jinja_html_env

# obliczanie ścieżki do folderu resources na potrzeby weasyprint base_url
INFRASTRUCTURE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
APP_DIR = os.path.dirname(INFRASTRUCTURE_DIR)
RESOURCES_DIR = os.path.join(APP_DIR, "shared", "resources")


class HTMLToPDFRenderer(PDFRenderer):
    async def render_pdf(
        self,
        applicant_data: StudentData,
        recipient_info: str,
        title: str,
        content: str,
        output_path: str,
    ) -> str:
        """
        Kompiluje treść wniosku oraz dane studenta do profesjonalnego pliku PDF
        przy użyciu szablonu HTML i silnika WeasyPrint.
        """
        current_date = datetime.now().strftime("%d.%m.%Y")

        # renderowanie szablonu za pomocą Jinja
        try:
            template = jinja_html_env.get_template("application_template.html")
            html_content = template.render(
                current_date=current_date,
                student=applicant_data,
                recipient_info=recipient_info,
                title=title,
                content=content,
            )
        except Exception as e:
            raise ValueError(f"Nie udało się załadować lub wyrenderować szablonu HTML: {e}")

        # inicjalizacja katalogu docelowego
        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)

        # zapis do PDF z użyciem biblioteki WeasyPrint
        base_url = f"file:///{os.path.abspath(RESOURCES_DIR).replace(os.sep, '/')}"

        def _generate_sync():
            from weasyprint import HTML

            HTML(string=html_content, base_url=base_url).write_pdf(output_path)

        await anyio.to_thread.run_sync(_generate_sync)

        return output_path
