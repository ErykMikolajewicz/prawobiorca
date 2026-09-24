from uuid import UUID

from src.app.dtos.user import StudentData
from src.app.interfaces.cases import CaseDocumentsRepository
from src.app.interfaces.pdf_generation import LLMClient, PDFRenderer
from src.app.interfaces.relational import SessionMaker
from src.app.use_cases.cases import ListCaseDocuments
from src.domain.exceptions.cases import LLMGenerationError
from src.shared.config.jinja import jinja_env


class GenerateCasePDF:
    def __init__(
        self,
        session_maker: SessionMaker,
        case_documents_repo: CaseDocumentsRepository,
        llm_client: LLMClient,
        pdf_renderer: PDFRenderer,
    ):
        self.session_maker = session_maker
        self.case_articles_repo = case_documents_repo
        self.llm_client = llm_client
        self.pdf_renderer = pdf_renderer

    async def execute(
        self,
        case_id: UUID,
        description: str,
        student_data: StudentData,
        output_path: str,
    ) -> str:
        # pobieranie artykułów z regulaminu, które pasują do tej sprawy
        list_case_articles = ListCaseDocuments(self.session_maker, self.case_articles_repo)
        articles = await list_case_articles.execute(student_data.user_id, case_id)
        pinned_texts = [f"{a.presentation_name}: {a.content}" for a in articles]

        # wczytywanie szablonu promptu z pliku i wklejanie do niego danych studenta
        try:
            template = jinja_env.get_template("system_prompt.md")
            system_prompt = template.render(
                user_name=student_data.user_name,
                student_id=student_data.student_id,
                situation_description=description,
                pinned_articles=pinned_texts,
            )
        except Exception as e:
            raise LLMGenerationError(f"Błąd ładowania lub renderowania szablonu promptu: {e}") from e

        # generowanie treści wniosku przez sztuczną inteligencję
        user_prompt = "Napisz formalne pismo na podstawie powyższych informacji."
        content = await self.llm_client.generate_text(system_prompt=system_prompt, user_prompt=user_prompt)

        # na sam koniec wrzucanie wszystkiego do pdfa
        recipient_info = "Sz. P. Dziekan\nPolitechnika Wrocławska"
        title = "WNIOSEK"

        pdf_path = await self.pdf_renderer.render_pdf(
            applicant_data=student_data,
            recipient_info=recipient_info,
            title=title,
            content=content,
            output_path=output_path,
        )

        return pdf_path
