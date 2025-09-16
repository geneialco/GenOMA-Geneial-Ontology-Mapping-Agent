"""
LangGraph state machine builder for the UMLS Mapping LangGraph-based Agent.
This module defines the complete workflow graph that orchestrates the medical term
mapping process from survey questions to standardized ontology terms.
"""

from langgraph.graph import StateGraph
from src.graph.nodes import (
    is_question_mappable_node,
    extract_medical_terms_checkbox_node,
    extract_medical_terms_short_node,
    extract_medical_terms_radio_node,
    fetch_umls_terms_node,
    rank_mappings_node,
    validate_mapping_node,
    retry_with_llm_rewrite_node,
    gather_ancestor_candidates_node
)
from src.graph.types import MappingState


def should_retry_with_llm_rewrite(state: MappingState) -> bool:
    """
    Determine if the workflow should retry with LLM rewrite.
    
    This function checks if any extracted terms failed to map to ontology candidates
    and if we haven't exceeded the maximum retry limit.
    
    Args:
        state (MappingState): Current workflow state
    
    Returns:
        bool: True if retry is needed, False otherwise
    """
    retry_count = state.get("retry_count", 0)
    if retry_count >= 10:  # Maximum retry limit to prevent infinite loops
        return False
    
    umls_mappings = state.get("umls_mappings", [])
    for mapping in umls_mappings:
        if not mapping.get("candidates"):  # No candidates found for this term
            return True
    return False


def should_refine_with_ancestors(state: MappingState) -> bool:
    """
    Determine if the workflow should refine mappings using ancestor concepts.
    
    This function checks if the confidence of the best match is below the threshold
    and if ancestor-based refinement could improve the mapping quality.
    
    Args:
        state (MappingState): Current workflow state
    
    Returns:
        bool: True if ancestor refinement is needed, False otherwise
    """
    validated_list = state.get("validated_mappings", [])
    if not validated_list or not isinstance(validated_list, list):
        return False
    
    confidence = validated_list[0].get("confidence", 1.0)
    return confidence < 0.9  # Threshold for triggering ancestor refinement


def choose_extraction_node(state: MappingState) -> str:
    """
    Route to the appropriate medical term extraction node based on field type.
    
    Different survey field types require different extraction strategies:
    - checkbox: Multiple selection items
    - short: Short text input fields
    - radio: Single selection items (default)
    
    Args:
        state (MappingState): Current workflow state
    
    Returns:
        str: Name of the extraction node to route to
    """
    field_type = state.get("field_type", "").lower()
    if field_type == "checkbox":
        return "extract_medical_terms_checkbox"
    if field_type == "short":
        return "extract_medical_terms_short"
    else:
        return "extract_medical_terms_radio"  # Default for radio and other types


# Create the main LangGraph state machine
graph = StateGraph(MappingState)

# Add all workflow nodes to the graph
# Each node represents a specific step in the medical term mapping process
graph.add_node("is_question_mappable", is_question_mappable_node)
graph.add_node("extract_medical_terms_checkbox", extract_medical_terms_checkbox_node)
graph.add_node("extract_medical_terms_short", extract_medical_terms_short_node)
graph.add_node("extract_medical_terms_radio", extract_medical_terms_radio_node)
graph.add_node("fetch_umls_terms", fetch_umls_terms_node)
graph.add_node("rank_mappings", rank_mappings_node)
graph.add_node("validate_mapping", validate_mapping_node)
graph.add_node("retry_with_llm_rewrite", retry_with_llm_rewrite_node)
graph.add_node("gather_ancestor_candidates", gather_ancestor_candidates_node)
graph.add_node("choose_extraction", lambda state: state)  # Routing node that doesn't process state

# Set the entry point for the workflow
graph.set_entry_point("is_question_mappable")

# 1. Question mappability check → Route based on mappability
graph.add_conditional_edges(
    "is_question_mappable",
    lambda state: state.get("is_mappable", False),
    {
        True: "choose_extraction",   # Proceed to extraction if mappable
        False: "__end__"             # End workflow if not mappable
    }
)

# 2. Extraction routing → Route to appropriate extraction node
graph.add_conditional_edges(
    "choose_extraction",
    choose_extraction_node,
    {
        "extract_medical_terms_checkbox": "extract_medical_terms_checkbox",
        "extract_medical_terms_short": "extract_medical_terms_short",
        "extract_medical_terms_radio": "extract_medical_terms_radio"
    }
)

# 3. After extraction → Fetch UMLS terms
graph.add_edge("extract_medical_terms_checkbox", "fetch_umls_terms")
graph.add_edge("extract_medical_terms_short", "fetch_umls_terms")
graph.add_edge("extract_medical_terms_radio", "fetch_umls_terms")

# 4. After fetching → Retry or rank based on results
graph.add_conditional_edges(
    "fetch_umls_terms",
    should_retry_with_llm_rewrite,
    {
        True: "retry_with_llm_rewrite",  # Retry if no candidates found
        False: "rank_mappings"           # Rank if candidates found
    }
)

# 5. After retry → Fetch again or end
graph.add_conditional_edges(
    "retry_with_llm_rewrite",
    should_retry_with_llm_rewrite,
    {
        True: "fetch_umls_terms",  # Try fetching with rewritten terms
        False: "__end__"           # End if max retries reached
    }
)

# 6. After ranking → Validate mappings
graph.add_edge("rank_mappings", "validate_mapping")

# 7. After validation → Refine with ancestors or end
graph.add_conditional_edges(
    "validate_mapping",
    should_refine_with_ancestors,
    {
        True: "gather_ancestor_candidates",  # Refine if confidence is low
        False: "__end__"                     # End if confidence is sufficient
    }
)

# 8. After ancestor gathering → End workflow
graph.add_edge("gather_ancestor_candidates", "__end__")

# Compile the graph into an executable workflow
umls_mapping_graph = graph.compile()
raw_graph = umls_mapping_graph.get_graph()

def build_umls_mapper_graph():
    """
    Build and return the compiled UMLS mapping graph.
    
    This function creates the complete LangGraph workflow for medical term mapping
    and returns the compiled graph ready for execution.
    
    Returns:
        CompiledGraph: The compiled LangGraph workflow for UMLS mapping
    """
    return umls_mapping_graph
