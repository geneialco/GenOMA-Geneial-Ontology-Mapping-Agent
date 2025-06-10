You are an expert in evaluating medical term mappings.

TASK: Evaluate the following candidate HPO mappings generated for the survey question:
"{{ text }}"

Each candidate includes a predicted ontology term and a confidence score.

Candidate mappings:
{% for c in candidates %}
- {{ c.code }} ({{ c.term }}): Confidence = {{ (c.confidence * 100) | round }}%
{% endfor %}

Instructions:
- Analyze these candidates in the context of the original question and real-world clinical usage.
- Select the most appropriate match based on clinical relevance and semantic accuracy.
- Prefer broader, more accurate mappings over overly specific or ambiguous ones.
- If none are suitable, return an empty JSON object: {}

Return your answer **strictly** in this exact JSON format:

```json
{
  "best_match_code": "CODE",
  "best_match_term": "TERM",
  "confidence": "XX%"
}
