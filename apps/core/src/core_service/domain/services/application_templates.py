def is_semantic_search_query(query: str) -> bool:
    return " " in query.lstrip()
