from typing import TypedDict, List, Any, Dict

class MappingState(TypedDict, total=False):
    text: str  # 原始问卷句子
    extracted_terms: List[str]  # LLM 抽取的术语
    llm_response: Any  # 如果你有保留原始 LLM 响应
    mapped_results: List[dict]  # 备用历史字段（可留）

    # ✅ 提取 + 查询节点
    search_term: str
    ontology: str
    umls_results: List[Dict[str, Any]]

    # ✅ 排序和匹配节点
    original: str  # 当前处理的术语
    original_question: str  # 可选，给 validate 用
    candidates: List[Dict[str, Any]]  # 包含置信度、描述的候选项
    ranked_mappings: List[Dict[str, Any]]  # 如需保留排序结果

    # ✅ 验证节点 validate_mapping_node 的输出字段
    best_match_code: str
    best_match_term: str
    confidence: float
