from typing import TypedDict, List, Any, Dict

class MappingState(TypedDict, total=False):
    text: str  # Original survey question
    extracted_terms: List[str]  # LLM extracted terms
    llm_response: Any  # If you want to keep the original LLM response
    mapped_results: List[dict]  # Optional historical field (can be left)

    # ✅ Extract + Query node
    search_term: str
    ontology: str
    umls_results: List[Dict[str, Any]]

    # ✅ Rank and match node
    original: str  # The term being processed
    original_question: str  # Optional, for validate
    candidates: List[Dict[str, Any]]  # Candidates with confidence, description
    ranked_mappings: List[Dict[str, Any]]  # If you need to keep the ranked results

    # ✅ Validate node output fields
    best_match_code: str
    best_match_term: str
    confidence: float
