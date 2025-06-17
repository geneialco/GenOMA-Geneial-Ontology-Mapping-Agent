import json
import re
from src.config.agents import AGENT_LLM_MAP
from src.prompts.template import apply_prompt_template
import requests
from typing import Dict, Any
from src.graph.types import MappingState
from src.tools.simple_cui_resolver import simple_cui_resolver
from src.tools.flatten_names import flatten_names
from src.tools.umls_tools import search_cui, get_ancestors, get_cui_info, get_hpo_from_cui

def is_question_mappable_node(state: MappingState) -> MappingState:
    # This node determines if the question should be mapped to HPO
    llm = AGENT_LLM_MAP["is_question_mappable_to_hpo"]
    prompt = apply_prompt_template("is_mappable", state)
    response = llm.invoke(prompt)
    raw_content = response.content.strip()

    cleaned = re.sub(r"```(json)?\n?(.*?)\n?```", r"\2", raw_content, flags=re.DOTALL).strip()

    normalized = cleaned.lower().replace('"', '').replace("'", '').strip()
    try:
        parsed = json.loads(normalized)
        is_mappable = bool(parsed)
    except Exception:
        is_mappable = normalized == "true"

    return {
        **state,
        "is_mappable": is_mappable
    }
# state: text, is_mappable


def extract_medical_terms_node(state: MappingState) -> MappingState:
# This node is used to extract medical terms from the question text, input is the question text, output is a list of medical terms
# Use GPT-4o, if none list output, retry again, max_retries = 5. If have terms extracted, go to the next node.
    llm = AGENT_LLM_MAP["extract_medical_term_from_survey"]
    prompt = apply_prompt_template("extract_medical_term_from_survey", state)

    max_retries = 5
    retries = 0
    parsed = []

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
# state: text, is_mappable, extracted_terms


def normalize_extracted_terms_node(state: MappingState) -> MappingState:
# This node is used to normalize the extracted terms, input is the list of medical terms, output is a list of normalized medical terms
# If only one term was extracted, do not go through this node.
# This node only for two or more extracted terms
    llm = AGENT_LLM_MAP["normalize_extracted_terms"]
    prompt = apply_prompt_template("normalize_extracted_terms", state)
    response = llm.invoke(prompt)
    raw_content = response.content
    cleaned = re.sub(r"json\n(.*?)\n", r"\1", raw_content, flags=re.DOTALL).strip()
    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError:
        parsed = []
    except Exception:
        parsed = []
 
    original_terms = state.get("extracted_terms", [])
    if parsed and isinstance(parsed, list) and len(parsed) > 0:
        updated_terms = parsed
    else:
        updated_terms = original_terms

    print("✅ Extracted terms:", updated_terms)
    # Use new term exchange the old extracted_terms
    return {
        **state,
        "extracted_terms": updated_terms
    }
# state: text, is_mappable, extracted_terms


API_BASE_URL = "http://52.43.228.165:8000/"  # UMLS API Base URL

def fetch_umls_terms_node(state: MappingState) -> MappingState:
# This node is used to fetch UMLS terms from the API, input is the list of medical terms, output is a list of UMLS terms
    terms = state.get("extracted_terms", [])
    ontology = state.get("ontology", "HPO")

    all_results = []

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
# state: text, is_mappable, extracted_terms, umls_mappings


def retry_with_llm_rewrite_node(state: MappingState) -> MappingState:
# If the term was not mapped a HPO code, will enter this node, use GPT-4o retry find a samilar term.
# The new term will back fetch_umls_terms_node and try to mapping the HPO code
# Will try 10 times unless find a term which can mapping
    # Prepare the list of previously seen terms
    previous_terms = set(state.get("history_rewritten_terms", []))
    extracted_terms = state.get("extracted_terms", [])
    previous_terms.update(extracted_terms)

    # Inject previous_terms into the prompt context (you can modify your jinja template accordingly)
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

    # Record the failed revised_terms
    revised_terms = []
    for term in parsed:
        if term not in previous_terms:
            revised_terms.append(term)
    if not revised_terms:
        revised_terms = []
    # Update the failed revised_terms list
    updated_history = list(previous_terms.union(revised_terms))

    print("✅ Revised terms:", revised_terms)

    return {
        **state,
        "extracted_terms": revised_terms,
        "history_rewritten_terms": updated_history,
        "retry_count": state.get("retry_count", 0) + 1
    }
# state: text, is_mappable, extracted_terms, umls_mappings, history_rewritten_terms,retry_count


def rank_mappings_node(state: MappingState) -> MappingState:
# If a term mapping not only one candidate, this node will use LLM rank them and find the best conditate.
    print("🧩 Entered rank_mappings_node")
    umls_mappings = state.get("umls_mappings", [])
    llm = AGENT_LLM_MAP["rank_mappings"]
    ranked_mappings = []

    for entry in umls_mappings:
        original_term = entry.get("original", "")
        candidates = entry.get("candidates", [])
        if not candidates:
            ranked_mappings.append({
                "original": original_term,
                "ranked_candidates": []
            })
            continue
        # Prepare prompt for this term
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
        # Build lookup from LLM output
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
        # Sort by confidence
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
# state: text,is_mappable,extracted_terms,umls_mappings,history_rewritten_terms,retry_count,ranked_mappings



def validate_mapping_node(state: MappingState) -> MappingState:
# This node was used to validate the results and output the best_match_code and best_match_term
    print("🧩 Entered validate_mapping_node")

    ranked_mappings = state.get("ranked_mappings", [])
    if not ranked_mappings:
        print("⚠️ No ranked mappings to validate.")
        return {**state}

    llm = AGENT_LLM_MAP["validate_mapping"]
    validated_results = []

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
            if parsed:
                validated_results.append({
                    "original": original_term,
                    "best_match_code": parsed["best_match_code"],
                    "best_match_term": parsed["best_match_term"],
                    "confidence": float(parsed["confidence"].replace("%", "")) / 100.0
                })
            else:
                validated_results.append({
                    "original": original_term,
                    "best_match_code": None,
                    "best_match_term": None,
                    "confidence": 0.0
                })
        except:
            validated_results.append({
                "original": original_term,
                "best_match_code": None,
                "best_match_term": None,
                "confidence": 0.0
            })
    return {**state, "validated_mappings": validated_results}
# state: text,is_mappable,extracted_terms,umls_mappings,history_rewritten_terms,retry_count,ranked_mappings,validated_mappings



def gather_ancestor_candidates_node(state: MappingState) -> MappingState:
    print("🧩 Entered gather_ancestor_candidates_node")
    print("🔎 Current full state before gather_ancestor_candidates_node:")
    print(json.dumps(state, indent=2, default=str))

    matched_term = state.get("extracted_terms", [])[0]

    cui_results = search_cui(matched_term)
    if not cui_results or "cuis" not in cui_results or not cui_results["cuis"]:
        return {**state, "candidate_details": []}

    candidate_cuis_dict = {}
    for entry in cui_results["cuis"]:
        cui = entry["cui"]
        name = entry["name"]
        if isinstance(name, list):
            names_to_add = name
        else:
            names_to_add = [name]

        if cui not in candidate_cuis_dict:
            candidate_cuis_dict[cui] = set()

        for single_name in names_to_add:
            candidate_cuis_dict[cui].add(single_name)

    candidate_cuis = [{"cui": cui, "names": flatten_names(names)} for cui, names in candidate_cuis_dict.items()]

    selected_cui = simple_cui_resolver(candidate_cuis, matched_term)
    if not selected_cui:
        return {**state, "candidate_details": []}

    ancestors_data = get_ancestors(selected_cui)
    if not ancestors_data or "ancestors" not in ancestors_data:
        return {**state, "candidate_details": []}

    ancestor_cuis = ancestors_data["ancestors"]  

    candidate_details = []
    matched_term_lower = matched_term.lower()  

    for ancestor_cui in ancestor_cuis:
        try:
            info = get_cui_info(ancestor_cui)
            if info.get("cui") and info.get("name"):
                name_field = info["name"]
                if isinstance(name_field, list):
                    flat_names = flatten_names(name_field)
                else:
                    flat_names = [name_field]

                for single_name in flat_names:
                    if single_name.lower() == matched_term_lower:
                        continue  

                    candidate_details.append({
                        "cui": info["cui"],
                        "name": single_name
                    })
        except Exception as e:
            print(f"Error retrieving {ancestor_cui}: {e}")
            continue
    return {**state, "candidate_details": candidate_details}



def refine_mapping_llm_node(state: MappingState) -> MappingState:
    print("🧠 Entered refine_mapping_llm_node")
    print("🔎 candidate_details:", state.get("candidate_details", []))

    llm = AGENT_LLM_MAP["refine_mapping"]  
    prompt = apply_prompt_template("refine_mapping", state)
    response = llm.invoke(prompt)
    raw_content = response.content

    cleaned = re.sub(r"```(?:json)?\s*(.*?)\s*```", r"\1", raw_content, flags=re.DOTALL).strip()

    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError:
        parsed = {}

    refined_term = parsed.get("refined_term")
    refined_code = parsed.get("refined_code")
    print("🔎 refined_term:", refined_term)
    print("🔎 refined_code:", refined_code)

    if refined_term:
        updated_extracted_terms = [refined_term]  
    else:
        updated_extracted_terms = state.get("extracted_terms", [])

    print("✅ Updated extracted_terms:", updated_extracted_terms)

    return {
        **state,
        "extracted_terms": updated_extracted_terms
    }



def re_extract_medical_terms_node(state: MappingState) -> MappingState:
    # This node is used to re-extract and normalize medical terms using a more aggressive standardization prompt
    llm = AGENT_LLM_MAP["re_extract_medical_term"]
    prompt = apply_prompt_template("re_extract_medical_term", state)

    response = llm.invoke(prompt)
    raw_content = response.content

    cleaned = re.sub(r"json\n(.*?)\n", r"\1", raw_content, flags=re.DOTALL).strip()

    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError:
        parsed = []
    except Exception:
        parsed = []

    print("✅ Re-Extracted terms:", parsed)
    return {
        **state,
        "extracted_terms": parsed
    }
