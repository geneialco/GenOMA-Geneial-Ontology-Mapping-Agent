from langchain_openai import ChatOpenAI

def get_llm_by_type(model_type: str):
    return ChatOpenAI(model=model_type, temperature=0)
