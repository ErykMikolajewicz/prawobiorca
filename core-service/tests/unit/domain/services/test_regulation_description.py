from src.domain.services.regulation_description import (
    MAX_DESCRIPTION_BEGINNING_CHARS,
    MAX_DESCRIPTION_HEADINGS,
    create_description_source,
)
from src.domain.value_objects.regulations import SectionContent


def test_create_description_source_collects_unique_headings():
    sections = [
        SectionContent(header="Dział I > Rozdział 1 > Art. 1", text="Art. 1."),
        SectionContent(header="Dział I > Rozdział 1 > Art. 2", text="Art. 2."),
        SectionContent(header="Dział I > Rozdział 2 > Art. 3", text="Art. 3."),
        SectionContent(header="§ 1", text="§ 1."),
        SectionContent(header=None, text="Wstęp"),
    ]

    description_source = create_description_source("Kodeks", sections)

    assert description_source.presentation_name == "Kodeks"
    assert description_source.headings == ["Dział I > Rozdział 1", "Dział I > Rozdział 2"]
    assert description_source.beginning == "Art. 1.\nArt. 2.\nArt. 3.\n§ 1.\nWstęp"


def test_create_description_source_limits_size():
    sections = [
        SectionContent(header=f"Rozdział {index} > Art. {index}", text="a" * 100)
        for index in range(MAX_DESCRIPTION_HEADINGS + 10)
    ]

    description_source = create_description_source("Ustawa", sections)

    assert len(description_source.headings) == MAX_DESCRIPTION_HEADINGS
    assert len(description_source.beginning) == MAX_DESCRIPTION_BEGINNING_CHARS
