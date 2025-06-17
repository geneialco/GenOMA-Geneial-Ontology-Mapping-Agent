from typing import TypedDict, List, Dict, Any

class MappingState(TypedDict, total=False):
    # Original Survey Input
    text: str  # Original complete survey
    survey_text: str  # (Redundantly kept for compatibility with refinement node)

    # Extracted Medical Terms (Term Extraction Node)
    extracted_terms: List[str]

    # Search UMLS Ontology (Search Node)
    search_term: str
    ontology: str
    umls_results: List[Dict[str, Any]]
    umls_mappings: List[Dict[str, Any]]
    retry_count: int
    history_rewritten_terms: List[str] = []

    # Candidate Alternatives (Ranking Node)
    original: str
    original_question: str
    candidates: List[Dict[str, Any]]
    ranked_mappings: List[Dict[str, Any]]
    retries: int 

    # Preliminary Matching Results (Validation Node)
    best_match_code: str
    best_match_term: str
    confidence: float
    validated_mappings: List[Dict[str, Any]]

    # Refinement Related Fields (Compatible with ancestor-based refinement)
    original_mapping: Dict[str, Any]  # {"matched_code":..., "matched_term":...}
    candidate_details: List[Dict[str, Any]]  # [{"cui":..., "name":...}]
    refined_mapping: Dict[str, Any]  # {"matched_code":..., "matched_term":..., "confidence":...}

    # Other Optional Records
    llm_response: Any
    mapped_results: List[dict]

