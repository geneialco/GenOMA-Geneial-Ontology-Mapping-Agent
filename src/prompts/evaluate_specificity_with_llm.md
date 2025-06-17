You are an ontology mapping assistant.

Given the following medical concept mappings, determine the most accurate classification:

Ground Truth: "{{ true_label }}" (Code: {{ true_code }})
Predicted: "{{ predicted_label }}" (Code: {{ predicted_code }})

Categorize the match into one of the following:
- "exact match" if the concepts are fully equivalent.
- "too specific" if the predicted term is a more detailed version of the ground truth.
- "too general" if the predicted term is broader than the ground truth.
- "related but not a match" if the terms are medically related but not equivalent.
- "incorrect" if the predicted term does not match the ground truth at all.

Respond with only the category name.


