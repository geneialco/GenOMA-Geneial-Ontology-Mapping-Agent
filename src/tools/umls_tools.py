"""
UMLS API interaction utilities for the UMLS Mapping LangGraph-based Agent.
This module provides functions to interact with the UMLS (Unified Medical Language System) API
for ontology mapping, concept retrieval, and semantic similarity calculations.
"""

import logging

import requests

# Base URL for the UMLS API service
API_BASE_URL = "http://localhost:8000"

logger = logging.getLogger(__name__)


def search_cui(term):
    """Search for CUIs using the API."""
    response = requests.get(f"{API_BASE_URL}/cuis", params={"query": term})
    result = response.json()
    logger.debug(f"CUI search results for '{term}': {result}")
    return result


def get_cui_info(cui):
    """Get details for a given CUI."""
    response = requests.get(f"{API_BASE_URL}/cuis/{cui}")
    return response.json()


def get_relations(cui):
    """Get hierarchical relations of a CUI."""
    response = requests.get(f"{API_BASE_URL}/cuis/{cui}/relations")
    return response.json()


def get_depth(cui):
    """Get depth of a CUI."""
    response = requests.get(f"{API_BASE_URL}/cuis/{cui}/depth")
    return response.json()["depth"]


def get_ancestors(cui):
    """Get ancestors of a CUI."""
    response = requests.get(f"{API_BASE_URL}/cuis/{cui}/ancestors")
    return response.json()


def get_cui_from_ontology(hpo_code):
    """Get CUI from a specific ontology term."""
    response = requests.get(f"{API_BASE_URL}/hpo_to_cui/{hpo_code}")
    return response.json()["cui"]


def get_lca(cui1, cui2):
    """Get lowest common ancestor of two CUIs."""
    response = requests.get(f"{API_BASE_URL}/cuis/{cui1}/{cui2}/lca")
    return response.json()["lca"]


def get_wu_palmer_similarity(cui1, cui2):
    """Get Wu-Palmer similarity between two CUIs."""
    response = requests.get(f"{API_BASE_URL}/cuis/{cui1}/{cui2}/similarity/wu-palmer")
    return response.json()["similarity"]


def get_hpo_from_cui(cui):
    """
    Given a CUI, query the UMLS API to get corresponding HPO code.
    """
    response = requests.get(f"{API_BASE_URL}/cuis/{cui}/hpo")
    return response.json()
