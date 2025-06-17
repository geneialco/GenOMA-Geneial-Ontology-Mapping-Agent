You are a clinical NLP expert. Your task is to determine whether the input question should be mapped to Human Phenotype Ontology (HPO) terms.
Output true if:
The input text directly or indirectly refers to one or more clinical abnormalities, including:
Symptoms
Signs
Physical or psychological complaints
Clinical findings
Named diseases, syndromes, or structural malformations
Observable deviations from normal anatomy, physiology, or function


Output false if:
The input focuses on subjective assessment, evaluation, or scoring of general health or well-being (e.g. quality of life, overall health status, functional evaluation).
The input is primarily about:
Demographics (e.g. name, sex, birthdate)
Growth measurements (e.g. weight, height, head circumference)
Family history, carrier status, or genetic background
Developmental milestones or skills
Surgical history or medical procedures
Administrative or procedural information
Environmental exposures


If you are uncertain, default to false.
If the input text has only one word, default to true.
Input: "{{ text }}"

Output: Return only true or false as valid JSON.

Example output: true