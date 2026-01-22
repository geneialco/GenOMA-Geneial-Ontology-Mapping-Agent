"""
Agent registry and LLM configuration for the UMLS Mapping LangGraph-based Agent.

This module defines the mapping between agent tasks and their corresponding LLM models,
and builds/exposes the main agent for medical term mapping workflows.

The module supports two LLM providers:
- OpenAI: Used for local development (default)
- AWS Bedrock: Used for AWS Lambda deployments

Set the LLM_PROVIDER environment variable to "bedrock" to use AWS Bedrock models.
"""

import os
from typing import Dict

from langchain_aws import ChatBedrock
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_openai import ChatOpenAI

# Environment variable to determine which LLM provider to use
# Options: "openai" (default for local dev) or "bedrock" (for AWS deployment)
LLM_PROVIDER = os.environ.get("LLM_PROVIDER", "openai").lower()


def _create_openai_model(model: str, temperature: float = 0.0) -> ChatOpenAI:
    """
    Create an OpenAI chat model instance.

    Parameters:
        model (str): The OpenAI model identifier (e.g., "gpt-4", "gpt-4o").
        temperature (float): Sampling temperature for response variability.

    Returns:
        ChatOpenAI: Configured OpenAI chat model instance.
    """
    return ChatOpenAI(model=model, temperature=temperature)


def _create_bedrock_model(model_id: str, temperature: float = 0.0) -> ChatBedrock:
    """
    Create an AWS Bedrock chat model instance.

    Parameters:
        model_id (str): The Bedrock model identifier
            (e.g., "anthropic.claude-3-5-sonnet-20241022-v2:0").
        temperature (float): Sampling temperature for response variability.

    Returns:
        ChatBedrock: Configured Bedrock chat model instance.
    """
    return ChatBedrock(model=model_id, temperature=temperature, service_tier="flex")


# OpenAI model configurations for each agent task
# Maps task names to (model_name, temperature) tuples
OPENAI_MODEL_CONFIG = {
    "is_question_mappable_to_hpo": ("gpt-5-mini", 0.0),
    "extract_medical_term_from_survey": ("gpt-5.2", 0.0),
    "rank_mappings": ("gpt-5.2", 0.0),
    "retry_with_llm_rewrite": ("gpt-5.2", 0.0),
    "validate_mapping": ("gpt-5.2", 0.0),
    "refine_mapping": ("gpt-5.2", 0.0),
    "rank_evaluate_with_llm": ("gpt-5.2", 0.0),
    "evaluate_specificity_with_llm": ("gpt-5.2", 0.0),
}

# AWS Bedrock model configurations for each agent task
# Maps task names to (model_id, temperature) tuples
BEDROCK_MODEL_CONFIG = {
    "is_question_mappable_to_hpo": (
        "anthropic.claude-haiku-4-5-20251001-v1:0",
        0.0,
    ),
    "extract_medical_term_from_survey": (
        "anthropic.claude-sonnet-4-5-20250929-v1:0",
        0.0,
    ),
    "rank_mappings": ("anthropic.claude-sonnet-4-5-20250929-v1:0", 0.0),
    "retry_with_llm_rewrite": ("anthropic.claude-sonnet-4-5-20250929-v1:0", 0.0),
    "validate_mapping": ("anthropic.claude-sonnet-4-5-20250929-v1:0", 0.0),
    "refine_mapping": ("anthropic.claude-sonnet-4-5-20250929-v1:0", 0.0),
    "rank_evaluate_with_llm": ("anthropic.claude-sonnet-4-5-20250929-v1:0", 0.0),
    "evaluate_specificity_with_llm": (
        "anthropic.claude-sonnet-4-5-20250929-v1:0",
        0.0,
    ),
}


def _build_agent_llm_map() -> Dict[str, BaseChatModel]:
    """
    Build the agent LLM mapping based on the configured provider.

    Selects the appropriate model configuration (OpenAI or Bedrock) based on
    the LLM_PROVIDER environment variable and instantiates the corresponding
    chat models for each agent task.

    Returns:
        Dict[str, BaseChatModel]: Mapping of agent task names to LLM instances.

    Raises:
        ValueError: If an unsupported LLM_PROVIDER value is specified.
    """
    if LLM_PROVIDER == "bedrock":
        return {
            task: _create_bedrock_model(model_id, temp)
            for task, (model_id, temp) in BEDROCK_MODEL_CONFIG.items()
        }
    elif LLM_PROVIDER == "openai":
        return {
            task: _create_openai_model(model, temp)
            for task, (model, temp) in OPENAI_MODEL_CONFIG.items()
        }
    else:
        raise ValueError(
            f"Unsupported LLM_PROVIDER: {LLM_PROVIDER}. Use 'openai' or 'bedrock'."
        )


# Configuration mapping for different agent tasks to their corresponding LLM models
# Each task uses a specific model with optimized parameters for its purpose
# The provider is determined by the LLM_PROVIDER environment variable
AGENT_LLM_MAP = _build_agent_llm_map()
