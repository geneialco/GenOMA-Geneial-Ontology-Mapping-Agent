# GenOMA (Geneial Ontology Mapping Agent)

Instructions for AI agents working in this repository.

## Project Overview

GenOMA is a LangGraph-based agent that maps clinical or survey text to **Human Phenotype Ontology (HPO)** terms.

The agent follows a multi-step pipeline:
**Extraction → Fetching → Ranking → Validation → Retry**

## Architecture & Core Concepts

### LangGraph Workflow

* **Graph Definition**: `src/graph/builder.py` defines the LangGraph state machine.
* **State**: `MappingState` (in `src/graph/types.py`) is the central TypedDict passed between nodes.

  * Always update `MappingState` when introducing new state fields.
* **Nodes**: Implemented in `src/graph/nodes.py`, including:

  * `is_question_mappable` — filters irrelevant inputs
  * `extract_medical_terms_*` — specialized extractors (radio, checkbox, short text)
  * `fetch_umls_terms` — queries ontology APIs
  * `rank_mappings` — LLM-based scoring of candidates
  * `validate_mapping` — final selection and validation

### External Integrations

* **Ontology API**

  * Direct calls to: `https://ontology.jax.org/api/hp/search`
  * Implemented in `src/graph/nodes.py`
* **LLM Providers**

  * OpenAI and AWS Bedrock via LangChain
  * Configuration: `src/graph/agent_config.py`
  * Provider selected via `LLM_PROVIDER` environment variable:

    * `openai` (default, local development)
    * `bedrock` (AWS Lambda; uses Claude 3.5 Sonnet)

## Development & Execution

### Testing

* **Primary Interface**: `experiments/test.ipynb`

  * Used for single-query testing and batch processing (Excel inputs)
* **FastAPI Stub**: `main.py`

  * Placeholder only
  * Not the primary execution path for agent logic

### Environment Configuration

* **Local Development**

  * `.env` must include:

    * `OPENAI_API_KEY`
    * `LLM_PROVIDER=openai` (default)
* **AWS Deployment**

  * `LLM_PROVIDER=bedrock` is set automatically via `template.yaml`

## Modifying the Agent

### Prompts

* Stored as Markdown templates in `src/prompts/`
* Loaded via `src/prompts/template.py`

### Adding or Updating Nodes

1. Implement the node function in `src/graph/nodes.py`
2. Add new fields to `MappingState` in `src/graph/types.py` if required
3. Register the node and edges in `src/graph/builder.py`

## Coding Conventions

### State Management

* Nodes must return **only** the fields they intend to update.
* LangGraph merges updates into the existing state.

```python
# Correct pattern
return {**state, "new_field": value}
```

### Error Handling

* Nodes must fail gracefully.
* Prefer empty results or safe defaults over raising exceptions that crash the graph.

### Retries

* Implement retry logic:

  * Internally within nodes (e.g., `mappability_retry_count`)
  * Or via LangGraph retry policies where appropriate

### Typing

* Use `MappingState` for all node input and return type hints.

## Key Files Reference

* `src/graph/agent_config.py` — LLM provider configuration
* `src/graph/builder.py` — Graph orchestration
* `src/graph/nodes.py` — Core agent logic
* `src/graph/types.py` — State schema
* `src/prompts/` — Prompt templates
* `experiments/test.ipynb` — Interactive testing
* `template.yaml` — AWS SAM deployment (sets `LLM_PROVIDER=bedrock`)
