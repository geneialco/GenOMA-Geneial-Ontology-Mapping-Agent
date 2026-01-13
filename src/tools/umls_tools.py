"""
UMLS API interaction utilities for the GenOMA Agent.
This module provides functions to interact with the UMLS (Unified Medical Language System) API
for ontology mapping and concept retrieval.
"""

import logging
import os

import requests

# Base URL for the UMLS API service
API_BASE_URL = os.getenv("UMLS_API_BASE_URL", "https://ontology.jax.org/api/hp")

logger = logging.getLogger(__name__)


def get_cui_info(cui):
    """Get details for a given CUI."""
    response = requests.get(f"{API_BASE_URL}/cuis/{cui}")
    return response.json()


def get_ancestors(cui):
    """Get ancestors of a CUI."""
    response = requests.get(f"{API_BASE_URL}/cuis/{cui}/ancestors")
    return response.json()


def get_cui_from_ontology(hpo_code):
    """Get CUI from a specific ontology term."""
    response = requests.get(f"{API_BASE_URL}/hpo_to_cui/{hpo_code}")
    return response.json()["cui"]
