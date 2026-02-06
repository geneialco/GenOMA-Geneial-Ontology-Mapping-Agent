# GenOMA (Geneial Ontology Mapping Agent)

A modular agent system for mapping clinical or survey questions to standardized biomedical ontologies (e.g., HPO) using LangGraph. The agent integrates LLM-based term extraction, ontology candidate retrieval, ranking, and validation to produce robust, context-aware mappings suitable for symptom normalization workflows.

## 🔍 Key Features

- **LLM-Based Extraction**: Identifies clinically relevant terms from free-text input
- **Ontology Querying**: Calls `ontology.jax.org` APIs to retrieve candidate terms from ontologies (e.g., HPO)
- **Candidate Ranking**: Uses LLM to assign confidence scores to mapped terms
- **Mapping Validation**: Chooses the most appropriate term using question context
- **Modular Nodes**: Each step is implemented as a reusable node in a LangGraph state graph
- **FastAPI Server**: Optional REST API for programmatic access

## Requirements

- **Python 3.11+** (recommended)
- **LLM Provider**: One of the following:
  - **OpenAI API Key** (for local development)
  - **AWS Bedrock Access** (for AWS Lambda deployment)

## Installation

Option A — manual venv + pip requirements:

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Minimal runtime deps (used by AWS SAM/Lambda builds)
pip install -r src/requirements.txt

# Optional: FastAPI server tooling
pip install -r requirements-server.txt

# Optional: notebooks/data analysis
pip install -r requirements-analysis.txt
```

Option B — uv-managed env with dependency groups:

```bash
uv venv .venv
source .venv/bin/activate

# Runtime only (Lambda/SAM)
uv sync --frozen

# Add FastAPI serer tooling
uv sync --extras server

# Add notebooks/data analysis
uv sync --extras analysis
```

**Configuration**:

Create a `.env` file in the project root:

```dotenv
# OpenAI API key (for local development)
OPENAI_API_KEY=your_key_here

# LLM provider: "openai" (default for local) or "bedrock" (for AWS)
LLM_PROVIDER=openai
```

**Note**: When deployed to AWS Lambda, `LLM_PROVIDER` is automatically set to `bedrock` in `template.yaml`.

## How to Use

**Prerequisites**: Complete installation and set your `OPENAI_API_KEY` in `.env`.

### Option 1: Interactive Notebook (`experiments/test.ipynb`)

Open `experiments/test.ipynb` in Jupyter and run the first cell:

```python
# Single text mapping test
from src.graph.builder import umls_mapping_graph

result = umls_mapping_graph.invoke({
    "text": "Gum disease (loss of tissue around teeth)",
    "field_type": "short"
})
print(result)
```

**Parameters**:

- `text`: The question/phrase to map
- `field_type`: One of:
  - `"radio"` — yes/no questions or regular sentences
  - `"checkbox"` — multi-select questions with options
  - `"short"` — short phrases (typically < 5 meaningful words)

**Output**: A dictionary with keys like `extracted_terms`, `candidates`, `best_match_code`, `best_match_term`, and `confidence`.

### Option 2: Batch Mapping from Excel (`experiments/test.ipynb`)

Run the cells after the single-text demo in `experiments/test.ipynb` following this order: **read data → batch process → export results**.

**Input**: Excel file (e.g., `gc.xlsx`) with a column named `"Question"` containing the text to map.

**Output**: Processed Excel with three new columns:

- `agent_term` — extracted term
- `agent_code` — mapped HPO code
- `confidence` — confidence score (0–1)

**Configuration variables** (adjust as needed):

```python
INPUT_PATH = "gc.xlsx"
OUTPUT_PATH = "mapped_gc.xlsx"
QUESTION_COL = "Question"
DEFAULT_FIELD_TYPE = "radio"  # or 'checkbox' / 'short'
```

### Option 3: REST API Server

Start the FastAPI server:

```bash
source .venv/bin/activate
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**Endpoint**: `POST /map`

**Request body**:

```json
{
  "text": "Gum disease (loss of tissue around teeth)",
  "field_type": "short",
  "ontology": "HPO"
}
```

**Response**:

```json
{
  "input": { "text": "...", "field_type": "short", "ontology": "HPO" },
  "validated_mappings": [
    {
      "code": "HP:0000704",
      "term": "Periodontitis",
      "description": "...",
      "confidence": 0.95
    }
  ],
  "raw_state": { ... }
}
```

## 📁 Project Structure

```text
src/
  requirements.txt   # Core runtime deps
  handler.py         # AWS Lambda entry point
  graph/
    __init__.py
    agent_config.py  # LLM provider configuration (OpenAI/Bedrock)
    builder.py       # Main graph compilation
    nodes.py         # Extract / fetch / rank / validate / retry nodes
    types.py         # MappingState TypedDict
  prompts/
    *.md             # Prompt templates for each node
    template.py      # Prompt loading helper

Public usage:
  main.py                   # Local FastAPI server
  experiments/              # Notebooks for testing and batch processing
  requirements-server.txt   # FastAPI deps for local runs
  requirements-analysis.txt # Notebook/data analysis deps
  pyproject.toml            # uv project config

AWS deployment:
  template.yaml             # SAM CloudFormation template
  samconfig.toml.example    # SAM config template
```

## ⚗️ Agent Workflow

**Node Pipeline**:

1. `is_question_mappable` — Detects whether the input is a mappable medical question
2. `choose_extraction` — Routes to the proper extractor based on `field_type`
3. `extract_medical_terms_{radio|checkbox|short}` — Extracts relevant medical terms
4. `fetch_umls_terms` — Queries `ontology.jax.org` for candidate HPO terms
5. `rank_mappings` — Ranks candidates using LLM and assigns confidence scores
6. `validate_mapping` — Final validation and selection of best match
7. `retry_with_llm_rewrite` — (Optional) Rewrites query and retries if confidence < 0.9

**State Management**: All nodes operate on a shared `MappingState` dictionary defined in [`src/graph/types.py`](src/graph/types.py).

## 🚀 AWS Deployment

GenOMA can be deployed as a serverless API using AWS Lambda and API Gateway with AWS SAM (Serverless Application Model).

**Prerequisites**:

- AWS CLI configured with appropriate credentials
- AWS SAM CLI installed ([installation guide](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html))
- AWS Bedrock access enabled in your AWS account (for Claude 3.5 Sonnet model)

**LLM Provider**: When deployed to AWS, GenOMA automatically uses **AWS Bedrock** (Claude 3.5 Sonnet) instead of OpenAI. This is configured via the `LLM_PROVIDER=bedrock` environment variable in `template.yaml`.

**Setup**:

```bash
# Configure SAM deployment settings
cp samconfig.toml.example samconfig.toml
# Edit samconfig.toml with your AWS account/region settings

# Ensure Bedrock access is enabled in your AWS account
# Visit: https://console.aws.amazon.com/bedrock/
```

**Build and Deploy**:

```bash
# Build the Lambda package
sam build

# Deploy to AWS
sam deploy
```
