# src/graph/builder.py

from langgraph.graph import StateGraph
from src.graph.nodes import (
    is_question_mappable_node,
    extract_medical_terms_node,
    fetch_umls_terms_node,
    rank_mappings_node,
    validate_mapping_node  # ✅ 新增导入
)
from src.graph.types import MappingState

def build_test_graph():
    builder = StateGraph(MappingState)

    # 注册所有节点
    builder.add_node("is_question_mappable", is_question_mappable_node)
    builder.add_node("extract_medical_terms", extract_medical_terms_node)
    builder.add_node("fetch_umls_terms", fetch_umls_terms_node)
    builder.add_node("rank_mappings", rank_mappings_node)
    builder.add_node("validate_mappings", validate_mapping_node)  

    # 构建线性流程
    builder.set_entry_point("is_question_mappable")
    builder.add_edge("is_question_mappable", "extract_medical_terms")
    builder.add_edge("extract_medical_terms", "fetch_umls_terms")
    builder.add_edge("fetch_umls_terms", "rank_mappings")
    builder.add_edge("rank_mappings", "validate_mappings")  # ✅ 添加连接
    builder.set_finish_point("validate_mappings")  # ✅ 最终节点

    return builder.compile()
