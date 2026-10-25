import json
from pathlib import Path

import pytest

from src.domain.services.legal_structure_parser import LegalStructureParser
from src.domain.value_objects.legal_units import RegulationElement, UnitType, UsefulLabels

DATA_DIR = Path(__file__).parents[3] / "data"

ACT_FIXTURE = "ustawa-nauka_slice_30-31"
STATUTE_FIXTURE = "pwr-regulamin_2025_slice_7-9"
PROMOTION_DATABASE_FIXTURE = "ustawa-nauka_slice_209-210"
MINISTERIAL_REGULATION_FIXTURE = "rozporzadzenie-studia_slice_11-12"


def load_regulation_elements(regulation_name: str) -> list[RegulationElement]:
    raw_elements = json.loads((DATA_DIR / f"{regulation_name}.json").read_text(encoding="utf-8"))

    return [RegulationElement(label=element["label"], text=element["text"]) for element in raw_elements]


def unit_text(unit) -> str:
    return " ".join(element.text for element in unit.elements)


def test_act_is_split_into_separate_articles():
    elements = load_regulation_elements(ACT_FIXTURE)

    units = LegalStructureParser().parse(elements)

    article_numbers = [unit.number for unit in units if unit.unit_type == UnitType.ARTICLE]
    assert article_numbers == ["107", "108", "109", "110", "111", "112", "113", "114", "115", "116"]


def test_article_keeps_division_breadcrumb():
    elements = load_regulation_elements(ACT_FIXTURE)

    units = LegalStructureParser().parse(elements)

    article = next(unit for unit in units if unit.number == "110")
    assert article.path == ["Rozdział 4 Samorząd studencki i organizacje studenckie"]
    assert article.breadcrumb == "Rozdział 4 Samorząd studencki i organizacje studenckie > Art. 110"


def test_articles_do_not_leak_into_each_other():
    elements = load_regulation_elements(ACT_FIXTURE)

    units = LegalStructureParser().parse(elements)

    article = next(unit for unit in units if unit.number == "108")
    assert unit_text(article).startswith("1. Studenta skreśla się z listy studentów")
    assert unit_text(article).endswith("3. Skreślenie z listy studentów następuje w drodze decyzji administracyjnej.")
    assert "Art. 109" not in unit_text(article)


def test_statute_is_split_into_paragraphs_with_titles():
    elements = load_regulation_elements(STATUTE_FIXTURE)

    units = LegalStructureParser().parse(elements)

    paragraphs = [unit for unit in units if unit.unit_type == UnitType.PARAGRAPH]
    assert [unit.number for unit in paragraphs] == ["5", "6", "7"]
    assert paragraphs[1].title == "Prawa studenta"
    assert paragraphs[1].breadcrumb == "Rozdział II Prawa i obowiązki studenta > § 6 Prawa studenta"


def test_page_headers_and_footers_are_dropped():
    elements = load_regulation_elements(ACT_FIXTURE) + load_regulation_elements(STATUTE_FIXTURE)

    units = LegalStructureParser().parse(elements)

    parsed_text = " ".join(unit_text(unit) for unit in units)
    assert "Dziennik Ustaw" not in parsed_text
    assert "Strona 7 z 48" not in parsed_text


def test_elements_before_first_unit_become_unnumbered_unit():
    elements = load_regulation_elements(ACT_FIXTURE)

    units = LegalStructureParser().parse(elements)

    assert units[0].unit_type == UnitType.UNNUMBERED
    assert units[0].number is None
    assert unit_text(units[0]).startswith("7. Podmiot, o którym mowa w ust. 2")


def test_article_reference_inside_text_does_not_start_new_unit():
    elements = [
        RegulationElement(label=UsefulLabels.TEXT, text="Art. 109. Osoba zachowuje prawa studenta."),
        RegulationElement(label=UsefulLabels.TEXT, text="Przepisy art. 110 ust. 8 zdanie drugie stosuje się."),
    ]

    units = LegalStructureParser().parse(elements)

    assert len(units) == 1
    assert units[0].number == "109"
    assert len(units[0].elements) == 2


def test_glued_articles_are_split_into_separate_units():
    elements = [
        RegulationElement(
            label=UsefulLabels.TEXT,
            text="Art. 112. Pracownikami uczelni są nauczyciele. Art. 113. Nauczycielem może być osoba.",
        )
    ]

    units = LegalStructureParser().parse(elements)

    assert [unit.number for unit in units] == ["112", "113"]


def test_text_is_normalized():
    elements = [
        RegulationElement(
            label=UsefulLabels.TEXT,
            text="Art. 5. 1. Uczelnia,  oprócz  systemu , udostępnia konto ( § 27 ) studentowi .",
        )
    ]

    units = LegalStructureParser().parse(elements)

    assert unit_text(units[0]) == "1. Uczelnia, oprócz systemu, udostępnia konto (§ 27) studentowi."


def test_paragraph_is_treated_as_content_when_act_uses_articles():
    elements = [
        RegulationElement(label=UsefulLabels.TEXT, text="Art. 5. § 1. Odpowiedzialności karnej podlega sprawca."),
        RegulationElement(label=UsefulLabels.TEXT, text="§ 2. Przepisu § 1 nie stosuje się."),
    ]

    units = LegalStructureParser().parse(elements)

    assert len(units) == 1
    assert units[0].unit_type == UnitType.ARTICLE
    assert units[0].number == "5"
    assert len(units[0].elements) == 2


def test_points_labelled_as_headers_stay_in_article():
    elements = load_regulation_elements(PROMOTION_DATABASE_FIXTURE)

    units = LegalStructureParser().parse(elements)

    article = next(unit for unit in units if unit.number == "349")
    article_texts = [element.text for element in article.elements]
    assert "1) imiona i nazwisko;" in article_texts
    assert "<1a) stopień albo tytuł profesora;" in article_texts
    assert "5) informacje o wzorach:" in article_texts
    assert units[-1] is article


def test_points_labelled_as_headers_inherit_subsection():
    elements = load_regulation_elements(PROMOTION_DATABASE_FIXTURE)

    units = LegalStructureParser().parse(elements)

    article = next(unit for unit in units if unit.number == "349")
    point = next(element for element in article.elements if element.text.startswith("<3a)"))
    assert point.subsection == "1"


def test_letter_labelled_as_header_is_content():
    elements = [
        RegulationElement(label=UsefulLabels.TEXT, text="Art. 5. 1. Baza obejmuje:"),
        RegulationElement(label=UsefulLabels.LIST_ITEM, text="1) informacje o wzorach:"),
        RegulationElement(label=UsefulLabels.SECTION_HEADER, text="a) dyplomów ukończenia studiów,"),
    ]

    units = LegalStructureParser().parse(elements)

    assert len(units) == 1
    assert len(units[0].elements) == 3
    assert units[0].path == []


def test_nested_divisions_build_full_path():
    elements = [
        RegulationElement(label=UsefulLabels.SECTION_HEADER, text="DZIAŁ VII"),
        RegulationElement(label=UsefulLabels.SECTION_HEADER, text="Studia i studenci"),
        RegulationElement(label=UsefulLabels.SECTION_HEADER, text="Rozdział 4"),
        RegulationElement(label=UsefulLabels.SECTION_HEADER, text="Samorząd studencki"),
        RegulationElement(label=UsefulLabels.TEXT, text="Art. 110. 1. Studenci tworzą samorząd."),
    ]

    units = LegalStructureParser().parse(elements)

    assert units[0].path == ["DZIAŁ VII Studia i studenci", "Rozdział 4 Samorząd studencki"]


def test_division_of_the_same_rank_replaces_previous_one():
    elements = [
        RegulationElement(label=UsefulLabels.SECTION_HEADER, text="Rozdział 4"),
        RegulationElement(label=UsefulLabels.TEXT, text="Art. 110. Studenci tworzą samorząd."),
        RegulationElement(label=UsefulLabels.SECTION_HEADER, text="Rozdział 5"),
        RegulationElement(label=UsefulLabels.TEXT, text="Art. 112. Pracownikami uczelni są nauczyciele."),
    ]

    units = LegalStructureParser().parse(elements)

    assert units[0].path == ["Rozdział 4"]
    assert units[1].path == ["Rozdział 5"]


def test_header_without_division_keyword_becomes_path_segment():
    elements = [
        RegulationElement(label=UsefulLabels.SECTION_HEADER, text="Postanowienia ogólne"),
        RegulationElement(label=UsefulLabels.TEXT, text="Uczelnia działa na podstawie ustawy."),
    ]

    units = LegalStructureParser().parse(elements)

    assert units[0].unit_type == UnitType.UNNUMBERED
    assert units[0].path == ["Postanowienia ogólne"]


def test_points_inherit_subsection_of_their_parent():
    elements = load_regulation_elements(ACT_FIXTURE)

    units = LegalStructureParser().parse(elements)

    article = next(unit for unit in units if unit.number == "107")
    assert [element.subsection for element in article.elements] == ["1", "2", "2", "2"]


@pytest.mark.parametrize("empty_text", ["", "   ", "\ufeff"])
def test_empty_elements_are_dropped(empty_text):
    elements = [
        RegulationElement(label=UsefulLabels.TEXT, text="Art. 1. Przepis."),
        RegulationElement(label=UsefulLabels.TEXT, text=empty_text),
    ]

    units = LegalStructureParser().parse(elements)

    assert len(units[0].elements) == 1


def test_unit_without_content_is_dropped():
    elements = [RegulationElement(label=UsefulLabels.SECTION_HEADER, text="Rozdział 4")]

    units = LegalStructureParser().parse(elements)

    assert units == []


def test_unnumbered_unit_without_divisions_has_no_breadcrumb():
    elements = [RegulationElement(label=UsefulLabels.TEXT, text="7. Podmiot zapewnia przebieg akcji.")]

    units = LegalStructureParser().parse(elements)

    assert units[0].breadcrumb is None
    assert units[0].citation is None


def test_unit_marker_placed_after_header_title_starts_unit():
    elements = [
        RegulationElement(label=UsefulLabels.SECTION_HEADER, text="Obowiązki mieszkańca domu studenckiego § 2"),
        RegulationElement(label=UsefulLabels.TEXT, text="Mieszkaniec domu studenckiego ma obowiązek:"),
    ]

    units = LegalStructureParser().parse(elements)

    assert len(units) == 1
    assert units[0].unit_type == UnitType.PARAGRAPH
    assert units[0].number == "2"
    assert units[0].title == "Obowiązki mieszkańca domu studenckiego"
    assert units[0].path == []


def test_header_above_bare_unit_marker_becomes_unit_title():
    elements = [
        RegulationElement(label=UsefulLabels.SECTION_HEADER, text="Prawa mieszkańca domu studenckiego"),
        RegulationElement(label=UsefulLabels.SECTION_HEADER, text="§ 1"),
        RegulationElement(label=UsefulLabels.TEXT, text="Mieszkaniec domu studenckiego ma prawo do:"),
    ]

    units = LegalStructureParser().parse(elements)

    assert len(units) == 1
    assert units[0].number == "1"
    assert units[0].title == "Prawa mieszkańca domu studenckiego"
    assert units[0].breadcrumb == "§ 1 Prawa mieszkańca domu studenckiego"


def test_division_title_is_not_stolen_by_following_unit():
    elements = [
        RegulationElement(label=UsefulLabels.SECTION_HEADER, text="Rozdział 4"),
        RegulationElement(label=UsefulLabels.SECTION_HEADER, text="Samorząd studencki"),
        RegulationElement(label=UsefulLabels.TEXT, text="Art. 110. Studenci tworzą samorząd."),
    ]

    units = LegalStructureParser().parse(elements)

    assert units[0].title is None
    assert units[0].path == ["Rozdział 4 Samorząd studencki"]


def test_ministerial_regulation_is_split_into_paragraphs():
    elements = load_regulation_elements(MINISTERIAL_REGULATION_FIXTURE)

    units = LegalStructureParser().parse(elements)

    assert [unit.unit_type for unit in units] == [UnitType.UNNUMBERED] + [UnitType.PARAGRAPH] * 7
    assert [unit.number for unit in units[1:]] == ["18", "19", "19a", "20", "21", "22", "23"]


def test_footnote_markers_are_removed():
    elements = load_regulation_elements(MINISTERIAL_REGULATION_FIXTURE)

    units = LegalStructureParser().parse(elements)

    first_texts = {unit.number: unit.elements[0].text for unit in units}
    assert first_texts[None].startswith("1a. W przypadku prowadzenia kart okresowych")
    assert first_texts["18"].startswith("1. Protokół egzaminu dyplomowego zawiera")
    assert first_texts["19a"].startswith("Dokumentacja przebiegu studiów w postaci elektronicznej")
    assert first_texts["20"] == "1. Wzór legitymacji studenckiej wydawanej w postaci:"
    assert first_texts["21"] == "1. Ważność legitymacji studenckiej potwierdza się co semestr:"
    assert first_texts["23"].startswith("1. W przypadku utraty oryginału dyplomu")


def test_footnote_marker_at_end_of_element_is_removed():
    elements = load_regulation_elements(MINISTERIAL_REGULATION_FIXTURE)

    units = LegalStructureParser().parse(elements)

    assert "4. Ukończenie studiów odnotowuje się w:" in [element.text for element in units[0].elements]


def test_footnote_markers_in_subsections_are_removed():
    elements = load_regulation_elements(MINISTERIAL_REGULATION_FIXTURE)

    units = LegalStructureParser().parse(elements)

    paragraph = next(unit for unit in units if unit.number == "22")
    paragraph_texts = [element.text for element in paragraph.elements]
    assert paragraph_texts[0].startswith("1. Odpis dyplomu ukończenia studiów")
    assert paragraph_texts[2].startswith("2a. W odpisie dyplomu wspólnego")
    assert paragraph_texts[3].startswith("2a. W odpisie dyplomu wspólnego")
    assert paragraph_texts[5] == "4. Do odpisów dyplomu wspólnego przepis ust. 3 stosuje się odpowiednio."


def test_subsection_after_footnote_marker_is_recognised():
    elements = load_regulation_elements(MINISTERIAL_REGULATION_FIXTURE)

    units = LegalStructureParser().parse(elements)

    paragraph = next(unit for unit in units if unit.number == "20")
    assert [element.subsection for element in paragraph.elements] == ["1", "1", "1", "1", "2"]


def test_paragraph_continued_on_next_page_keeps_subsections():
    elements = load_regulation_elements(MINISTERIAL_REGULATION_FIXTURE)

    units = LegalStructureParser().parse(elements)

    paragraph = next(unit for unit in units if unit.number == "21")
    assert [element.subsection for element in paragraph.elements] == [
        "1",
        "1",
        "1",
        "2",
        "3",
        "4",
        "4",
        "4",
        "4",
        "4",
        "4",
        "5",
    ]


def test_subsection_labelled_as_header_stays_in_paragraph():
    elements = load_regulation_elements(MINISTERIAL_REGULATION_FIXTURE)

    units = LegalStructureParser().parse(elements)

    paragraph = next(unit for unit in units if unit.number == "22")
    assert [element.subsection for element in paragraph.elements] == ["1", "2", "2a", "2a", "3", "4", "5"]
    assert all(unit.path == [] for unit in units)


def test_hyphenated_words_are_joined():
    elements = load_regulation_elements(MINISTERIAL_REGULATION_FIXTURE)

    units = LegalStructureParser().parse(elements)

    parsed_texts = {unit.number: unit_text(unit) for unit in units}
    assert "datę złożenia egzaminu dyplomowego" in parsed_texts["19"]
    assert "w systemie teleinformatycznym" in parsed_texts["19a"]
    assert "podmiotów realizujących zadania publiczne" in parsed_texts["19a"]
    assert "zawieszenia w prawach studenta" in parsed_texts["21"]
    assert "wyraz 'DUPLIKAT'" in parsed_texts["23"]


def test_dash_between_spaces_is_kept():
    elements = load_regulation_elements(MINISTERIAL_REGULATION_FIXTURE)

    units = LegalStructureParser().parse(elements)

    paragraph = next(unit for unit in units if unit.number == "20")
    assert paragraph.elements[3].text == "- jest określony w załączniku nr 1 do rozporządzenia."


def test_article_labelled_as_header_is_content():
    elements = [
        RegulationElement(label=UsefulLabels.TEXT, text="Art. 18. 5. Rada uczelni składa senatowi sprawozdanie."),
        RegulationElement(label=UsefulLabels.SECTION_HEADER, text="Art. 19. 1. W skład rady uczelni wchodzi:"),
        RegulationElement(label=UsefulLabels.LIST_ITEM, text="1) 6 albo 8 osób powoływanych przez senat;"),
    ]

    units = LegalStructureParser().parse(elements)

    assert [unit.number for unit in units] == ["18", "19"]
    assert units[1].title is None
    assert [element.text for element in units[1].elements] == [
        "1. W skład rady uczelni wchodzi:",
        "1) 6 albo 8 osób powoływanych przez senat;",
    ]


@pytest.mark.parametrize(
    "header_text",
    [
        "<6. Legitymacja doktoranta jest wydawana w postaci:",
        "[3. Wpływy z kar stanowią dochód budżetu państwa.]",
        "-uczelnia podaje do wiadomości publicznej w terminie, o którym mowa w ust. 1.>",
    ],
    ids=("subsection not yet in force", "repealed subsection", "continuation after dash"),
)
def test_mislabelled_provision_stays_in_article(header_text):
    elements = [
        RegulationElement(label=UsefulLabels.SECTION_HEADER, text="Rozdział 2"),
        RegulationElement(label=UsefulLabels.TEXT, text="Art. 202. 5. Podmiot wydaje legitymację."),
        RegulationElement(label=UsefulLabels.SECTION_HEADER, text=header_text),
        RegulationElement(label=UsefulLabels.TEXT, text="Art. 203. Doktorant ma prawo."),
    ]

    units = LegalStructureParser().parse(elements)

    assert [unit.number for unit in units] == ["202", "203"]
    assert units[0].elements[-1].text == header_text
    assert units[1].path == ["Rozdział 2"]


def test_division_number_with_letter_is_recognised():
    elements = [
        RegulationElement(label=UsefulLabels.SECTION_HEADER, text="DZIAŁ XIV"),
        RegulationElement(label=UsefulLabels.SECTION_HEADER, text="Przepisy szczególne"),
        RegulationElement(label=UsefulLabels.TEXT, text="Art. 469. Przepis."),
        RegulationElement(label=UsefulLabels.SECTION_HEADER, text="DZIAŁ XIVA"),
        RegulationElement(label=UsefulLabels.SECTION_HEADER, text="Przetwarzanie danych osobowych"),
        RegulationElement(label=UsefulLabels.TEXT, text="Art. 469a. Przepis."),
    ]

    units = LegalStructureParser().parse(elements)

    assert units[1].path == ["DZIAŁ XIVA Przetwarzanie danych osobowych"]


def test_division_number_glued_to_title_is_recognised():
    elements = [
        RegulationElement(label=UsefulLabels.SECTION_HEADER, text="Rozdział V -Realizacja studiów"),
        RegulationElement(label=UsefulLabels.SECTION_HEADER, text="§ 28 Powtarzanie etapu studiów"),
        RegulationElement(label=UsefulLabels.TEXT, text="1. Student może powtarzać etap studiów."),
        RegulationElement(label=UsefulLabels.SECTION_HEADER, text="Rozdział VIIndywidualna organizacja studiów"),
        RegulationElement(label=UsefulLabels.SECTION_HEADER, text="§ 29 Indywidualna organizacja studiów"),
        RegulationElement(label=UsefulLabels.TEXT, text="1. Student może studiować według planu."),
    ]

    units = LegalStructureParser().parse(elements)

    assert units[1].path == ["Rozdział VIIndywidualna organizacja studiów"]


def test_split_paragraph_number_is_joined():
    elements = [
        RegulationElement(label=UsefulLabels.SECTION_HEADER, text="§ 3 0. Przeniesienia z innej uczelni"),
        RegulationElement(label=UsefulLabels.TEXT, text="1. Student może przenieść się z innej uczelni."),
    ]

    units = LegalStructureParser().parse(elements)

    assert units[0].number == "30"
    assert units[0].title == "Przeniesienia z innej uczelni"


def test_generic_header_of_unnumbered_content_does_not_cover_following_units():
    elements = [
        RegulationElement(label=UsefulLabels.SECTION_HEADER, text="Słownik pojęć"),
        RegulationElement(label=UsefulLabels.TEXT, text="Przez użyte w regulaminie pojęcia rozumie się:"),
        RegulationElement(label=UsefulLabels.SECTION_HEADER, text="§ 2. Szkoła Doktorska"),
        RegulationElement(label=UsefulLabels.TEXT, text="1. W Politechnice jest prowadzona szkoła doktorska."),
    ]

    units = LegalStructureParser().parse(elements)

    assert units[0].path == ["Słownik pojęć"]
    assert units[1].title == "Szkoła Doktorska"
    assert units[1].path == []


def test_attachment_starts_new_branch_of_breadcrumb():
    elements = [
        RegulationElement(label=UsefulLabels.SECTION_HEADER, text="DZIAŁ XII"),
        RegulationElement(label=UsefulLabels.SECTION_HEADER, text="PRZEPISY KOŃCOWE"),
        RegulationElement(label=UsefulLabels.SECTION_HEADER, text="§ 71"),
        RegulationElement(label=UsefulLabels.TEXT, text="Statut wchodzi w życie z dniem 1 października."),
        RegulationElement(label=UsefulLabels.SECTION_HEADER, text="Załącznik 6 ZASADY PRZEPROWADZANIA WYBORÓW"),
        RegulationElement(label=UsefulLabels.SECTION_HEADER, text="Rozdział 1"),
        RegulationElement(label=UsefulLabels.SECTION_HEADER, text="POSTANOWIENIA OGÓLNE"),
        RegulationElement(label=UsefulLabels.TEXT, text="1. Poniższe zasady dotyczą przeprowadzania wyborów."),
    ]

    units = LegalStructureParser().parse(elements)

    assert units[1].path == ["Załącznik 6 ZASADY PRZEPROWADZANIA WYBORÓW", "Rozdział 1 POSTANOWIENIA OGÓLNE"]


def test_attachment_marker_in_text_starts_attachment():
    elements = [
        RegulationElement(label=UsefulLabels.TEXT, text="§ 39. Rozporządzenie wchodzi w życie."),
        RegulationElement(label=UsefulLabels.TEXT, text="Załącznik nr 1 38) Załącznik nr 1 38)"),
        RegulationElement(label=UsefulLabels.SECTION_HEADER, text="WZÓR LEGITYMACJI STUDENCKIEJ"),
        RegulationElement(label=UsefulLabels.TEXT, text="Blankiet legitymacji ma wymiary 85,6 mm x 54 mm."),
        RegulationElement(label=UsefulLabels.TEXT, text="Załącznik nr 1"),
        RegulationElement(label=UsefulLabels.TEXT, text="Hologram ma kształt koła."),
    ]

    units = LegalStructureParser().parse(elements)

    assert len(units) == 2
    assert units[1].path == ["Załącznik nr 1 WZÓR LEGITYMACJI STUDENCKIEJ"]
    assert [element.text for element in units[1].elements] == [
        "Blankiet legitymacji ma wymiary 85,6 mm x 54 mm.",
        "Hologram ma kształt koła.",
    ]


def test_sentence_starting_with_attachment_is_content():
    elements = [
        RegulationElement(label=UsefulLabels.TEXT, text="§ 1. Wzory dokumentów."),
        RegulationElement(label=UsefulLabels.TEXT, text="Załącznik nr 1 określa wzór legitymacji."),
    ]

    units = LegalStructureParser().parse(elements)

    assert len(units) == 1
    assert units[0].elements[-1].text == "Załącznik nr 1 określa wzór legitymacji."


def test_footnote_marker_is_removed_from_header():
    elements = [
        RegulationElement(label=UsefulLabels.SECTION_HEADER, text="OBWIESZCZENIE MINISTRA NAUKI 1)"),
        RegulationElement(label=UsefulLabels.TEXT, text="z dnia 25 sierpnia 2026 r."),
    ]

    units = LegalStructureParser().parse(elements)

    assert units[0].path == ["OBWIESZCZENIE MINISTRA NAUKI"]
