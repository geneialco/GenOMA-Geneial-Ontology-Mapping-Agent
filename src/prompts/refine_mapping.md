TASK: Refine the HPO mapping by considering broader UMLS ancestor concepts.

Survey Question:
"{{ survey_text }}"

Validated Mapping:
{
  "original": "{{ validated_mappings[0]['original'] }}"
  "best_match_code": "{{ validated_mappings[0]['best_match_code'] }}",
  "best_match_term": "{{ validated_mappings[0]['best_match_term'] }}"
}

Ancestor terms for this mapping are:
{{ candidate_list }}

Instructions:
- Review the meaning of the survey question in context.
- Examine the validated mapping and each ancestor candidate.
- If "original" is "Persistent bleeding", "best_match_term" is "Persistent bleeding after trauma", it's good, do not use others, just return: {}.
- If any of the ancestor CUIs semantically matches the "original" term, choose it, like using "Thrombosis" is more appropriate than "Venous thrombosis"
- If any of the ancestor CUIs represents a **more general and appropriate** medical concept than the validated mapping, select it, like using "Cardiomyopathies", "Ataxia" “Tonic Seizures” is more appropriate than "Dilated cardiomyopathy", "Cerebellar ataxia", “Focal tonic seizures”.
- Then map the selected CUI to the most appropriate **HPO term**.
- If the question contains multiple terms separated by a forward slash ("/") or expressions like "and/or", extract a broader or unifying medical concept that encompasses all listed terms is good.  Example: “Muscle issues in the chest, back, and/or shoulders” → keep using “Abnormality of the musculature of the thorax” as the "best_match_term" is better than "Muscle weakness".
- If the validated mapping is already the most appropriate option, return an empty result.
- If the validated mapping includes qualifiers like "extreme", "severe", or specific etiology (e.g., genetic cause), and the survey question does **not** include those qualifiers or implications, prefer a broader ancestor term, like using "Short stature" may be more appropriate than "Short stature, extreme".


Return your answer strictly in this JSON format:
{
  "refined_code": "NEW_HPO_CODE",
  "refined_term": "NEW_HPO_TERM",
  "confidence": "XX%"
}

If no refinement is needed, return:
{}

