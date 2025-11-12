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
    # gather_ancestor_candidates_node  # ← 移除
)
from src.graph.types import MappingState


def should_retry_with_llm_rewrite(state: MappingState) -> bool:
    """
    Decide whether to retry with LLM rewrite AFTER validation.
    Trigger if best confidence < 0.9 and we haven't exceeded 5 retries.
    """
    retry_count = state.get("retry_count", 0)
    if retry_count >= 5:  # ← 将最大重试次数改为 5
        return False

    validated_list = state.get("validated_mappings", [])
    if not validated_list or not isinstance(validated_list, list):
        return False

    confidence = validated_list[0].get("confidence", 1.0)
    return confidence < 0.9


def choose_extraction_node(state: MappingState) -> str:
    """
    Route to the appropriate medical term extraction node based on field type.
    """
    field_type = state.get("field_type", "").lower()
    if field_type == "checkbox":
        return "extract_medical_terms_checkbox"
    if field_type == "short":
        return "extract_medical_terms_short"
    else:
        return "extract_medical_terms_radio"


# Create the main LangGraph state machine
graph = StateGraph(MappingState)

# Add all workflow nodes to the graph
graph.add_node("is_question_mappable", is_question_mappable_node)
graph.add_node("extract_medical_terms_checkbox", extract_medical_terms_checkbox_node)
graph.add_node("extract_medical_terms_short", extract_medical_terms_short_node)
graph.add_node("extract_medical_terms_radio", extract_medical_terms_radio_node)
graph.add_node("fetch_umls_terms", fetch_umls_terms_node)
graph.add_node("rank_mappings", rank_mappings_node)
graph.add_node("validate_mapping", validate_mapping_node)
graph.add_node("retry_with_llm_rewrite", retry_with_llm_rewrite_node)
# graph.add_node("gather_ancestor_candidates", gather_ancestor_candidates_node)  # ← 移除
graph.add_node("choose_extraction", lambda state: state)  # Routing node

# Entry
graph.set_entry_point("is_question_mappable")

# 1) 是否可映射
graph.add_conditional_edges(
    "is_question_mappable",
    lambda state: state.get("is_mappable", False),
    {
        True: "choose_extraction",
        False: "__end__"
    }
)

# 2) 按字段类型选择提取节点
graph.add_conditional_edges(
    "choose_extraction",
    choose_extraction_node,
    {
        "extract_medical_terms_checkbox": "extract_medical_terms_checkbox",
        "extract_medical_terms_short": "extract_medical_terms_short",
        "extract_medical_terms_radio": "extract_medical_terms_radio"
    }
)

# 3) 提取后 → 拉取候选
graph.add_edge("extract_medical_terms_checkbox", "fetch_umls_terms")
graph.add_edge("extract_medical_terms_short", "fetch_umls_terms")
graph.add_edge("extract_medical_terms_radio", "fetch_umls_terms")

# 4) 拉取候选后 → 直接进入排序（不再在此处触发重写重试）
graph.add_edge("fetch_umls_terms", "rank_mappings")

# 5) 排序后 → 校验
graph.add_edge("rank_mappings", "validate_mapping")

# 6) 校验后 → 若低于阈值则重写重试；否则结束
graph.add_conditional_edges(
    "validate_mapping",
    should_retry_with_llm_rewrite,
    {
        True: "retry_with_llm_rewrite",
        False: "__end__"
    }
)

# 7) 重写后 → 回到拉取候选（形成闭环，最多 5 次；retry_count 应在重写节点内部自增）
graph.add_edge("retry_with_llm_rewrite", "fetch_umls_terms")

# Compile
umls_mapping_graph = graph.compile()
raw_graph = umls_mapping_graph.get_graph()

def build_umls_mapper_graph():
    """Return the compiled LangGraph workflow."""
    return umls_mapping_graph
