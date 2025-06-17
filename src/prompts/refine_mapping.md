TASK: Select the most appropriate UMLS ancestor term for the given survey question.

Survey question context:
"{{ survey_text }}"

Ancestor candidates:
{% for c in candidate_details %}
- {{ c.cui }} ({{ c.name }})
{% endfor %}

Instructions:
- Carefully review the survey question context.
- From the list of ancestor candidates, select the single most semantically appropriate and clinically accurate term.
- Select a more general ancestor if possible.
- IMPORTANT: You must ONLY select from the ancestor candidates listed above. Do not create any new term or reuse any other external knowledge.
- You MUST NOT output any term that is not listed in the ancestor candidates list.

Respond strictly in JSON format:
{
  "refined_code": "SELECTED_CUI",
  "refined_term": "SELECTED_TERM"
}

