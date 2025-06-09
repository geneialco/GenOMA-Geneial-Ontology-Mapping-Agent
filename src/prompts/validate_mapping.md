You are an expert in evaluating medical term mappings.

TASK: Evaluate the following candidate HPO mappings generated for the survey question:
"{{ text }}"

Each candidate includes a predicted ontology term and a confidence score.

Candidate mappings:
{% for c in candidates %}
- {{ c.code }} ({{ c.term }}): Confidence = {{ (c.confidence * 100) | round }}%
{% endfor %}

Instructions:
- Analyze these candidates in the context of the original question.
- Choose the most appropriate match based on clinical relevance and semantic accuracy.
- If none are suitable, return an empty JSON object: {}

Return your answer **strictly** in this exact JSON format:

```json
{
  "best_match_code": "CODE",
  "best_match_term": "TERM",
  "confidence": "XX%"
}
