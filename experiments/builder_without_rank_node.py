from langgraph.graph import StateGraph

from experiments.ablation_nodes import gather_ancestor_candidates_node
from src.graph.nodes import (
    extract_medical_terms_checkbox_node,
    extract_medical_terms_radio_node,
    fetch_umls_terms_node,
    is_question_mappable_node,
    retry_with_llm_rewrite_node,
    validate_mapping_node,
)
from src.graph.types import MappingState


# Determine whether a retry is needed
def should_retry_with_llm_rewrite(state: MappingState) -> bool:
    retry_count = state.get("retry_count", 0)
    if retry_count >= 10:
        return False
    umls_mappings = state.get("umls_mappings", [])
    for mapping in umls_mappings:
        if not mapping.get("candidates"):
            return True
    return False


# Determine whether to enter gather_ancestor_candidates_node
def should_refine_with_ancestors(state: MappingState) -> bool:
    validated_list = state.get("validated_mappings", [])
    if not validated_list or not isinstance(validated_list, list):
        return False
    confidence = validated_list[0].get("confidence", 1.0)
    return confidence < 0.9


# Transfer judgment node: select the extraction path based on field_type
def choose_extraction_node(state: MappingState) -> str:
    field_type = state.get("field_type", "").lower()
    if field_type == "checkbox":
        return "extract_medical_terms_checkbox"
    else:
        return "extract_medical_terms_radio"


# New: No sorting pass-through node to keep validate input consistent
def promote_umls_to_ranked(state: MappingState) -> MappingState:
    state["ranked_mappings"] = state.get("umls_mappings", [])
    return state


# Create a graph
graph = StateGraph(MappingState)

# Add all nodes (remove rank_mappings; add promote_umls_to_ranked)
graph.add_node("is_question_mappable", is_question_mappable_node)
graph.add_node("extract_medical_terms_checkbox", extract_medical_terms_checkbox_node)
graph.add_node("extract_medical_terms_radio", extract_medical_terms_radio_node)
graph.add_node("fetch_umls_terms", fetch_umls_terms_node)
# graph.add_node("rank_mappings", rank_mappings_node)  # ⟵ removed
graph.add_node("validate_mapping", validate_mapping_node)
graph.add_node("retry_with_llm_rewrite", retry_with_llm_rewrite_node)
graph.add_node("gather_ancestor_candidates", gather_ancestor_candidates_node)
graph.add_node("choose_extraction", lambda state: state)
graph.add_node("promote_umls_to_ranked", promote_umls_to_ranked)  # ⟵ new

# Set the entry
graph.set_entry_point("is_question_mappable")

# 1. is_question_mappable → Is it mappable?
graph.add_conditional_edges(
    "is_question_mappable",
    lambda state: state.get("is_mappable", False),
    {True: "choose_extraction", False: "__end__"},
)

# 2. choose_extraction → Enter the specific extraction node
graph.add_conditional_edges(
    "choose_extraction",
    choose_extraction_node,
    {
        "extract_medical_terms_checkbox": "extract_medical_terms_checkbox",
        "extract_medical_terms_radio": "extract_medical_terms_radio",
    },
)

# 3. after extraction node → fetch
graph.add_edge("extract_medical_terms_checkbox", "fetch_umls_terms")
graph.add_edge("extract_medical_terms_radio", "fetch_umls_terms")

# 4. fetch → retry or  validate
graph.add_conditional_edges(
    "fetch_umls_terms",
    should_retry_with_llm_rewrite,
    {
        True: "retry_with_llm_rewrite",
        # False originally went to rank_mappings; now directly upgrade um ls_mappings to ranked_mappings, and then go to validate
        False: "promote_umls_to_ranked",
    },
)

# 5. retry → fetch or end (Keep your original branching logic unchanged)
graph.add_conditional_edges(
    "retry_with_llm_rewrite",
    should_retry_with_llm_rewrite,
    {True: "fetch_umls_terms", False: "__end__"},
)

# 6. Direct to Node → validate
graph.add_edge("promote_umls_to_ranked", "validate_mapping")

# 7. validate → gather_ancestor_candidates or end
graph.add_conditional_edges(
    "validate_mapping",
    should_refine_with_ancestors,
    {True: "gather_ancestor_candidates", False: "__end__"},
)

graph.add_edge("gather_ancestor_candidates", "__end__")

# Compiled Graph
umls_mapping_graph = graph.compile()
raw_graph = umls_mapping_graph.get_graph()
