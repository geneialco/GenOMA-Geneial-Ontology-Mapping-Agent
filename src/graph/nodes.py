"""
Node functions for the UMLS Mapping LangGraph-based Agent.
This module contains all the individual node functions that make up the workflow,
including medical term extraction, UMLS querying, ranking, validation, and refinement.
"""

import json
import logging
import os
import re
from typing import List

import requests

from src.graph.agent_config import AGENT_LLM_MAP
from src.graph.types import MappingState
from src.prompts.template import apply_prompt_template

# UMLS API Base URL for ontology queries
API_BASE_URL = (
    os.getenv("UMLS_API_BASE_URL", "https://ontology.jax.org/api/hp") + "/search"
)

logger = logging.getLogger(__name__)


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


def _extract_medical_terms(state: MappingState, prompt_name: str) -> MappingState:
    """
    Generic medical term extraction logic for all survey field types.

    Args:
        state: Current workflow state
        prompt_name: Name of the prompt template to use

    Returns:
        MappingState: Updated state with extracted medical terms
    """
    llm = AGENT_LLM_MAP["extract_medical_term_from_survey"]
    prompt = apply_prompt_template(prompt_name, state)

    max_retries = 3
    retries = 0
    parsed: List[str] = []

    while retries < max_retries:
        response = llm.invoke(prompt)
        raw_content = str(response.content)
        cleaned = re.sub(r"json\n(.*?)\n", r"\1", raw_content, flags=re.DOTALL).strip()

        try:
            parsed = json.loads(cleaned)
        except (json.JSONDecodeError, Exception):
            parsed = []

        if parsed:
            break

        retries += 1
        logger.warning(
            f"Extraction retry {retries}/{max_retries} - prompt: {prompt_name}"
        )

    if not parsed:
        logger.error(
            f"Extraction failed after {max_retries} retries - prompt: {prompt_name}"
        )

    logger.info(f"Extracted {len(parsed)} terms: {parsed}")

    return {**state, "extracted_terms": parsed}


def is_question_mappable_node(state: MappingState) -> MappingState:
    """
    Determine if a survey question can be mapped to medical ontologies.

    This node uses an LLM to assess whether the input question contains
    medical concepts that can be mapped to standardized ontologies like HPO.

    Args:
        state (MappingState): Current workflow state containing the survey question

    Returns:
        MappingState: Updated state with mappability assessment
    """
    # Use a separate retry counter to avoid conflicts with other retry mechanisms
    retry_count = state.get("mappability_retry_count", 0)
    logger.debug("Entered is_question_mappable_node")

    # Get LLM agent and prompt for mappability assessment
    llm = AGENT_LLM_MAP["is_question_mappable_to_hpo"]
    prompt = apply_prompt_template("is_mappable", state)
    response = llm.invoke(prompt)
    raw_content = str(response.content).strip()

    # Clean and normalize the LLM response
    cleaned = re.sub(
        r"```(json)?\n?(.*?)\n?```", r"\2", raw_content, flags=re.DOTALL
    ).strip()
    normalized = cleaned.lower().replace('"', "").replace("'", "").strip()

    # Parse the result to determine mappability
    try:
        parsed = json.loads(normalized)
        is_mappable = bool(parsed)
    except Exception:
        is_mappable = normalized == "true"

    # Retry if assessment is false and we haven't exceeded retry limit
    if not is_mappable and retry_count < 5:
        return is_question_mappable_node(
            {**state, "mappability_retry_count": retry_count + 1}
        )

    # Return final state with mappability result and retry count
    return {**state, "is_mappable": is_mappable, "mappability_retry_count": retry_count}


# state: text, is_mappable, mappability_retry_count
def extract_medical_terms_radio_node(state: MappingState) -> MappingState:
    """Extract medical terms from radio button survey questions."""
    return _extract_medical_terms(state, "extract_medical_term_radio_from_survey")


def extract_medical_terms_checkbox_node(state: MappingState) -> MappingState:
    """Extract medical terms from checkbox survey questions."""
    return _extract_medical_terms(state, "extract_medical_term_checkbox_from_survey")


def extract_medical_terms_short_node(state: MappingState) -> MappingState:
    """Extract medical terms from short text survey questions."""
    return _extract_medical_terms(state, "extract_medical_term_short_from_survey")


def fetch_umls_terms_node(state: MappingState) -> MappingState:
    """
    Fetch UMLS ontology terms for extracted medical terms.

    This node queries the UMLS API to find candidate ontology terms that match
    the extracted medical terms from the survey question.

    Args:
        state (MappingState): Current workflow state containing extracted terms

    Returns:
        MappingState: Updated state with UMLS mapping candidates
    """
    raw = state.get("extracted_terms", "")
    
    # Normalize to a list of terms
    if isinstance(raw, list):
        terms = [str(t).strip() for t in raw if t and str(t).strip()]
    else:
        terms = [str(raw).strip()] if raw and str(raw).strip() else []

    all_results = []
    
    if not terms:
        logger.warning("No terms provided for UMLS fetch")
        return {**state, "umls_mappings": []}

    # Process each extracted term
    for term in terms:
        if not term:
            continue

        params = {"q": term, "page": 0, "limit": 5}

        try:
            resp = requests.get(API_BASE_URL, params=params, timeout=10)
            logger.info(f"UMLS API query - term: {term}, status: {resp.status_code}")

            if resp.status_code != 200:
                logger.error(
                    f"UMLS API error - term: {term}, status: {resp.status_code}, "
                    f"response: {resp.text[:200]}"
                )
                all_results.append({"original": term, "candidates": []})
            else:
                try:
                    data = resp.json()
                    results = data.get("terms", [])
                except Exception as e:
                    logger.error(
                        f"UMLS API JSON parse error - term: {term}, error: {e}, "
                        f"response_preview: {resp.text[:200]}"
                    )
                    results = []

                candidates = [
                    {
                        "code": r.get("id"),
                        "term": r.get("name"),
                        "description": r.get("definition"),
                        "synonyms": r.get("synonyms", []),
                        "xrefs": r.get("xrefs", []),
                    }
                    for r in results
                ]

                logger.info(
                    f"UMLS candidates found - term: {term}, count: {len(candidates)}, "
                    f"top_2: {[c.get('code') for c in candidates[:2]]}"
                )
                all_results.append({"original": term, "candidates": candidates})

        except requests.exceptions.Timeout:
            logger.error(f"UMLS API timeout - term: {term}, timeout: 10s")
            all_results.append({"original": term, "candidates": []})
        except requests.exceptions.RequestException as e:
            logger.error(
                f"UMLS API request failed - term: {term}, error: {type(e).__name__}: {e}"
            )
            all_results.append({"original": term, "candidates": []})
        except Exception as e:
            logger.error(f"Unexpected error fetching UMLS terms - term: {term}, error: {e}")
            all_results.append({"original": term, "candidates": []})

    logger.debug(f"Final HPO mappings for {len(all_results)} terms: {all_results}")
    return {**state, "umls_mappings": all_results}


# state: text, is_mappable, mappability_retry_count, extracted_terms, umls_mappings
def retry_with_llm_rewrite_node(state: MappingState) -> MappingState:
    """
    Retry term extraction with LLM rewrite for low-confidence mappings.

    This node is triggered when some mappings have low confidence (< 0.9).
    It preserves high-confidence mappings and only rewrites terms that need
    improvement.

    Args:
        state (MappingState): Current workflow state with validated mappings

    Returns:
        MappingState: Updated state with rewritten terms for low-confidence mappings
    """
    validated_mappings = state.get("validated_mappings", [])
    confidence_threshold = 0.9
    
    # Separate high-confidence and low-confidence mappings
    high_confidence_mappings = []
    low_confidence_terms = []
    
    for mapping in validated_mappings:
        confidence = mapping.get("confidence", 0.0)
        original_term = mapping.get("original", "")
        
        if confidence >= confidence_threshold:
            # Preserve this mapping
            high_confidence_mappings.append(mapping)
            logger.info(
                f"Preserving high-confidence mapping - term: {original_term}, "
                f"code: {mapping.get('best_match_code')}, confidence: {confidence:.2f}"
            )
        else:
            # This term needs rewriting
            low_confidence_terms.append(original_term)
            logger.info(
                f"Flagged for retry - term: {original_term}, confidence: {confidence:.2f}"
            )
    
    if not low_confidence_terms:
        logger.warning("Retry triggered but no low-confidence terms found")
        return {**state, "preserved_mappings": high_confidence_mappings}
    
    # Prepare the list of previously seen terms to avoid repetition
    previous_terms = set(state.get("history_rewritten_terms", []))
    previous_terms.update(low_confidence_terms)
    
    # Rewrite only the low-confidence terms
    revised_terms = []
    for term in low_confidence_terms:
        state_for_prompt = {
            **state,
            "text": term,
            "previous_terms": list(previous_terms)
        }
        
        llm = AGENT_LLM_MAP["retry_with_llm_rewrite"]
        prompt = apply_prompt_template("retry_with_llm_rewrite", state_for_prompt)
        
        response = llm.invoke(prompt)
        raw_content = str(response.content)
        
        cleaned = re.sub(
            r"```json\s*\n*(.*?)```", r"\1", raw_content, flags=re.DOTALL
        ).strip()
        
        try:
            parsed = json.loads(cleaned)
            # Extract the rewritten term (should be a single term)
            if isinstance(parsed, list) and parsed:
                rewritten_term = parsed[0]
            elif isinstance(parsed, str):
                rewritten_term = parsed
            else:
                rewritten_term = None
                
            if rewritten_term and rewritten_term not in previous_terms:
                revised_terms.append(rewritten_term)
                previous_terms.add(rewritten_term)
                logger.info(f"Rewrote '{term}' → '{rewritten_term}'")
            else:
                logger.warning(f"Failed to rewrite term: {term}, using original")
                revised_terms.append(term)
        except (json.JSONDecodeError, Exception) as e:
            logger.error(f"Error parsing rewritten term for '{term}': {e}")
            revised_terms.append(term)
    
    # Update the history of rewritten terms
    updated_history = list(previous_terms)
    
    logger.info(
        f"Retry summary - preserved: {len(high_confidence_mappings)}, "
        f"rewriting: {len(revised_terms)}"
    )

    return {
        **state,
        "extracted_terms": revised_terms,
        "history_rewritten_terms": updated_history,
        "retry_count": state.get("retry_count", 0) + 1,
        "preserved_mappings": high_confidence_mappings,
        "ranked_mappings": [],
        "validated_mappings": [],
        "umls_mappings": [],
    }


# state: text, is_mappable, mappability_retry_count, extracted_terms, umls_mappings, history_rewritten_terms,retry_count
def rank_mappings_node(state: MappingState) -> MappingState:
    """
    Rank UMLS mapping candidates by confidence using LLM evaluation.

    This node takes multiple candidate ontology terms for each extracted medical
    term and uses an LLM to rank them by confidence and relevance to the original
    survey question context.

    Args:
        state (MappingState): Current workflow state with UMLS mapping candidates

    Returns:
        MappingState: Updated state with ranked mappings by confidence
    """
    logger.debug("Entered rank_mappings_node")
    umls_mappings = state.get("umls_mappings", [])
    llm = AGENT_LLM_MAP["rank_mappings"]
    ranked_mappings = []

    # Process each term's candidates
    for entry in umls_mappings:
        original_term = entry.get("original", "")
        candidates = entry.get("candidates", [])

        if not candidates:
            ranked_mappings.append({"original": original_term, "ranked_candidates": []})
            continue

        # Prepare prompt for this term's candidates
        prompt_state = {"original": original_term, "candidates": candidates}
        prompt = apply_prompt_template("rank_mappings", prompt_state)
        response = llm.invoke(prompt)
        raw_output = str(response.content).strip()
        logger.debug(f"Raw LLM output for '{original_term}': {raw_output[:100]}...")

        try:
            cleaned = re.sub(
                r"```json\n?(.*?)\n?```", r"\1", raw_output, flags=re.DOTALL
            ).strip()
            output = json.loads(cleaned)
        except json.JSONDecodeError as e:
            logger.error(
                f"Ranking JSON decode failed - term: {original_term}, "
                f"error: {e}, output_preview: {raw_output[:200]}"
            )
            output = []
        except Exception as e:
            logger.error(f"Ranking parse error - term: {original_term}, error: {e}")
            output = []

        # Build confidence lookup from LLM output
        confidence_lookup = {
            item["matched_code"]: float(item["confidence"].replace("%", "").strip())
            / 100
            for item in output
        }

        # Update candidate list with confidence scores
        updated_candidates = []
        for c in candidates:
            code = c["code"]
            updated_candidates.append(
                {
                    "code": code,
                    "term": c["term"],
                    "description": c.get("description", ""),
                    "confidence": confidence_lookup.get(code, 0.0),
                }
            )

        # Sort candidates by confidence (highest first)
        updated_candidates.sort(key=lambda x: x["confidence"], reverse=True)

        ranked_mappings.append(
            {"original": original_term, "ranked_candidates": updated_candidates}
        )

    logger.info(f"Final ranked mappings count: {len(ranked_mappings)}")
    return {**state, "ranked_mappings": ranked_mappings}


# state: text,is_mappable,mappability_retry_count,extracted_terms,umls_mappings,history_rewritten_terms,retry_count,ranked_mappings
def validate_mapping_node(state: MappingState) -> MappingState:
    """
    Validate and select the best mapping for each medical term.

    This node takes the ranked candidates and uses an LLM to validate the best match
    in the context of the original survey question, providing final confidence scores
    and selecting the most appropriate ontology mapping.

    Args:
        state (MappingState): Current workflow state with ranked mappings

    Returns:
        MappingState: Updated state with validated final mappings
    """
    logger.debug("Entered validate_mapping_node")

    ranked_mappings = state.get("ranked_mappings", [])
    if not ranked_mappings:
        logger.warning("No ranked mappings to validate")
        return {**state}

    llm = AGENT_LLM_MAP["validate_mapping"]
    validated_results = []

    # Validate each term's best candidate
    for item in ranked_mappings:
        original_term = item.get("original", "")
        candidates = item.get("ranked_candidates", [])

        if not candidates:
            validated_results.append(
                {
                    "original": original_term,
                    "best_match_code": None,
                    "best_match_term": None,
                    "confidence": 0.0,
                }
            )
            continue

        # Use the top-ranked candidate for validation
        candidate = candidates[0]
        code = candidate.get("code")
        term = candidate.get("term")

        prompt_state = {"text": state.get("text", ""), "code": code, "term": term}

        prompt = apply_prompt_template("validate_mapping", prompt_state)
        response = llm.invoke(prompt)
        raw_output = str(response.content).strip()
        logger.debug(f"Raw LLM output for '{original_term}': {raw_output[:100]}...")
        cleaned_output = re.sub(
            r"```json\n?(.*?)\n?```", r"\1", raw_output, flags=re.DOTALL
        ).strip()

        try:
            parsed = json.loads(cleaned_output)
            # Fallback if parsed result is empty or malformed
            if not parsed or not parsed.get("best_match_code"):
                logger.warning(
                    f"Validation result empty/malformed - term: {original_term}, "
                    f"using top-ranked fallback (code: {candidates[0].get('code')})"
                )
                fallback_candidate = candidates[0]
                validated_results.append(
                    {
                        "original": original_term,
                        "best_match_code": fallback_candidate["code"],
                        "best_match_term": fallback_candidate["term"],
                        "confidence": fallback_candidate.get("confidence", 1.0),
                    }
                )
            else:
                confidence = _parse_confidence(parsed["confidence"])
                logger.debug(
                    f"Validation successful - term: {original_term}, "
                    f"code: {parsed['best_match_code']}, confidence: {confidence:.2f}"
                )
                validated_results.append(
                    {
                        "original": original_term,
                        "best_match_code": parsed["best_match_code"],
                        "best_match_term": parsed["best_match_term"],
                        "confidence": confidence,
                    }
                )
        except json.JSONDecodeError as e:
            logger.warning(
                f"Validation JSON decode error - term: {original_term}, "
                f"error: {e}, output_preview: {cleaned_output[:200]}, using fallback"
            )
            fallback_candidate = candidates[0]
            validated_results.append(
                {
                    "original": original_term,
                    "best_match_code": fallback_candidate["code"],
                    "best_match_term": fallback_candidate["term"],
                    "confidence": fallback_candidate.get("confidence", 1.0),
                }
            )
        except Exception as e:
            logger.warning(
                f"Validation parse error - term: {original_term}, "
                f"error: {type(e).__name__}: {e}, using fallback"
            )
            fallback_candidate = candidates[0]
            validated_results.append(
                {
                    "original": original_term,
                    "best_match_code": fallback_candidate["code"],
                    "best_match_term": fallback_candidate["term"],
                    "confidence": fallback_candidate.get("confidence", 1.0),
                }
            )

    # Merge with preserved mappings from retry (if any)
    preserved_mappings = state.get("preserved_mappings", [])
    if preserved_mappings:
        logger.info(
            f"Merging {len(preserved_mappings)} preserved mappings with "
            f"{len(validated_results)} new mappings"
        )
        all_validated = preserved_mappings + validated_results
    else:
        all_validated = validated_results

    return {**state, "validated_mappings": all_validated, "preserved_mappings": []}


# state: text,is_mappable,mappability_retry_count,extracted_terms,umls_mappings,history_rewritten_terms,retry_count,ranked_mappings,validated_mappings
