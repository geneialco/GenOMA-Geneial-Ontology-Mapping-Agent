"""
Node functions for the UMLS Mapping LangGraph-based Agent.
This module contains all the individual node functions that make up the workflow,
including medical term extraction, UMLS querying, ranking, validation, and refinement.
"""

import json
import re
from src.config.agents import AGENT_LLM_MAP
from src.prompts.template import apply_prompt_template
import requests
from typing import Dict, Any
from src.graph.types import MappingState
from src.tools.umls_tools import get_cui_from_ontology, get_ancestors, get_cui_info, get_hpo_from_cui

# UMLS API Base URL for ontology queries
API_BASE_URL = "http://localhost:8000/"

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
    print("✅ enter is_question_mappable_node ")
    
    # Get LLM agent and prompt for mappability assessment
    llm = AGENT_LLM_MAP["is_question_mappable_to_hpo"]
    prompt = apply_prompt_template("is_mappable", state)
    response = llm.invoke(prompt)
    raw_content = response.content.strip()

    # Clean and normalize the LLM response
    cleaned = re.sub(r"```(json)?\n?(.*?)\n?```", r"\2", raw_content, flags=re.DOTALL).strip()
    normalized = cleaned.lower().replace('"', '').replace("'", '').strip()

    # Parse the result to determine mappability
    try:
        parsed = json.loads(normalized)
        is_mappable = bool(parsed)
    except Exception:
        is_mappable = normalized == "true"

    # Retry if assessment is false and we haven't exceeded retry limit
    if not is_mappable and retry_count < 5:
        return is_question_mappable_node({
            **state,
            "mappability_retry_count": retry_count + 1
        })

    # Return final state with mappability result and retry count
    return {
        **state,
        "is_mappable": is_mappable,
        "mappability_retry_count": retry_count
    }

# state: text, is_mappable, mappability_retry_count


def extract_medical_terms_radio_node(state: MappingState) -> MappingState:
    """
    Extract medical terms from radio button survey questions.
    
    This node uses an LLM to identify and extract medical terms from survey
    questions that use radio button format (single selection).
    
    Args:
        state (MappingState): Current workflow state containing the survey question
    
    Returns:
        MappingState: Updated state with extracted medical terms
    """
    llm = AGENT_LLM_MAP["extract_medical_term_from_survey"]
    prompt = apply_prompt_template("extract_medical_term_radio_from_survey", state)

    max_retries = 50  # Maximum number of retry attempts
    retries = 0
    parsed = []

    # Retry loop to ensure we extract at least some terms
    while retries < max_retries:
        response = llm.invoke(prompt)
        raw_content = response.content
        cleaned = re.sub(r"json\n(.*?)\n", r"\1", raw_content, flags=re.DOTALL).strip()

        try:
            parsed = json.loads(cleaned)
        except json.JSONDecodeError:
            parsed = []
        except Exception:
            parsed = []

        if parsed:  # Successfully extracted terms
            break

        retries += 1
        print(f"⚠️ Retry {retries}: No terms extracted.")

    if not parsed:
        print("❌ Extraction failed after max retries. Proceeding with empty list.")

    print("✅ Extracted terms:", parsed)

    return {
        **state,
        "extracted_terms": parsed
    }
# state: text, is_mappable, mappability_retry_count, extracted_terms


def extract_medical_terms_checkbox_node(state: MappingState) -> MappingState:
    """
    Extract medical terms from checkbox survey questions.
    
    This node uses an LLM to identify and extract medical terms from survey
    questions that use checkbox format (multiple selection).
    
    Args:
        state (MappingState): Current workflow state containing the survey question
    
    Returns:
        MappingState: Updated state with extracted medical terms
    """
    llm = AGENT_LLM_MAP["extract_medical_term_from_survey"]
    prompt = apply_prompt_template("extract_medical_term_checkbox_from_survey", state)

    max_retries = 50  # Maximum number of retry attempts
    retries = 0
    parsed = []

    # Retry loop to ensure we extract at least some terms
    while retries < max_retries:
        response = llm.invoke(prompt)
        raw_content = response.content
        cleaned = re.sub(r"json\n(.*?)\n", r"\1", raw_content, flags=re.DOTALL).strip()

        try:
            parsed = json.loads(cleaned)
        except json.JSONDecodeError:
            parsed = []
        except Exception:
            parsed = []

        if parsed:  # Successfully extracted terms
            break

        retries += 1
        print(f"⚠️ Retry {retries}: No terms extracted.")

    if not parsed:
        print("❌ Extraction failed after max retries. Proceeding with empty list.")

    print("✅ Extracted terms:", parsed)

    return {
        **state,
        "extracted_terms": parsed
    }
# state: text, is_mappable, mappability_retry_count, extracted_terms

def extract_medical_terms_short_node(state: MappingState) -> MappingState:
    """
    Extract medical terms from short text survey questions.
    
    This node uses an LLM to identify and extract medical terms from survey
    questions that use short text input format.
    
    Args:
        state (MappingState): Current workflow state containing the survey question
    
    Returns:
        MappingState: Updated state with extracted medical terms
    """
    llm = AGENT_LLM_MAP["extract_medical_term_from_survey"]
    prompt = apply_prompt_template("extract_medical_term_short_from_survey", state)

    max_retries = 50  # Maximum number of retry attempts
    retries = 0
    parsed = []

    # Retry loop to ensure we extract at least some terms
    while retries < max_retries:
        response = llm.invoke(prompt)
        raw_content = response.content
        cleaned = re.sub(r"json\n(.*?)\n", r"\1", raw_content, flags=re.DOTALL).strip()

        try:
            parsed = json.loads(cleaned)
        except json.JSONDecodeError:
            parsed = []
        except Exception:
            parsed = []

        if parsed:  # Successfully extracted terms
            break

        retries += 1
        print(f"⚠️ Retry {retries}: No terms extracted.")

    if not parsed:
        print("❌ Extraction failed after max retries. Proceeding with empty list.")

    print("✅ Extracted terms:", parsed)

    return {
        **state,
        "extracted_terms": parsed
    }
# state: text, is_mappable, mappability_retry_count, extracted_terms

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
    terms = state.get("extracted_terms", [])
    ontology = state.get("ontology", "HPO")  # Default to Human Phenotype Ontology

    all_results = []

    # Query UMLS API for each extracted term
    for term in terms:
        url = f"{API_BASE_URL}/terms?search={term}&ontology={ontology}"

        try:
            response = requests.get(url, timeout=10)
            print(f"🌐 [{term}] API Status: {response.status_code}")

            if response.status_code != 200:
                print(f"❌ Failed for term: {term}")
                all_results.append({
                    "original": term,
                    "candidates": []
                })
                continue

            try:
                data = response.json()
                results = data.get("results", [])
                print(f"✅ Results for {term}: {results}")
            except Exception as e:
                print(f"❗ JSON parse error for term '{term}': {e}")
                results = []

            all_results.append({
                "original": term,
                "candidates": results
            })

        except Exception as e:
            print(f"❗ Request failed for term '{term}': {e}")
            all_results.append({
                "original": term,
                "candidates": []
            })

    print("🧪 Final UMLS mappings:", all_results)
    return {
        **state,
        "umls_mappings": all_results  
    }
# state: text, is_mappable, mappability_retry_count, extracted_terms, umls_mappings


def retry_with_llm_rewrite_node(state: MappingState) -> MappingState:
    """
    Retry term extraction with LLM rewrite when no UMLS candidates are found.
    
    This node is triggered when the initial term extraction fails to find any
    UMLS ontology candidates. It uses an LLM to generate alternative terms
    that might be more likely to match ontology entries.
    
    Args:
        state (MappingState): Current workflow state with failed mappings
    
    Returns:
        MappingState: Updated state with rewritten terms for retry
    """
    # Prepare the list of previously seen terms to avoid repetition
    previous_terms = set(state.get("history_rewritten_terms", []))
    extracted_terms = state.get("extracted_terms", [])
    previous_terms.update(extracted_terms)

    # Inject previous_terms into the prompt context for the LLM
    state_for_prompt = {
        **state,
        "previous_terms": list(previous_terms)
    }
    
    llm = AGENT_LLM_MAP["retry_with_llm_rewrite"]
    prompt = apply_prompt_template("retry_with_llm_rewrite", state_for_prompt)
    
    response = llm.invoke(prompt)
    raw_content = response.content
    
    cleaned = re.sub(r"```json\s*\n*(.*?)```", r"\1", raw_content, flags=re.DOTALL).strip()

    try:
        parsed = json.loads(cleaned)
    except (json.JSONDecodeError, Exception):
        parsed = []

    # Record the newly revised terms (excluding previously seen ones)
    revised_terms = []
    for term in parsed:
        if term not in previous_terms:
            revised_terms.append(term)
    if not revised_terms:
        revised_terms = []
    
    # Update the history of rewritten terms
    updated_history = list(previous_terms.union(revised_terms))

    print("✅ Revised terms:", revised_terms)

    return {
        **state,
        "extracted_terms": revised_terms,
        "history_rewritten_terms": updated_history,
        "retry_count": state.get("retry_count", 0) + 1
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
    print("🧩 Entered rank_mappings_node")
    umls_mappings = state.get("umls_mappings", [])
    llm = AGENT_LLM_MAP["rank_mappings"]
    ranked_mappings = []

    # Process each term's candidates
    for entry in umls_mappings:
        original_term = entry.get("original", "")
        candidates = entry.get("candidates", [])
        
        if not candidates:
            ranked_mappings.append({
                "original": original_term,
                "ranked_candidates": []
            })
            continue
            
        # Prepare prompt for this term's candidates
        prompt_state = {
            "original": original_term,
            "candidates": candidates
        }
        prompt = apply_prompt_template("rank_mappings", prompt_state)
        response = llm.invoke(prompt)
        raw_output = response.content.strip()
        print(f"🧠 Raw LLM output for '{original_term}':", raw_output)
        
        try:
            cleaned = re.sub(r"```json\n?(.*?)\n?```", r"\1", raw_output, flags=re.DOTALL).strip()
            output = json.loads(cleaned)
        except Exception as e:
            print(f"❌ JSON decode failed for '{original_term}':", e)
            output = []
            
        # Build confidence lookup from LLM output
        confidence_lookup = {
            item["matched_code"]: float(item["confidence"].replace("%", "").strip()) / 100
            for item in output
        }
        
        # Update candidate list with confidence scores
        updated_candidates = []
        for c in candidates:
            code = c["code"]
            updated_candidates.append({
                "code": code,
                "term": c["term"],
                "description": c.get("description", ""),
                "confidence": confidence_lookup.get(code, 0.0),
            })
            
        # Sort candidates by confidence (highest first)
        updated_candidates.sort(key=lambda x: x["confidence"], reverse=True)

        ranked_mappings.append({
            "original": original_term,
            "ranked_candidates": updated_candidates
        })
        
    result = {
        **state,
        "ranked_mappings": ranked_mappings
    }
    print("✅ Final ranked mappings:", result)
    return result
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
    print("🧩 Entered validate_mapping_node")

    ranked_mappings = state.get("ranked_mappings", [])
    if not ranked_mappings:
        print("⚠️ No ranked mappings to validate.")
        return {**state}

    llm = AGENT_LLM_MAP["validate_mapping"]
    validated_results = []

    # Validate each term's best candidate
    for item in ranked_mappings:
        original_term = item.get("original", "")
        candidates = item.get("ranked_candidates", [])

        if not candidates:
            validated_results.append({
                "original": original_term,
                "best_match_code": None,
                "best_match_term": None,
                "confidence": 0.0
            })
            continue

        # Use the top-ranked candidate for validation
        candidate = candidates[0]
        code = candidate.get("code")
        term = candidate.get("term")

        prompt_state = {
            "text": state.get("text", ""),
            "code": code,
            "term": term
        }

        prompt = apply_prompt_template("validate_mapping", prompt_state)
        response = llm.invoke(prompt)
        raw_output = response.content.strip()
        print(f"🧠 Raw LLM output for '{original_term}':", raw_output)

        try:
            parsed = json.loads(raw_output)
            # Fallback if parsed result is empty or malformed
            if not parsed or not parsed.get("best_match_code"):
                print("⚠️ Validation failed or empty — using top-ranked fallback.")
                fallback_candidate = candidates[0]
                validated_results.append({
                    "original": original_term,
                    "best_match_code": fallback_candidate["code"],
                    "best_match_term": fallback_candidate["term"],
                    "confidence": fallback_candidate.get("confidence", 1.0)
                })
            else:
                validated_results.append({
                    "original": original_term,
                    "best_match_code": parsed["best_match_code"],
                    "best_match_term": parsed["best_match_term"],
                    "confidence": float(parsed["confidence"].replace("%", "")) / 100.0
                    if isinstance(parsed["confidence"], str) else float(parsed["confidence"])
                })
        except Exception as e:
            print(f"⚠️ Exception parsing validation output: {e} — using fallback.")
            fallback_candidate = candidates[0]
            validated_results.append({
                "original": original_term,
                "best_match_code": fallback_candidate["code"],
                "best_match_term": fallback_candidate["term"],
                "confidence": fallback_candidate.get("confidence", 1.0)
            })

    return {**state, "validated_mappings": validated_results}

# state: text,is_mappable,mappability_retry_count,extracted_terms,umls_mappings,history_rewritten_terms,retry_count,ranked_mappings,validated_mappings


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
    print("🧩 Entered gather_ancestor_candidates_node")
    print("🔎 State snapshot:", json.dumps(state, indent=2, default=str))

    validated_list = state.get("validated_mappings", [])
    if not validated_list or not isinstance(validated_list, list):
        return {**state, "refine_mapping": {}}

    validated = validated_list[0]
    matched_code = validated.get("best_match_code", "")
    matched_term = validated.get("best_match_term", "")
    if not matched_code:
        return {**state, "refine_mapping": {}}

    # Step 1: Get CUI (Concept Unique Identifier) from ontology code
    cui = get_cui_from_ontology(matched_code)
    if not cui:
        return {**state, "refine_mapping": {}}
    print("🧩 CUI", cui)
    
    # Step 2: Get ancestor CUIs from the ontology hierarchy
    ancestors_data = get_ancestors(cui)
    print("🧩 CUI", ancestors_data)
    ancestor_cuis = ancestors_data.get("ancestors", [])
    if not ancestor_cuis:
        return {**state, "refine_mapping": {}}
    print("🧩 ancestor_cuis", ancestor_cuis)
    
    # Step 3: Get detailed information for each ancestor CUI
    candidate_details = []
    for ancestor_cui in ancestor_cuis:
        try:
            info = get_cui_info(ancestor_cui)
            if info.get("cui") and info.get("name"):
                candidate_details.append(info)
        except Exception as e:
            print(f"Error retrieving CUI info for {ancestor_cui}: {e}")
            continue
    print("🧩 candidate_details", candidate_details)
    if not candidate_details:
        return {**state, "refine_mapping": {}}

    # Step 4: Build prompt context with ancestor candidates
    survey_text = state.get("text", "")
    candidate_list = "\n".join([f"- {c['cui']} ({c['name']})" for c in candidate_details])

    prompt_context = {
        "survey_text": survey_text,
        "validated_mappings": validated_list,
        "candidate_list": candidate_list
    }

    prompt = apply_prompt_template("refine_mapping", prompt_context)
    print("🧩 prompt", prompt)
    
    # Step 5: Call LLM to select best ancestor candidate
    try:
        response = AGENT_LLM_MAP["refine_mapping"].invoke(prompt)
        print("🧩 response", response)
        raw_output = response.content.strip()
        cleaned = re.sub(r"```(?:json)?\s*(.*?)\s*```", r"\1", raw_output, flags=re.DOTALL).strip()
        parsed = json.loads(cleaned)
    except Exception as e:
        print(f"❌ ERROR during LLM refinement: {e}")
        return {**state, "refine_mapping": {}}

    refined_code = parsed.get("refined_code", "").strip()
    refined_term = parsed.get("refined_term", "").strip()
    if not refined_code or not refined_term:
        return {**state, "refine_mapping": {}}

    try:
        refined_confidence = float(parsed.get("confidence", "0").replace("%", "")) / 100
    except:
        refined_confidence = 0.0

    print("🧠 LLM refined_term:", refined_term)
    print("🧠 LLM refined_code:", refined_code)

    return {
        **state,
        "refine_mapping": {
            "refined_term": refined_term,
            "refined_code": refined_code,
            "confidence": refined_confidence
        }
    }


