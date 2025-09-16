# main.py
"""
Main FastAPI application entry point for the UMLS Mapping LangGraph-based Agent.
This module provides a simple REST API interface for testing the medical term mapping functionality.
"""

from fastapi import FastAPI

# Initialize FastAPI application
app = FastAPI()

@app.get("/terms")
def get_terms(search: str, ontology: str = "HPO"):
    """
    Endpoint to search for medical terms in ontologies.
    
    Args:
        search (str): The medical term to search for
        ontology (str): The target ontology (default: "HPO" for Human Phenotype Ontology)
    
    Returns:
        dict: A dictionary containing search results with dummy data for testing
    """
    return {"results": [{"code": "HP:0000001", "term": search, "description": "Dummy description"}]}
