from langgraph.graph import StateGraph

from experiments.ablation_nodes import gather_ancestor_candidates_node
from src.graph.nodes import (
    extract_medical_terms_checkbox_node,
    extract_medical_terms_radio_node,
    fetch_umls_terms_node,
    is_question_mappable_node,
    rank_mappings_node,
    validate_mapping_node,
)
from src.graph.types import MappingState

# (Optional) To completely remove the retry logic, you can delete this function.
# If it might be needed later for A/B replication, you can also keep it but not use it.
# def should_retry_with_llm_rewrite(state: MappingState) -> bool:
#     ...


def should_refine_with_ancestors(state: MappingState) -> bool:
    validated_list = state.get("validated_mappings", [])
    if not validated_list or not isinstance(validated_list, list):
        return False
    confidence = validated_list[0].get("confidence", 1.0)
    return confidence < 0.9


def choose_extraction_node(state: MappingState) -> str:
    field_type = state.get("field_type", "").lower()
    if field_type == "checkbox":
        return "extract_medical_terms_checkbox"
    else:
        return "extract_medical_terms_radio"


# Create a graph
graph = StateGraph(MappingState)

# Adding reserved nodes
graph.add_node("is_question_mappable", is_question_mappable_node)
graph.add_node("extract_medical_terms_checkbox", extract_medical_terms_checkbox_node)
graph.add_node("extract_medical_terms_radio", extract_medical_terms_radio_node)
graph.add_node("fetch_umls_terms", fetch_umls_terms_node)
graph.add_node("rank_mappings", rank_mappings_node)
graph.add_node("validate_mapping", validate_mapping_node)
# graph.add_node("retry_with_llm_rewrite", retry_with_llm_rewrite_node)
graph.add_node("gather_ancestor_candidates", gather_ancestor_candidates_node)
graph.add_node("choose_extraction", lambda state: state)

# Entrance
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

# 3. After extraction → fetch
graph.add_edge("extract_medical_terms_checkbox", "fetch_umls_terms")
graph.add_edge("extract_medical_terms_radio", "fetch_umls_terms")

# 4. fetch → Direct rank (remove the retry branch)
graph.add_edge("fetch_umls_terms", "rank_mappings")

# 5. rank → validate
graph.add_edge("rank_mappings", "validate_mapping")

# 6. validate → gather_ancestor_candidates or end
graph.add_conditional_edges(
    "validate_mapping",
    should_refine_with_ancestors,
    {True: "gather_ancestor_candidates", False: "__end__"},
)

graph.add_edge("gather_ancestor_candidates", "__end__")

# Compiled Graph
umls_mapping_graph = graph.compile()
raw_graph = umls_mapping_graph.get_graph()
