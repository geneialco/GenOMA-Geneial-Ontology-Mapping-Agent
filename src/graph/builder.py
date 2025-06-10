from langgraph.graph import StateGraph
from src.graph.types import MappingState
from src.graph.nodes import (
    is_question_mappable_node,
    extract_medical_terms_node,
    fetch_umls_terms_node,
    rank_mappings_node,
    validate_mapping_node,  
)

def build_graph():
    builder = StateGraph(MappingState)

    # Add all nodes
    builder.add_node("is_mappable", is_question_mappable_node)
    builder.add_node("extract_terms", extract_medical_terms_node)
    builder.add_node("fetch_umls_terms", fetch_umls_terms_node)
    builder.add_node("rank_mappings", rank_mappings_node)
    builder.add_node("validate_mapping", validate_mapping_node) 

    # Conditional edges
    builder.add_conditional_edges(
        "is_mappable",
        lambda state: "extract_terms" if state.get("is_mappable") else "__end__"
    )

    # Connect each stage in order
    builder.add_edge("extract_terms", "fetch_umls_terms")
    builder.add_edge("fetch_umls_terms", "rank_mappings")
    builder.add_edge("rank_mappings", "validate_mapping")  

    # Set entry and finish points
    builder.set_entry_point("is_mappable")
    builder.set_finish_point("validate_mapping")  # ✅ Change finish point to validate

    return builder.compile()
