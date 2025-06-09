# UMLS Mapping LangGrapt based Agent 

A modular agent system for mapping clinical or survey questions to standardized biomedical ontologies, including Human Phenotype Ontology (HPO). Built with [LangGraph](https://github.com/langchain-ai/langgraph), the agent integrates LLM-based term extraction, candidate ranking, and mapping validation for robust symptom normalization workflows.

## 📁 Project Structure

- `src/`: Core source code directory
  - `agents/`: LangGraph agent and LLM setup
    - `agents.py`: Agent registry and execution logic
    - `llm.py`: LLM model configuration
  - `config/`: Optional shared configuration
    - `agents.py`: Agent-level config helpers
  - `graph/`: LangGraph flow, node logic, and state schema
    - `builder.py`: Defines LangGraph state machine
    - `nodes.py`: Node functions (e.g., extract, rank, validate)
    - `types.py`: Defines the MappingState TypedDict
  - `prompts/`: Jinja2 prompt templates for each LLM node
    - `extract_medical_term_from_survey.md`: Extracts symptom terms
    - `is_mappable.md`: Filters non-medical questions
    - `rank_mappings.md`: Ranks ontology candidates
    - `validate_mapping.md`: Validates final selected mapping
    - `umls_mapper.md`: Optional agent prompt wrapper
    - `template.py`: Jinja2 rendering utility
  - `tools/`: Utility scripts for external API interaction
    - `ums_api.py`: Interfaces with UMLS-compatible ontology API
- `run.py`: Main entry point for running the full pipeline
- `.env`: Environment configuration (e.g., OpenAI API key)
- `README.md`: Project documentation



## 🔍 Key Features

- ✅ **LLM-Based Extraction**: Identifies clinically relevant terms from free-text input
- 🌐 **Ontology Querying**: Calls UMLS-compatible APIs to retrieve candidate terms from ontologies (e.g., HPO)
- 📊 **Candidate Ranking**: Uses LLM to assign confidence scores to mapped terms
- 🧠 **Mapping Validation**: Chooses the most appropriate term using question context
- ⚙️ **Modular Nodes**: Each step is implemented as a reusable node in a LangGraph state graph

## ⚗️ Agent Nodes

- `is_question_mappable_node`: Filters non-medical questions
- `extract_medical_terms_node`: Extracts symptom terms from user input
- `fetch_umls_terms_node`: Queries UMLS-like API for term candidates
- `rank_mappings_node`: Ranks candidate ontology terms
- `validate_mapping_node`: Validates and selects the best match

## 📊 Output Example

```json
{
  "text": "Does your child have chest pain?",
  "extracted_terms": ["chest pain"],
  "original": "chest pain",
  "candidates": [
    {
      "code": "HP:0100749",
      "term": "Chest pain",
      "confidence": 0.95
    },
    ...
  ],
  "best_match_code": "HP:0100749",
  "best_match_term": "Chest pain",
  "confidence": 0.95
}
