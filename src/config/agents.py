
from langchain_openai import ChatOpenAI

# We use GPT-4 for all agents
llm = ChatOpenAI(model="gpt-4", temperature=0)

# Identify the nodes used llm here
AGENT_LLM_MAP = {
    "extract_medical_term_from_survey": llm,
    "is_question_mappable_to_hpo": llm,
    "validate_mapping": llm,
    "rank_mappings": llm
}
