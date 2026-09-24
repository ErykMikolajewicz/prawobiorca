from typing import Protocol

from src.app.dtos.user import StudentData


class LLMClient(Protocol):
    async def generate_text(self, system_prompt: str, user_prompt: str) -> str:
        """
        generowanie gotowego tekstu na podstawie zawartości podanego promptu.
        """
        ...


class PDFRenderer(Protocol):
    async def render_pdf(
        self,
        applicant_data: StudentData,
        recipient_info: str,
        title: str,
        content: str,
        output_path: str,
    ) -> str:
        """
        zapisywanie wygenerowanego pdfa na dysku pod wskazanym adresem.
        """
        ...
