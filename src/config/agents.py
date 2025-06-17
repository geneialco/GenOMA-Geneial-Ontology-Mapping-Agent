from langchain_openai import ChatOpenAI

# We use GPT-4 for all agents
AGENT_LLM_MAP = {
    "is_question_mappable_to_hpo": ChatOpenAI(model="gpt-4", temperature=0.0),
    "extract_medical_term_from_survey": ChatOpenAI(model="gpt-4o", temperature=0.0),
    "normalize_medical_terms": ChatOpenAI(model="gpt-4", temperature=0.0),
    "rank_mappings": ChatOpenAI(model="gpt-4", temperature=0.0),
    "retry_with_llm_rewrite": ChatOpenAI(model="gpt-4o", temperature=0.8),  # increase the temperature getting more possibility output.
    "validate_mapping": ChatOpenAI(model="gpt-4", temperature=0.0),
    "refine_mapping": ChatOpenAI(model="gpt-4", temperature=0.0),
    "rank_evaluate_with_llm": ChatOpenAI(model="gpt-4o", temperature=0.0),
    "evaluate_specificity_with_llm": ChatOpenAI(model="gpt-4o", temperature=0.0)
}