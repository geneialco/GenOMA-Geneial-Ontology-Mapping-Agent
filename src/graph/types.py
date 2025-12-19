"""
Data structure definitions for the UMLS Mapping LangGraph-based Agent.
This module defines the TypedDict classes that represent the state and data flow
throughout the medical term mapping workflow.
"""

from typing import Any, Dict, List, TypedDict


class MappingState(TypedDict, total=False):
    """
    Main state class for the UMLS mapping workflow.
    This TypedDict defines all possible fields that can be present in the state
    as data flows through different nodes in the LangGraph workflow.
    """

    # === Original Survey Input ===
    text: str  # Original complete survey question text
    field_type: str  # Type of survey field (radio, checkbox, short, etc.)
    is_mappable: bool  # Whether the question can be mapped to medical ontologies

    # === Extracted Medical Terms (Term Extraction Node) ===
    extracted_terms: List[str]  # List of medical terms extracted from the survey text

    # === Search UMLS Ontology (Search Node) ===
    search_term: str  # Individual term being searched
    ontology: str  # Target ontology (e.g., "HPO" for Human Phenotype Ontology)
    umls_results: List[Dict[str, Any]]  # Raw results from UMLS API
    umls_mappings: List[Dict[str, Any]]  # Processed mappings with candidates
    retry_count: int  # Number of retry attempts for term rewriting
    mappability_retry_count: int  # Number of retry attempts for mappability assessment
    history_rewritten_terms: List[str]  # History of terms that have been rewritten

    # === Candidate Alternatives (Ranking Node) ===
    original: str  # Original term being processed
    original_question: str  # Original survey question context
    candidates: List[Dict[str, Any]]  # List of candidate ontology terms
    ranked_mappings: List[Dict[str, Any]]  # Mappings with confidence scores
    retries: int  # General retry counter

    # === Preliminary Matching Results (Validation Node) ===
    best_match_code: str  # Best matching ontology code (e.g., "HP:0000001")
    best_match_term: str  # Best matching ontology term name
    confidence: float  # Confidence score for the best match (0.0 to 1.0)
    validated_mappings: List[Dict[str, Any]]  # Final validated mapping results

    # === Refinement Related Fields (Ancestor-based refinement) ===
    original_mapping: Dict[str, Any]  # Original mapping before refinement
    candidate_details: List[
        Dict[str, Any]
    ]  # Detailed candidate information from ancestors
    refine_mapping: Dict[str, Any]  # Refined mapping with improved confidence

    # === Other Optional Records ===
    llm_response: Any  # Raw LLM response for debugging
    mapped_results: List[dict]  # Final mapped results for output
