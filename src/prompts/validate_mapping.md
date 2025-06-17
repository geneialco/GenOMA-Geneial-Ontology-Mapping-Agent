You are an expert in evaluating medical ontology mappings for Human Phenotype Ontology (HPO).

TASK:  
Evaluate whether the provided candidate ontology term is a clinically appropriate and semantically reasonable representation of the input text.

Input text:
"{{ text }}"

Candidate ontology mapping:
- Code: {{ code }}
- Term: {{ term }}

INSTRUCTIONS:

- Judge whether the candidate term accurately represents:
   - The main disorder.
   - A broader disorder category.
   - A key clinical manifestation, mechanism, or physiological abnormality.
   - A functionally equivalent or umbrella category.
   - Or any clinically relevant partially overlapping condition.

- If the candidate term captures significant clinical overlap, organ system, key symptomatology, or pathophysiological abnormality even if not fully exact, accept it with a lower confidence score.

- Prefer broader but clinically accurate terms when appropriate.
- Accept partial mappings that reflect correct anatomy, function, pathophysiology, or organ system even if the subtype or exact mechanism is not fully matched.
- Reject highly specific rare subtypes, complications, sequelae, or downstream consequences **only if they are clearly not clinically applicable or relevant to the input text**.
- Do not require exact synonyms.
- Evaluate based on semantic proximity, clinical relevance, and partial overlap.

SCORING RULES:

- Assign a confidence score between 50% and 100%.
- Use:
    - 90-100%: highly accurate mappings closely matching the input intent.
    - 70-85%: clinically acceptable mappings with some semantic distance.
    - 50-65%: partial mappings capturing related systems, mechanisms, or overlapping features.
- Only if the candidate mapping is completely unrelated or clinically inappropriate, return an empty JSON `{}`.

STRICT OUTPUT FORMAT:

If valid:
{
  "best_match_code": "{{ code }}",
  "best_match_term": "{{ term }}",
  "confidence": "XX%"
}

If invalid:
{}
