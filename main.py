# main.py
"""
Main FastAPI application entry point for the UMLS Mapping LangGraph-based Agent.

This module provides a REST API interface for testing the medical term mapping
functionality. For AWS Lambda deployment, see src/lambda_handler.py.

Usage (local development):
    uvicorn main:app --reload
"""

from typing import Any, Dict, List, Optional, cast

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from src.graph.builder import build_umls_mapper_graph
from src.graph.types import MappingState

# Initialize FastAPI application with metadata
app = FastAPI(
    title="GenOMA API",
    description="Geneial Ontology Mapping Agent - Maps clinical text to HPO terms",
    version="1.0.0",
)

# Allow local frontend during development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class MapRequest(BaseModel):
    text: str = Field(..., description="The survey question or free-text to map")
    field_type: str = Field(..., description='One of: "radio", "checkbox", "short"')
    ontology: Optional[str] = Field("HPO", description="Target ontology (default HPO)")


class MappingCandidate(BaseModel):
    code: str
    term: str
    description: Optional[str]
    confidence: Optional[float]


class MapResponse(BaseModel):
    input: Dict[str, Any]
    validated_mappings: List[MappingCandidate] = []
    raw_state: Dict[str, Any] = {}


@app.get("/health")
def health_check():
    """Health check endpoint for load balancers and monitoring."""
    return {"status": "healthy", "service": "genoma-api"}


@app.post("/map", response_model=MapResponse)
def map_text(req: MapRequest):
    """Invoke the UMLS/HPO mapping LangGraph workflow.

    The graph expects a MappingState-like dict. We provide the minimal required
    inputs: `text` and `field_type`. The compiled graph is invoked and the
    final state is returned (we surface `validated_mappings` when present).
    """
    try:
        graph = build_umls_mapper_graph()
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to build mapping graph: {e}"
        )

    initial_state = cast(
        MappingState,
        {
            "text": req.text,
            "field_type": req.field_type,
            "ontology": req.ontology,
        },
    )

    try:
        result_state = graph.invoke(initial_state)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Graph invocation failed: {e}")

    # Ensure we return JSON-serializable structures
    validated = (
        result_state.get("validated_mappings")
        if isinstance(result_state, dict)
        else None
    )
    if not validated:
        # Try other likely keys
        validated = (
            result_state.get("ranked_mappings")
            if isinstance(result_state, dict)
            else []
        )

    # Normalize candidate items
    normalized: List[MappingCandidate] = []
    if isinstance(validated, list):
        for item in validated:
            if not isinstance(item, dict):
                continue
            normalized.append(
                MappingCandidate(
                    code=item.get("code") or item.get("id") or "",
                    term=item.get("term") or item.get("label") or "",
                    description=item.get("description") or item.get("def") or None,
                    confidence=item.get("confidence"),
                )
            )

    return MapResponse(
        input=dict(initial_state),
        validated_mappings=normalized,
        raw_state=dict(result_state),
    )
