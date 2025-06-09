
from langchain_openai import ChatOpenAI


llm = ChatOpenAI(model="gpt-4o", temperature=0)


AGENT_LLM_MAP = {
    "extract_medical_term_from_survey": llm,
    "is_question_mappable_to_hpo": llm,
    "validate_mapping": llm,
    "rank_mappings": llm
}
