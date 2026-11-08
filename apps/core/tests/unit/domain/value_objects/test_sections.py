from src.domain.value_objects.sections import RegulationSection, SectionChunk, SectionsCollection

BATCH_SIZE = 10


def create_section(*texts: str) -> RegulationSection:
    chunks = [SectionChunk(text=text, embed_title="Art. 1", chunk_index=index) for index, text in enumerate(texts)]
    return RegulationSection(header="Art. 1", text=" ".join(texts), chunks=chunks)


def test_chunks_are_sorted_by_text_length():
    collection = SectionsCollection([create_section("dłuższy tekst chunka"), create_section("krótki")])

    batches = collection.get_chunks_batch_iterator(BATCH_SIZE)

    assert [chunk.text for chunk in batches[0]] == ["krótki", "dłuższy tekst chunka"]


def test_sections_keep_their_order():
    collection = SectionsCollection([create_section("dłuższy tekst sekcji"), create_section("krótki")])

    assert [section.text for section in collection] == ["dłuższy tekst sekcji", "krótki"]


def test_batch_iterator_splits_chunks_into_batches():
    chunks_count = BATCH_SIZE + 1
    collection = SectionsCollection([create_section(*[f"tekst {index}" for index in range(chunks_count)])])

    batches = collection.get_chunks_batch_iterator(BATCH_SIZE)

    assert len(batches) == 2
    assert len(batches[0]) == BATCH_SIZE
    assert len(batches[1]) == 1
