from langchain_openai import ChatOpenAI

# We use the same llm for all agents

def get_llm_by_type(model_type: str):
    return ChatOpenAI(model=model_type, temperature=0)
