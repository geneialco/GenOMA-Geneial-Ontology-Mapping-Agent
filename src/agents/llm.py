"""
LLM factory module for the UMLS Mapping LangGraph-based Agent.

Note: This module is kept for potential future use. Currently, LLM instances
are configured directly in src/config/agents.py via AGENT_LLM_MAP.
"""

from langchain_openai import ChatOpenAI


def get_llm_by_type(model_type: str) -> ChatOpenAI:
    """
    Create a ChatOpenAI instance with the specified model.

    Args:
        model_type: The OpenAI model name (e.g., 'gpt-4', 'gpt-4o')

    Returns:
        ChatOpenAI: Configured LLM instance with temperature=0
    """
    return ChatOpenAI(model=model_type, temperature=0)
