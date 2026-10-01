import json
import re
from pathlib import Path
from unittest.mock import patch

import pytest

from src.domain.value_objects import regulations as regulations_module
from src.domain.value_objects.legal_units import RegulationElement, UsefulLabels
from src.domain.value_objects.regulations import RegulationAct

DATA_DIR = Path(__file__).parents[3] / "data"

ACT_FIXTURE = "ustawa-nauka_slice_30-31"

RECTOR_TASKS_FIXTURE = "ustawa-nauka_slice_12-13"

PROMOTION_DATABASE_FIXTURE = "ustawa-nauka_slice_209-210"

STUDY_REGULATIONS_FIXTURE = "pwr-regulamin_2025_slice_5-6"

SUBSECTION_OR_POINT_START_PATTERN = re.compile(r"^\d+[a-z]*[.)]\s")

LETTER_START_PATTERN = re.compile(r"^[a-z]\)\s")

ARTICLE_NUMBER_PATTERN = re.compile(r"Art\. (\w+)$")

CHUNK_MAX_TOKENS = 60


class WordTokenizer:
    max_tokens = 2048

    def count_tokens(self, text: str) -> int:
        return len(text.split())


@pytest.fixture(autouse=True)
def chunk_max_tokens():
    with patch.object(regulations_module, "CHUNK_MAX_TOKENS", CHUNK_MAX_TOKENS):
        yield


def load_regulation_elements(regulation_name: str) -> list[RegulationElement]:
    raw_elements = json.loads((DATA_DIR / f"{regulation_name}.json").read_text(encoding="utf-8"))

    return [RegulationElement(label=element["label"], text=element["text"]) for element in raw_elements]


def create_sections(elements: list[RegulationElement]) -> list:
    collection = RegulationAct(elements, WordTokenizer()).get_sections_to_embed()

    return sorted(collection, key=lambda section: section.section_order)


def create_subsections(subsections_count: int, words_per_subsection: int) -> list[RegulationElement]:
    elements = [RegulationElement(label=UsefulLabels.TEXT, text="Art. 110. 1. Studenci tworzą samorząd studencki.")]
    for subsection_number in range(2, subsections_count + 1):
        text = f"{subsection_number}. " + " ".join(["słowo"] * words_per_subsection)
        elements.append(RegulationElement(label=UsefulLabels.LIST_ITEM, text=text))

    return elements


def find_unit_section(sections: list, unit_number: str):
    unit_pattern = re.compile(rf"(^| > )(Art\.|§) {re.escape(unit_number)}( |$)")

    return next(section for section in sections if section.header and unit_pattern.search(section.header))


def find_section(regulation_name: str, unit_number: str):
    sections = create_sections(load_regulation_elements(regulation_name))

    return find_unit_section(sections, unit_number)


def get_chunk_subsections(section, chunk) -> set[str | None]:
    return {element.subsection for element in section.elements[chunk.span.start_element : chunk.span.end_element + 1]}


def test_each_article_becomes_separate_section():
    sections = create_sections(load_regulation_elements(ACT_FIXTURE))

    article_numbers = [
        match.group(1)
        for section in sections
        if section.header and (match := ARTICLE_NUMBER_PATTERN.search(section.header))
    ]

    assert sorted(set(article_numbers), key=int) == [
        "107",
        "108",
        "109",
        "110",
        "111",
        "112",
        "113",
        "114",
        "115",
        "116",
    ]


def test_short_articles_are_not_merged_together():
    sections = create_sections(load_regulation_elements(ACT_FIXTURE))

    short_article = find_unit_section(sections, "112")

    assert len(short_article.chunks) == 1
    assert "Art. 113" not in short_article.text
    assert "Nauczycielem akademickim" not in short_article.text


def test_sections_carry_breadcrumb_header():
    sections = create_sections(load_regulation_elements(ACT_FIXTURE))

    section = find_unit_section(sections, "112")

    assert section.header == "Rozdział 5 Pracownicy uczelni > Art. 112"


def test_long_section_stays_one_section_split_into_chunks():
    elements = create_subsections(subsections_count=6, words_per_subsection=25)

    sections = create_sections(elements)

    assert len(sections) == 1
    assert len(sections[0].chunks) > 1


def test_section_text_keeps_whole_unit():
    elements = create_subsections(subsections_count=6, words_per_subsection=25)

    section = create_sections(elements)[0]

    assert section.text.startswith("1. Studenci tworzą samorząd studencki.")
    assert section.text.count("2.") == 1
    assert section.text.count("6.") == 1


def test_chunks_are_split_on_subsection_boundaries():
    elements = create_subsections(subsections_count=6, words_per_subsection=25)

    section = create_sections(elements)[0]

    for chunk in section.chunks:
        assert chunk.text.split(" ")[0].endswith(".")


def test_chunks_keep_whole_section_content():
    elements = create_subsections(subsections_count=6, words_per_subsection=25)

    section = create_sections(elements)[0]

    assert " ".join(chunk.text for chunk in section.chunks) == " ".join(section.text.split("\n"))


def test_chunk_titles_are_unique_within_section():
    elements = create_subsections(subsections_count=6, words_per_subsection=25)

    section = create_sections(elements)[0]

    embed_titles = [chunk.embed_title for chunk in section.chunks]
    assert len(set(embed_titles)) == len(embed_titles)
    assert embed_titles[0].startswith("Art. 110 ust.")


def test_chunk_titles_use_part_numbers_when_subsections_repeat():
    long_point = " ".join(["słowo"] * 25)
    elements = [
        RegulationElement(label=UsefulLabels.TEXT, text="Art. 110. 1. Studenci tworzą samorząd w zakresie:"),
        RegulationElement(label=UsefulLabels.LIST_ITEM, text=f"1) {long_point};"),
        RegulationElement(label=UsefulLabels.LIST_ITEM, text=f"2) {long_point};"),
        RegulationElement(label=UsefulLabels.LIST_ITEM, text=f"3) {long_point}."),
    ]

    section = create_sections(elements)[0]

    assert len(section.chunks) > 1
    assert all("(część" in chunk.embed_title for chunk in section.chunks)


def test_section_header_has_no_part_suffix():
    elements = create_subsections(subsections_count=6, words_per_subsection=25)

    section = create_sections(elements)[0]

    assert section.header == "Art. 110"


def test_chunk_embedding_text_with_title_fits_limit():
    elements = create_subsections(subsections_count=6, words_per_subsection=26)

    section = create_sections(elements)[0]

    for chunk in section.chunks:
        assert len(chunk.embedding_text.split()) <= CHUNK_MAX_TOKENS


def test_element_longer_than_budget_is_split_by_sentences():
    sentence = " ".join(["słowo"] * 30)
    elements = [RegulationElement(label=UsefulLabels.TEXT, text=f"Art. 110. {sentence}. {sentence}. {sentence}.")]

    section = create_sections(elements)[0]

    assert len(section.chunks) == 3
    for chunk in section.chunks:
        assert len(chunk.text.split(" ")) <= CHUNK_MAX_TOKENS


def test_element_without_sentence_boundaries_is_split_by_tokens():
    elements = [RegulationElement(label=UsefulLabels.TEXT, text="Art. 110. " + " ".join(["słowo"] * 200))]

    section = create_sections(elements)[0]

    assert len(section.chunks) > 1
    for chunk in section.chunks:
        assert len(chunk.text.split(" ")) <= CHUNK_MAX_TOKENS


def test_too_long_breadcrumb_is_trimmed_only_in_chunk_title():
    elements = [
        RegulationElement(label=UsefulLabels.SECTION_HEADER, text="DZIAŁ VII"),
        RegulationElement(
            label=UsefulLabels.SECTION_HEADER,
            text="Bardzo długi tytuł działu o studiach i studentach oraz sprawach im podobnych",
        ),
        RegulationElement(label=UsefulLabels.SECTION_HEADER, text="Rozdział 4"),
        RegulationElement(
            label=UsefulLabels.SECTION_HEADER, text="Samorząd studencki i organizacje studenckie w uczelni"
        ),
        RegulationElement(label=UsefulLabels.TEXT, text="Art. 110. Studenci tworzą samorząd."),
    ]

    section = create_sections(elements)[0]

    assert section.header.startswith("DZIAŁ VII")
    assert section.header.endswith("Art. 110")
    assert "DZIAŁ VII" not in section.chunks[0].embed_title
    assert section.chunks[0].embed_title.endswith("Art. 110")
    assert section.header == (
        "DZIAŁ VII Bardzo długi tytuł działu o studiach i studentach oraz sprawach im podobnych"
        " > Rozdział 4 Samorząd studencki i organizacje studenckie w uczelni"
        " > Art. 110"
    )


def test_elements_are_joined_with_separator():
    sections = create_sections(load_regulation_elements(ACT_FIXTURE))

    article = find_unit_section(sections, "108")

    assert "studiów;\n2) rezygnacji" in article.text
    assert "studiów;2)" not in article.text


def test_unnumbered_content_has_no_header():
    elements = [RegulationElement(label=UsefulLabels.TEXT, text="7. Podmiot zapewnia przebieg akcji protestacyjnej.")]

    sections = create_sections(elements)

    assert sections[0].header is None


def test_section_order_is_continuous():
    sections = create_sections(load_regulation_elements(ACT_FIXTURE))

    assert [section.section_order for section in sections] == list(range(len(sections)))


def test_chunk_index_is_continuous_within_section():
    elements = create_subsections(subsections_count=6, words_per_subsection=25)

    section = create_sections(elements)[0]

    assert [chunk.chunk_index for chunk in section.chunks] == list(range(len(section.chunks)))


def test_unit_with_title_but_without_content_produces_no_sections():
    elements = [RegulationElement(label=UsefulLabels.SECTION_HEADER, text="§ 5 . Systemy komunikacji")]

    sections = create_sections(elements)

    assert sections == []


def test_chunk_span_covers_whole_elements():
    elements = create_subsections(subsections_count=6, words_per_subsection=26)

    section = create_sections(elements)[0]

    for chunk in section.chunks:
        start_text = section.elements[chunk.span.start_element].text
        end_text = section.elements[chunk.span.end_element].text
        assert chunk.text.startswith(start_text)
        assert chunk.text.endswith(end_text)


def test_chunk_span_points_to_split_element():
    sentence = " ".join(["słowo"] * 30)
    elements = [RegulationElement(label=UsefulLabels.TEXT, text=f"Art. 110. {sentence}. {sentence}. {sentence}.")]

    section = create_sections(elements)[0]

    element_text = section.elements[0].text
    for chunk in section.chunks:
        assert chunk.span.start_element == chunk.span.end_element == 0
        assert chunk.text in element_text


def test_long_subsection_is_split_between_points():
    section = find_section(RECTOR_TASKS_FIXTURE, "23")

    for chunk in section.chunks:
        assert SUBSECTION_OR_POINT_START_PATTERN.match(chunk.text)


def test_split_subsection_does_not_share_chunk_with_other_subsections():
    section = find_section(RECTOR_TASKS_FIXTURE, "23")

    split_subsection_chunks = [chunk for chunk in section.chunks if get_chunk_subsections(section, chunk) == {"2"}]

    assert len(split_subsection_chunks) > 1
    for chunk in section.chunks:
        subsections = get_chunk_subsections(section, chunk)
        assert subsections == {"2"} or "2" not in subsections


def test_continuation_chunks_repeat_subsection_intro_only_in_embed_title():
    intro = "2. Do zadań rektora należy w szczególności:"
    section = find_section(RECTOR_TASKS_FIXTURE, "23")

    first_chunk, *continuation_chunks = [
        chunk for chunk in section.chunks if get_chunk_subsections(section, chunk) == {"2"}
    ]

    assert first_chunk.text.startswith(intro)
    assert intro not in first_chunk.embed_title
    for chunk in continuation_chunks:
        assert chunk.embed_title.endswith(f"\n{intro}")
        assert intro not in chunk.text


def test_chunks_split_between_letters_repeat_point_lead_in_embed_title():
    section = find_section(PROMOTION_DATABASE_FIXTURE, "348")

    letter_chunks = [chunk for chunk in section.chunks if LETTER_START_PATTERN.match(chunk.text)]

    assert letter_chunks
    for chunk in letter_chunks:
        subsection_intro, point_lead = chunk.embed_title.split("\n")[-2:]
        assert subsection_intro.startswith("1. Baza dokumentów")
        assert SUBSECTION_OR_POINT_START_PATTERN.match(point_lead)


def test_point_lead_is_not_separated_from_its_first_letter():
    with patch.object(regulations_module, "CHUNK_MAX_TOKENS", 125):
        section = find_section(STUDY_REGULATIONS_FIXTURE, "3")

    chunk = next(chunk for chunk in section.chunks if "1) studia pierwszego stopnia" in chunk.text)

    assert "a) licencjackie" in chunk.text


def test_split_subsection_parts_are_balanced():
    point = " ".join(["słowo"] * 10)
    elements = [RegulationElement(label=UsefulLabels.TEXT, text="Art. 110. 1. Samorząd studencki w zakresie:")]
    for point_number in range(1, 7):
        elements.append(RegulationElement(label=UsefulLabels.LIST_ITEM, text=f"{point_number}) {point};"))

    section = create_sections(elements)[0]

    points_per_chunk = [len(re.findall(r"\d+\) ", chunk.text)) for chunk in section.chunks]
    assert len(points_per_chunk) > 1
    assert max(points_per_chunk) - min(points_per_chunk) <= 1
