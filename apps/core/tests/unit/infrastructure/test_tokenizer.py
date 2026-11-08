from core_service.infrastructure.tokenizers.mmlw import MmlwTokenizer

SENTENCE = "Art. 1. Ustawa określa zasady działania uczelni. "


def test_mmlw_tokenizer_counts_more_tokens_for_longer_text():
    tokenizer = MmlwTokenizer()

    assert 0 < tokenizer.count_tokens(SENTENCE) < tokenizer.count_tokens(SENTENCE * 2)


def test_mmlw_tokenizer_does_not_truncate_text_longer_than_model_limit():
    tokenizer = MmlwTokenizer()

    assert tokenizer.count_tokens(SENTENCE * 100) > MmlwTokenizer.max_tokens
