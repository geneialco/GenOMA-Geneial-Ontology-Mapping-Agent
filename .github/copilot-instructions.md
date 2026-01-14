# GenOMA (Geneial Ontology Mapping Agent) Copilot Instructions

## Project Overview
GenOMA is a LangGraph-based agent designed to map clinical/survey text to Human Phenotype Ontology (HPO) terms. It uses a multi-step pipeline: Extraction -> Fetching -> Ranking -> Validation -> Retry.

## Architecture & Core Concepts

### LangGraph Workflow
- **Graph Definition**: `src/graph/builder.py` defines the state machine.
- **State**: `MappingState` (in `src/graph/types.py`) is the central data structure passed between nodes. Always check this TypedDict when adding new fields.
- **Nodes**: `src/graph/nodes.py` contains the logic for each step.
  - `is_question_mappable`: Filters irrelevant inputs.
  - `extract_medical_terms_*`: Specialized extractors for different input types (radio, checkbox, short).
  - `fetch_umls_terms`: Queries external APIs (HPO).
  - `rank_mappings`: Uses LLM to score candidates.
  - `validate_mapping`: Final check of the best match.

### External Integrations
- **Ontology API**: The agent queries `https://ontology.jax.org/api/hp/search` directly in `src/graph/nodes.py`.
- **LLM**: OpenAI models via LangChain. Configuration is in `src/agents.py`.

## Development Workflows

### Testing & Execution
- **Primary Interface**: `experiments/test.ipynb` is the main way to run and test the agent.
  - Use `experiments/test.ipynb` for single-query tests and batch processing (Excel).
- **FastAPI Stub**: `main.py` is currently a placeholder/stub. Do not use it as the primary entry point for agent logic.
- **Environment**: Ensure `.env` contains `OPENAI_API_KEY`.

### Modifying the Agent
1.  **Prompts**: Edit markdown templates in `src/prompts/`.
    - Prompts are loaded via `src/prompts/template.py`.
2.  **New Nodes**:
    - Define the function in `src/graph/nodes.py`.
    - Add to `MappingState` in `src/graph/types.py` if new state fields are needed.
    - Register the node and edges in `src/graph/builder.py`.

## Coding Conventions

- **State Management**: Always return a dictionary with *only* the fields you want to update in the state. LangGraph merges these updates.
  ```python
  # Good
  return {**state, "new_field": value}
  ```
- **Error Handling**: Nodes should handle API failures gracefully (e.g., returning empty lists) to prevent the graph from crashing.
- **Retries**: Implement retry logic within nodes (like `mappability_retry_count`) or using LangGraph's retry policies if applicable.
- **Type Hinting**: Use `MappingState` for node arguments and return types.

## Key Files Map
- `src/graph/builder.py`: Graph orchestration.
- `src/graph/nodes.py`: Business logic for each step.
- `src/graph/types.py`: Data schema.
- `src/prompts/`: LLM prompt templates.
- `experiments/test.ipynb`: Interactive testing playground.
