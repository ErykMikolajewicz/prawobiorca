from src.domain.services.regulation_description import (
    MAX_DESCRIPTION_BEGINNING_CHARS,
    MAX_DESCRIPTION_HEADINGS,
    create_description_source,
)
from src.domain.value_objects.regulations import RegulationHeading, SectionContent


def test_create_description_source_builds_table_of_contents():
    sections = [
        SectionContent(header="Rozdział I Postanowienia ogólne > § 1 Wprowadzenie", text="§ 1."),
        SectionContent(header="Rozdział I Postanowienia ogólne > § 2 Słownik pojęć", text="§ 2."),
        SectionContent(header="Rozdział V Realizacja studiów > § 27 Urlopy", text="§ 27."),
        SectionContent(header="Rozdział V Realizacja studiów > § 3 0. Przeniesienia z innej uczelni", text="§ 30."),
        SectionContent(header="Rozdział IX Przepisy końcowe > § 40", text="§ 40."),
        SectionContent(header="Art. 5a", text="Art. 5a."),
        SectionContent(header="Art. 6 Zakres ustawy", text="Art. 6."),
        SectionContent(header="Załącznik 6 > Rozdział 1 POSTANOWIENIA OGÓLNE", text="1. Zasady."),
        SectionContent(header=None, text="Wstęp"),
    ]

    description_source = create_description_source("Regulamin", sections)

    assert description_source.presentation_name == "Regulamin"
    assert description_source.headings == [
        RegulationHeading(text="Rozdział I Postanowienia ogólne", level=0),
        RegulationHeading(text="Wprowadzenie", level=1),
        RegulationHeading(text="Słownik pojęć", level=1),
        RegulationHeading(text="Rozdział V Realizacja studiów", level=0),
        RegulationHeading(text="Urlopy", level=1),
        RegulationHeading(text="Przeniesienia z innej uczelni", level=1),
        RegulationHeading(text="Rozdział IX Przepisy końcowe", level=0),
        RegulationHeading(text="Zakres ustawy", level=0),
        RegulationHeading(text="Załącznik 6 > Rozdział 1 POSTANOWIENIA OGÓLNE", level=0),
    ]
    assert description_source.beginning == "§ 1.\n§ 2.\n§ 27.\n§ 30.\n§ 40.\nArt. 5a.\nArt. 6.\n1. Zasady.\nWstęp"


def test_create_description_source_limits_size():
    sections = [
        SectionContent(header=f"Rozdział {index} > Art. {index}", text="a" * 100)
        for index in range(MAX_DESCRIPTION_HEADINGS + 10)
    ]

    description_source = create_description_source("Ustawa", sections)

    assert len(description_source.headings) == MAX_DESCRIPTION_HEADINGS
    assert len(description_source.beginning) == MAX_DESCRIPTION_BEGINNING_CHARS
