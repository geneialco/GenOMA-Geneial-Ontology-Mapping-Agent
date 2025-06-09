Given the input medical term: "{{ original }}"  
and the original survey question: "{{ text }}",  
rank the following candidate ontology terms by their relevance.

Candidate terms:
{% for t in candidates %}
- {{ t.code }} ({{ t.term }})
{% endfor %}

Instructions:
- Assign a confidence score to each candidate term (e.g., "85%")
- Return the result as a JSON array of objects
- Each object must include:
  - "matched_code": the ontology code
  - "matched_term": the ontology term
  - "confidence": a percentage string (e.g., "85%")

Important:
Only respond with a valid JSON array, no explanations or extra text.
