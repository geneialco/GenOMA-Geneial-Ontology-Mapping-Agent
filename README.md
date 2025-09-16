# UMLS Mapping LangGraph-Based Agent
A modular agent system for mapping clinical or survey questions to standardized biomedical ontologies (e.g., HPO) using LangGraph. The agent integrates LLM-based term extraction, ontology candidate retrieval, ranking, and validation to produce robust, context-aware mappings suitable for symptom normalization workflows.

## 🔍 Key Features
- ✅ **LLM-Based Extraction**: Identifies clinically relevant terms from free-text input
- 🌐 **Ontology Querying**: Calls UMLS-compatible APIs to retrieve candidate terms from ontologies (e.g., HPO)
- 📊 **Candidate Ranking**: Uses LLM to assign confidence scores to mapped terms
- 🧠 **Mapping Validation**: Chooses the most appropriate term using question context
- ⚙️ **Modular Nodes**: Each step is implemented as a reusable node in a LangGraph state graph

## Requirements
### 1. Python 3.11 (recommended)
### 2. API keys: OPENAI_API_KEY (necessary)
### 3. umls server API (necessary):You can fellow this link: https://github.com/geneialco/umls-server

## Installation step
Linux / macOS (bash)
```bash
# create venv
python -m venv .venv
source .venv/bin/activate
# install deps
pip install -r requirements.txt
# prepare env file
cp .env.example .env
```

## .env.example
Linux / macOS (dotenv)
```dotenv
OPENAI_API_KEY=your_key_here
```

## How to Use
> Prereqs: complete **Installation**, and set `OPENAI_API_KEY` in `.env`.
> umls server API is ready (API_BASE_URL = "http://localhost:8000/")

### 1 Single text (quick test in `test_ML4H.ipynb`)
Open `test_ML4H.ipynb`, find the first cell:

```python
# Use a data to test before officially starting the running
from src.graph.builder import umls_mapping_graph
result = umls_mapping_graph.invoke({
    "text": "Gum disease (loss of tissue around teeth)",
    "field_type": "short"
})
print(result)
```
Replace the value of "text" with the question/phrase you want to map.
Set "field_type" based on your input:
    radio — (default) for yes/no questions or regular sentences.
    checkbox — for multi-select questions with options.
    short — for short phrases (typically < 5 meaningful words).
The cell prints a dict with keys like:
extracted_terms, candidates, best_match_code, best_match_term, confidence.

### 2 Batch mapping from Excel (in test_ML4H.ipynb)
Run the cells after the single-text demo in test_ML4H.ipynb following this order:
read data → batch process → export results.
Input: an Excel file (default gc.xlsx) with a column named Question.
The notebook processes each row and creates three new columns:
    agent_term — the term extracted by the agent
    agent_code — the mapped HPO code
    confidence — confidence score (0–1)

Typical variables in the notebook (adjust if needed):
    INPUT_PATH = "gc.xlsx"
    OUTPUT_PATH = "mapped_gc.xlsx"
    QUESTION_COL = "Question"
    DEFAULT_FIELD_TYPE = "radio"  # change to 'checkbox' or 'short' if appropriate

## 📁 Project Structure
src/
  agents/
    __init__.py
    agents.py        # agent registry & high-level runner
    llm.py           # LLM config (model, params, retries)
  config/
    agents.py        # shared config helpers / defaults
  graph/
    __init__.py
    builder.py
    builder_without_rank_node.py
    builder_without_retry_node.py
    builder_without_validate_node.py
    nodes.py         # extract / fetch / rank / validate / retry nodes
    types.py         # MappingState TypedDict
  prompts/
    evaluate_specificity_with_llm.md
    extract_medical_term_checkbox_from_survey.md
    extract_medical_term_radio_from_survey.md
    extract_medical_term_short_from_survey.md
    is_mappable.md
    rank_evaluate_with_llm.md
    rank_mappings.md
    refine_mapping.md
    retry_with_llm_rewrite.md
    template.py
    validate_mapping.md
  tools/
    __init__.py
    flatten_names.py
    umls_tools.py     # UMLS/HPO API helpers (env-based)
# repo root
main.py               # CLI entry
requirements.txt
.env.example          # fill & rename to .env
eva_ML4H.ipynb        # evaluation / analysis
test_ML4H.ipynb       # tests code 
test_ML4H_nodes_test.ipynb
gc.xlsx               # sample input (questions)
mapped_gc.xlsx        # sample output (mappings)


## ⚗️ Agent Nodes

- `is_question_mappable` — Detects whether the input is a mappable medical question.
- `choose_extraction` — Routes to the proper extractor (`radio` / `checkbox` / `short`).
- `extract_medical_terms_radio` — Extracts terms from single-choice questions.
- `extract_medical_terms_checkbox` — Extracts multiple terms from multi-select questions.
- `extract_medical_terms_short` — Extracts terms from short/free-text prompts.
- `fetch_umls_terms` — Calls a UMLS/HPO API to retrieve candidate ontology terms.
- `rank_mappings` — Ranks candidates with context and assigns confidence scores.
- `validate_mapping` — Final sanity check and selection (`best_match_*`).
- `retry_with_llm_rewrite` — Rewrites and retries when confidence is low.
- `gather_ancestor_candidates` — Fetches ancestor/parent concepts for the matched term.


