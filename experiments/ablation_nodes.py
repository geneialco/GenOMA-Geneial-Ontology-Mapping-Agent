"""
Ablation-specific nodes and utilities for GenOMA experiments.
These functions are NOT used in the main workflow but are kept for ablation studies
that test different graph configurations.
"""

import json
import logging
import os
import re

import requests

from src.agents import AGENT_LLM_MAP
from src.graph.types import MappingState
from src.prompts.template import apply_prompt_template

# UMLS API Base URL for ontology queries
API_BASE_URL = os.getenv("UMLS_API_BASE_URL", "https://ontology.jax.org/api/hp")

logger = logging.getLogger(__name__)


# --- UMLS Tools (only used by gather_ancestor_candidates_node) ---
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


def _parse_confidence(value) -> float:
    """
    Parse confidence value from various formats (string percentage or float).

    Args:
        value: Confidence value as string (e.g., "85%") or float

    Returns:
        float: Normalized confidence value between 0.0 and 1.0
    """
    if isinstance(value, str):
        return float(value.replace("%", "").strip()) / 100.0
    return float(value)


# --- Ablation Node ---
def gather_ancestor_candidates_node(state: MappingState) -> MappingState:
    """
    Refine mappings using ancestor concepts from the ontology hierarchy.

    This node is triggered when the confidence of the best match is below threshold.
    It retrieves ancestor concepts from the ontology hierarchy and uses an LLM to
    select a more appropriate mapping from the broader context.

    Args:
        state (MappingState): Current workflow state with validated mappings

    Returns:
        MappingState: Updated state with refined mapping using ancestor concepts
    """
    logger.debug("Entered gather_ancestor_candidates_node")
    logger.debug(f"State snapshot: {json.dumps(state, indent=2, default=str)}")

    validated_list = state.get("validated_mappings", [])
    if not validated_list or not isinstance(validated_list, list):
        return {**state, "refine_mapping": {}}

    validated = validated_list[0]
    matched_code = validated.get("best_match_code", "")
    if not matched_code:
        return {**state, "refine_mapping": {}}

    # Step 1: Get CUI (Concept Unique Identifier) from ontology code
    cui = get_cui_from_ontology(matched_code)
    if not cui:
        return {**state, "refine_mapping": {}}
    logger.debug(f"CUI: {cui}")

    # Step 2: Get ancestor CUIs from the ontology hierarchy
    ancestors_data = get_ancestors(cui)
    logger.debug(f"Ancestors data: {ancestors_data}")
    ancestor_cuis = ancestors_data.get("ancestors", [])
    if not ancestor_cuis:
        return {**state, "refine_mapping": {}}
    logger.debug(f"Ancestor CUIs: {ancestor_cuis}")

    # Step 3: Get detailed information for each ancestor CUI
    candidate_details = []
    for ancestor_cui in ancestor_cuis:
        try:
            info = get_cui_info(ancestor_cui)
            if info.get("cui") and info.get("name"):
                candidate_details.append(info)
        except Exception as e:
            logger.error(f"Error retrieving CUI info for {ancestor_cui}: {e}")
            continue
    logger.debug(f"Candidate details: {candidate_details}")
    if not candidate_details:
        return {**state, "refine_mapping": {}}

    # Step 4: Build prompt context with ancestor candidates
    survey_text = state.get("text", "")
    candidate_list = "\n".join(
        [f"- {c['cui']} ({c['name']})" for c in candidate_details]
    )

    prompt_context = {
        "survey_text": survey_text,
        "validated_mappings": validated_list,
        "candidate_list": candidate_list,
    }

    prompt = apply_prompt_template("refine_mapping", prompt_context)
    logger.debug(f"Prompt: {prompt}")

    # Step 5: Call LLM to select best ancestor candidate
    try:
        response = AGENT_LLM_MAP["refine_mapping"].invoke(prompt)
        logger.debug(f"Response: {response}")
        raw_output = str(response.content).strip()
        cleaned = re.sub(
            r"```(?:json)?\s*(.*?)\s*```", r"\1", raw_output, flags=re.DOTALL
        ).strip()
        parsed = json.loads(cleaned)
    except Exception as e:
        logger.error(f"Error during LLM refinement: {e}")
        return {**state, "refine_mapping": {}}

    refined_code = parsed.get("refined_code", "").strip()
    refined_term = parsed.get("refined_term", "").strip()
    if not refined_code or not refined_term:
        return {**state, "refine_mapping": {}}

    try:
        refined_confidence = _parse_confidence(parsed.get("confidence", "0"))
    except Exception:
        refined_confidence = 0.0

    logger.info(f"LLM refined_term: {refined_term}")
    logger.info(f"LLM refined_code: {refined_code}")

    return {
        **state,
        "refine_mapping": {
            "refined_term": refined_term,
            "refined_code": refined_code,
            "confidence": refined_confidence,
        },
    }
