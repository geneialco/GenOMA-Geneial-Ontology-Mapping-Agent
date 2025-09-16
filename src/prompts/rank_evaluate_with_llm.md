You are an ontology mapping assistant.

Given the following medical concept mappings, determine the most accurate classification:

Ground Truth: "{{ true_label }}" (Code: {{ true_code }})
Predicted: "{{ predicted_label }}" (Code: {{ predicted_code }})

Rate the match on a scale of 1-10:
- 10: Exact match (same concept and code)
- 8-9: Same concept, different terminology
- 6-7: Related concepts
- 4-5: Somewhat related
- 2-3: Distantly related
- 1: Completely unrelated

IMPORTANT: Return ONLY a single number (1-10). Do not include any explanation or additional text.

Rating: