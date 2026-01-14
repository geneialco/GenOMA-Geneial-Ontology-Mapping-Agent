from langgraph.graph import StateGraph

from experiments.ablation_nodes import gather_ancestor_candidates_node
from src.graph.nodes import (
    extract_medical_terms_checkbox_node,
    extract_medical_terms_radio_node,
    fetch_umls_terms_node,
    is_question_mappable_node,
    rank_mappings_node,
    retry_with_llm_rewrite_node,
)
from src.graph.types import MappingState

# -------- Toggle for ablation --------
USE_VALIDATE = False  # set to True to restore the original validate path


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


# ---- Shim: promote ranked results into validated_mappings (for no-validate ablation) ----
def promote_ranked_to_validated_node(state: MappingState) -> MappingState:
    """
    Copies ranked mappings into `validated_mappings` so downstream nodes
    (like gather_ancestor_candidates) can reuse the same key.
    Ensures a `confidence` field exists (falls back to `score` or 1.0).
    """
    ranked = state.get("ranked_mappings") or []
    if not ranked:
        # Fallback: try to construct minimal ranked entries from umls_mappings
        ranked = []
        for m in state.get("umls_mappings", []):
            cands = m.get("candidates") or []
            if cands:
                top = cands[0] or {}
                ranked.append(
                    {
                        "term": m.get("term"),
                        "cui": top.get("cui"),
                        "confidence": top.get("score", top.get("confidence", 1.0)),
                        "source": "fallback_from_umls",
                    }
                )
    # Normalize confidence
    for item in ranked:
        if "confidence" not in item:
            item["confidence"] = item.get("score", 1.0)
    state["validated_mappings"] = ranked
    return state


# Create a graph
graph = StateGraph(MappingState)

# Add all nodes
graph.add_node("is_question_mappable", is_question_mappable_node)
graph.add_node("extract_medical_terms_checkbox", extract_medical_terms_checkbox_node)
graph.add_node("extract_medical_terms_radio", extract_medical_terms_radio_node)
graph.add_node("fetch_umls_terms", fetch_umls_terms_node)
graph.add_node("rank_mappings", rank_mappings_node)
graph.add_node("retry_with_llm_rewrite", retry_with_llm_rewrite_node)
graph.add_node("gather_ancestor_candidates", gather_ancestor_candidates_node)
graph.add_node(
    "choose_extraction", lambda state: state
)  # The transit node itself does not process

# New: Add promote node only when validate is not used
if not USE_VALIDATE:
    graph.add_node("promote_ranked_to_validated", promote_ranked_to_validated_node)
else:
    # If you want to restore the original path, import it here and add the validate_mapping_node:
    from src.graph.nodes import validate_mapping_node

    graph.add_node("validate_mapping", validate_mapping_node)

# Set up entry
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

# 4. fetch → retry or rank
graph.add_conditional_edges(
    "fetch_umls_terms",
    should_retry_with_llm_rewrite,
    {True: "retry_with_llm_rewrite", False: "rank_mappings"},
)

# 5. retry → fetch or end
graph.add_conditional_edges(
    "retry_with_llm_rewrite",
    should_retry_with_llm_rewrite,
    {True: "fetch_umls_terms", False: "__end__"},
)

# 6/7. rank → (no-validate path) promote → gather_or_end
if not USE_VALIDATE:
    graph.add_edge("rank_mappings", "promote_ranked_to_validated")
    graph.add_conditional_edges(
        "promote_ranked_to_validated",
        should_refine_with_ancestors,
        {True: "gather_ancestor_candidates", False: "__end__"},
    )
else:
    # rank → validate → gather_or_end
    graph.add_edge("rank_mappings", "validate_mapping")
    graph.add_conditional_edges(
        "validate_mapping",
        should_refine_with_ancestors,
        {True: "gather_ancestor_candidates", False: "__end__"},
    )

graph.add_edge("gather_ancestor_candidates", "__end__")

# Compiled Graph
umls_mapping_graph = graph.compile()
raw_graph = umls_mapping_graph.get_graph()
