"""
LLM model configuration for the UMLS Mapping LangGraph-based Agent.
This module defines the mapping between agent tasks and their corresponding LLM models.
"""

from langchain_openai import ChatOpenAI

# Configuration mapping for different agent tasks to their corresponding LLM models
# Each task uses a specific model with optimized parameters for its purpose
AGENT_LLM_MAP = {
    # Question mappability assessment - uses GPT-4o for high accuracy
    "is_question_mappable_to_hpo": ChatOpenAI(model="gpt-4o", temperature=0.0),
    
    # Medical term extraction - uses GPT-5 for advanced reasoning capabilities
    "extract_medical_term_from_survey": ChatOpenAI(model="gpt-5"),
    
    # Candidate ranking - uses GPT-4 with zero temperature for deterministic results
    "rank_mappings": ChatOpenAI(model="gpt-4", temperature=0.0),
    
    # Retry with rewrite - uses GPT-5 with higher temperature for creative alternatives
    "retry_with_llm_rewrite": ChatOpenAI(model="gpt-5"), 
    
    # Mapping validation - uses GPT-4 with zero temperature for consistent validation
    "validate_mapping": ChatOpenAI(model="gpt-4", temperature=0.0),
    
    # Mapping refinement - uses GPT-4 for precise refinement tasks
    "refine_mapping": ChatOpenAI(model="gpt-4", temperature=0.0),
    
    # Ranking evaluation - uses GPT-4o for high-quality evaluation
    "rank_evaluate_with_llm": ChatOpenAI(model="gpt-4o", temperature=0.0),
    
    # Specificity evaluation - uses GPT-5 for nuanced specificity assessment
    "evaluate_specificity_with_llm": ChatOpenAI(model="gpt-5")
}