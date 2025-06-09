import json
import re
from src.config.agents import AGENT_LLM_MAP
from src.prompts.template import apply_prompt_template
import requests
from typing import Dict, Any
from src.graph.types import MappingState

def is_question_mappable_node(state: MappingState) -> MappingState:
    llm = AGENT_LLM_MAP["is_question_mappable_to_hpo"]
    prompt = apply_prompt_template("is_mappable", state)

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
    print("📝 Input text:", state.get("text"))
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
                continue

            results = response.json().get("results", [])
            print(f"✅ Results for {term}:", results)
            all_results.append({
                "original": term,
                "candidates": results
            })
        except Exception as e:
            print(f"❗ Exception for term '{term}':", str(e))

    if all_results:
        flattened = {
            "original": all_results[0]["original"],
            "candidates": all_results[0]["candidates"]
        }
    else:
        flattened = {
            "original": "",
            "candidates": []
        }
    print("🧪 Final flattened state:", {**state, **flattened})
    return {
        **state,
        **flattened  
    }




def rank_mappings_node(state: MappingState) -> MappingState:
    print("🧩 Entered rank_mappings_node")
    print("✅ state", state)
    candidate_terms = state.get("candidates", [])

    if not candidate_terms:
        return {**state}

    llm = AGENT_LLM_MAP["rank_mappings"]
    prompt = apply_prompt_template("rank_mappings", state)

    response = llm.invoke(prompt)
    raw_output = response.content.strip()
    print("🧠 Raw LLM output:", raw_output)

    cleaned = re.sub(r"```json\n?(.*?)\n?```", r"\1", raw_output, flags=re.DOTALL).strip()

    try:
        output = json.loads(cleaned)
    except Exception as e:
        print("❌ JSON decode failed:", e)
        return {**state}

    confidence_lookup = {
        item["matched_code"]: float(item["confidence"].replace("%", "").strip()) / 100
        for item in output
    }

    updated_candidates = []
    for c in candidate_terms:
        code = c["code"]
        confidence = confidence_lookup.get(code, 0.0)
        updated = {
            "code": code,
            "term": c["term"],
            "description": c.get("description", ""),
            "confidence": confidence,
        }
        updated_candidates.append(updated)

    updated_candidates.sort(key=lambda x: x["confidence"], reverse=True)

    result = {
        **state, 
        "candidates": updated_candidates,
    }

    print("✅ Final updated state:", result)
    return result





def validate_mapping_node(state: MappingState) -> MappingState:
    print("🧩 Entered validate_mapping_node")
    print("📝 Input question:", state.get("text"))
    print("📌 Candidates:", state.get("candidates"))

    llm = AGENT_LLM_MAP["validate_mapping"]
    prompt = apply_prompt_template("validate_mapping", state)

    response = llm.invoke(prompt)
    raw_content = response.content
    print("🧠 Raw LLM output:", raw_content)

    # 更鲁棒的清理正则
    cleaned = re.sub(r"```(?:json)?\s*([\s\S]*?)\s*```", r"\1", raw_content, flags=re.IGNORECASE).strip()

    try:
        output = json.loads(cleaned)
        best_code = output.get("best_match_code", "").strip().upper()
        best_term = output.get("best_match_term", "").strip()
        confidence = float(output.get("confidence", "0").replace("%", "").strip()) / 100 if output.get("confidence") else 0.0

        result = {
            "best_match_code": best_code or None,
            "best_match_term": best_term or None,
            "confidence": confidence
        }

    except Exception as e:
        print("❌ Error parsing LLM response:", e)
        result = {
            "best_match_code": None,
            "best_match_term": None,
            "confidence": 0.0
        }

    print("✅ Validated result:", result)

    return {
        **state,
        **result
    }
