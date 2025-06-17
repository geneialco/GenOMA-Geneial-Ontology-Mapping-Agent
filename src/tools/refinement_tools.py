from src.tools.umls_tools import get_cui_from_ontology, get_ancestors, get_cui_info, get_depth, get_wu_palmer_similarity    
from src.prompts.template import apply_prompt_template
from typing import List, Dict

def generate_refinement_prompt(
    survey_text: str, 
    matched_code: str, 
    matched_term: str, 
    ontology: str = "HPO"
) -> str:
    cui = get_cui_from_ontology(ontology, matched_code)
    if not cui:
        return ""  

    ancestor_cuis = get_ancestors(cui)
    candidate_details: List[Dict[str, str]] = []

    for ancestor_cui in ancestor_cuis:
        info = get_cui_info(ancestor_cui)
        if info:
            candidate_details.append(info)

    if not candidate_details:
        return ""

    prompt = apply_prompt_template(
        "refine_mapping_with_ancestors",
        {
            "survey_text": survey_text,
            "original_mapping": {
                "matched_code": matched_code,
                "matched_term": matched_term
            },
            "candidate_details": candidate_details
        }
    )

    return prompt