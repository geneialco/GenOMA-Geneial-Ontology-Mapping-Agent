from langgraph.graph import StateGraph
from src.graph.nodes import (
    is_question_mappable_node,
    extract_medical_terms_node,
    normalize_extracted_terms_node,
    fetch_umls_terms_node,
    rank_mappings_node,
    validate_mapping_node,
    retry_with_llm_rewrite_node  
)
from src.graph.types import MappingState

# Determine if normalization is needed
def should_normalize(state: MappingState) -> bool:
    extracted_terms = state.get("extracted_terms", [])
    return len(extracted_terms) > 1

# Determine if fetch_umls_terms needs retry rewrite (maximum ten retry allowed)
def should_retry_with_llm_rewrite(state: MappingState) -> bool:
    retry_count = state.get("retry_count", 0)
    if retry_count >= 10:
        return False  # Only allow ten retry
    umls_mappings = state.get("umls_mappings", [])
    for mapping in umls_mappings:
        if not mapping.get("candidates"):  # If any term has no candidates
            return True
    return False

# Define complete workflow
graph = StateGraph(MappingState)

# Add all nodes
graph.add_node("is_question_mappable", is_question_mappable_node)
graph.add_node("extract_medical_terms", extract_medical_terms_node)
graph.add_node("normalize_extracted_terms", normalize_extracted_terms_node)
graph.add_node("fetch_umls_terms", fetch_umls_terms_node)
graph.add_node("rank_mappings", rank_mappings_node)
graph.add_node("validate_mapping", validate_mapping_node)
graph.add_node("retry_with_llm_rewrite", retry_with_llm_rewrite_node)

# Set entry point
graph.set_entry_point("is_question_mappable")

# Conditional branching: decide whether to continue based on is_mappable
graph.add_conditional_edges(
    "is_question_mappable",
    lambda state: state.get("is_mappable", False),
    {
        True: "extract_medical_terms",
        False: "__end__"
    }
)

# Normalization decision logic
graph.add_conditional_edges(
    "extract_medical_terms",
    should_normalize,
    {
        True: "normalize_extracted_terms",
        False: "fetch_umls_terms"
    }
)

# After normalization, proceed to fetch
graph.add_edge("normalize_extracted_terms", "fetch_umls_terms")

# After fetch, determine if retry rewrite is needed
graph.add_conditional_edges(
    "fetch_umls_terms",
    should_retry_with_llm_rewrite,
    {
        True: "retry_with_llm_rewrite",
        False: "rank_mappings"
    }
)

# After retry rewrite, increment retry_count and check if limit exceeded
graph.add_conditional_edges(
    "retry_with_llm_rewrite",
    should_retry_with_llm_rewrite,
    {
        True: "fetch_umls_terms",
        False: "__end__"
    }
)

# fetch → rank → validate → end
graph.add_edge("rank_mappings", "validate_mapping")
graph.add_edge("validate_mapping", "__end__")

# Compile workflow
umls_mapping_graph = graph.compile()

# Export raw graph for visualization
raw_graph = umls_mapping_graph.get_graph()  # Note: use the compiled object
