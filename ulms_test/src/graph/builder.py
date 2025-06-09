from langgraph.graph import StateGraph
from src.graph.types import MappingState
from src.graph.nodes import (
    is_question_mappable_node,
    extract_medical_terms_node,
    fetch_umls_terms_node,
    rank_mappings_node,
    validate_mapping_node,  # ✅ 新增
)

def build_graph():
    builder = StateGraph(MappingState)

    # 添加所有节点
    builder.add_node("is_mappable", is_question_mappable_node)
    builder.add_node("extract_terms", extract_medical_terms_node)
    builder.add_node("fetch_umls_terms", fetch_umls_terms_node)
    builder.add_node("rank_mappings", rank_mappings_node)
    builder.add_node("validate_mapping", validate_mapping_node)  # ✅ 新增

    # 条件判断路径
    builder.add_conditional_edges(
        "is_mappable",
        lambda state: "extract_terms" if state.get("is_mappable") else "__end__"
    )

    # 顺序连接每个阶段
    builder.add_edge("extract_terms", "fetch_umls_terms")
    builder.add_edge("fetch_umls_terms", "rank_mappings")
    builder.add_edge("rank_mappings", "validate_mapping")  # ✅ 新增连接

    # 设置入口和终点
    builder.set_entry_point("is_mappable")
    builder.set_finish_point("validate_mapping")  # ✅ 修改终点为 validate

    return builder.compile()
