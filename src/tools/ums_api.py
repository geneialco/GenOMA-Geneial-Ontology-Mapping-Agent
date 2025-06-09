from langchain_core.tools import tool
from typing import Annotated
import json

@tool
def umls_api_tool(term: Annotated[str, "Symptom to look up in UMLS."]) -> str:
    """
    Simulates querying UMLS/HPO/BioPortal API to return multiple ontology candidate matches.
    Returns a JSON string containing a list of dicts with 'term' and 'code'.
    """
    mock_mapping_dict = {
        "shortness of breath": [
            {"term": "Dyspnea", "code": "HP:0002094"},
            {"term": "Breathing difficulty", "code": "HP:0032447"},
            {"term": "Respiratory distress", "code": "HP:0002098"}
        ],
        "chest pain": [
            {"term": "Chest pain", "code": "HP:0100749"},
            {"term": "Chest discomfort", "code": "HP:0012735"},
            {"term": "Angina pectoris", "code": "HP:0001681"}
        ],
        "fever": [
            {"term": "Fever", "code": "HP:0001945"},
            {"term": "Recurrent fever", "code": "HP:0001954"},
            {"term": "Intermittent fever", "code": "HP:0001962"}
        ],
        "nausea": [
            {"term": "Nausea", "code": "HP:0002018"},
            {"term": "Vomiting", "code": "HP:0002013"},
            {"term": "Queasiness", "code": "HP:0031014"}
        ],
        "headache": [
            {"term": "Headache", "code": "HP:0002315"},
            {"term": "Migraine", "code": "HP:0002076"},
            {"term": "Occipital headache", "code": "HP:0002078"}
        ]
    }

    result = mock_mapping_dict.get(term.lower())
    if result:
        return json.dumps(result, indent=2)
    return json.dumps([])

if __name__ == "__main__":
    test_term = "shortness of breath"
    result = umls_api_tool.invoke(test_term)
    print("Test input:", test_term)
    print("Result:\n", result)

