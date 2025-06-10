import json
import re
from src.config.agents import AGENT_LLM_MAP
from src.prompts.template import apply_prompt_template
import requests
from typing import Dict, Any
from src.graph.types import MappingState

def is_question_mappable_node(state: MappingState) -> MappingState:
    # This node is used to determine if the question is mappable to HPO, input is the question text, output is a boolean
    llm = AGENT_LLM_MAP["is_question_mappable_to_hpo"]
    prompt = apply_prompt_template("is_mappable", state) # apply the prompt template to the state

    response = llm.invoke(prompt)
    raw_content = response.content
    
    cleaned = re.sub(r"```(json)?\n?(.*?)\n?```", r"\2", raw_content, flags=re.DOTALL).strip()

    try:
        # Try direct boolean parsing
        is_mappable = json.loads(cleaned.lower())
        if not isinstance(is_mappable, bool):
            raise ValueError
    except Exception:
        # fallback: text-based heuristic
        is_mappable = "true" in cleaned.lower()

    return {
        **state,
        "is_mappable": is_mappable
    }



def extract_medical_terms_node(state: MappingState) -> MappingState:
    # This node is used to extract medical terms from the question text, input is the question text, output is a list of medical terms
    llm = AGENT_LLM_MAP["extract_medical_term_from_survey"]
    prompt = apply_prompt_template("extract_medical_term_from_survey", state)

    response = llm.invoke(prompt)
    raw_content = response.content

    cleaned = re.sub(r"json\n(.*?)\n", r"\1", raw_content, flags=re.DOTALL).strip()

    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError:
        parsed = []
    except Exception:
        parsed = []

    print("✅ Extracted terms:", parsed)
    return {
        **state,
        "extracted_terms": parsed
    }



API_BASE_URL = "http://52.43.228.165:8000/"  # UMLS API Base URL

def fetch_umls_terms_node(state: MappingState) -> MappingState:
    # This node is used to fetch UMLS terms from the API, input is the list of medical terms, output is a list of UMLS terms
    terms = state.get("extracted_terms", [])
    ontology = state.get("ontology", "HPO")

    all_results = []
    print("🔎 Searching for terms:", terms)

    for term in terms:
        url = f"{API_BASE_URL}/terms?search={term}&ontology={ontology}"
        try:
            response = requests.get(url)
            print(f"🌐 [{term}] API Status:", response.status_code)

            if response.status_code != 200:
                print(f"❌ Failed for term: {term}")
                all_results.append({
                    "original": term,
                    "candidates": []
                })
                continue

            results = response.json().get("results", [])
            print(f"✅ Results for {term}:", results)
            all_results.append({
                "original": term,
                "candidates": results
            })
        except Exception as e:
            print(f"❗ Exception for term '{term}':", str(e))
            all_results.append({
                "original": term,
                "candidates": []
            })

    print("🧪 Final UMLS mappings:", all_results)
    return {
        **state,
        "umls_mappings": all_results  
    }



def rank_mappings_node(state: MappingState) -> MappingState:
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




def validate_mapping_node(state: MappingState) -> MappingState:
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

        prompt_state = {
            "text": state.get("text", ""),
            "original": original_term,
            "candidates": candidates
        }

        prompt = apply_prompt_template("validate_mapping", prompt_state)
        response = llm.invoke(prompt)
        raw_output = response.content
        print(f"🧠 Raw LLM output for '{original_term}':", raw_output)

        try:
            # Step 1: Clean LLM output to strip away ```json blocks
            cleaned = raw_output.strip()
            if cleaned.startswith("```"):
                cleaned = re.sub(r"^```(?:json)?", "", cleaned, flags=re.IGNORECASE).strip()
                cleaned = re.sub(r"```$", "", cleaned).strip()

            # Step 2: Load JSON
            parsed = json.loads(cleaned)

            validated_results.append({
                "original": original_term,
                "best_match_code": parsed.get("best_match_code", "").strip().upper() or None,
                "best_match_term": parsed.get("best_match_term", "").strip() or None,
                "confidence": float(parsed.get("confidence", "0").replace("%", "").strip()) / 100 if parsed.get("confidence") else 0.0
            })

        except Exception as e:
            print(f"❌ Error validating '{original_term}':", e)
            validated_results.append({
                "original": original_term,
                "best_match_code": None,
                "best_match_term": None,
                "confidence": 0.0
            })

    result = {
        **state,
        "validated_mappings": validated_results
    }

    print("✅ Final validated mappings:", validated_results)
    return result