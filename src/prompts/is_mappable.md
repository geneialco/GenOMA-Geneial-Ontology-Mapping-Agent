You are a clinical NLP expert. Your task is to determine whether the input question should be mapped to Human Phenotype Ontology (HPO) terms.


Output false if the input is entirely unrelated to phenotypic abnormalities.
Specifically, exclude the following:
1. Demographics:
Name, sex, birthdate, race, ethnicity

2. Administrative or legal issues:
Insurance, consent, contact preferences, future survey participation

3. Genetic information:
Inheritance patterns or whether family members were tested (unless phenotypes are mentioned)
Only the gene name is described but no specific disease or symptom name is given. (e.g., POLR2-related disorder (not POLR2A) y/n Has your child received a diagnosis of a POLR2-related syndrome based on identification of a mutation in a POLR2 gene that is not POLR2A?)

4. Non-phenotypic responses:
Input text has, "- Unknown", "- Unsure", "- None", "- Don't know", "- Untested", "- Prefer not to answer". Like "Gtube removed reason Please select the reason/s your child had their G-tube removed. - Other",'Seizure worsen factors list Are there contributing factors that seem to induce or worsen your childs seizures? - None'. Although there is "No" in "Non-melanoma skin cancer", but it is meaningful, so exclude this. 

5. Skill achievement questions:
Questions asking what skills the child has already acquired (not what is lacking or delayed), or asking to select what extent a certain skill has been mastered. However, if age-related definitions appear in the text(e.g., Age 4 fine motor), this rule does not apply.


6. If the question is about how symptoms are reported or detected, and not the presence of the symptom itself, like "Headache indication How does your child indicate to you that they have a headache"


7. The input text is divided into different parts using the "-" symbol (note: hyphens in compound words like "self-injury", “Anti-reflux” are not considered separators). The last part is usually options, ff the option is deny or unsure, no mapping is required, like "- Other", "- Unknown", "- Unsure", "- None", "- Don't know", "- No", "-  Untested", "- Prefer not to answer", "- Too young to tell yet", like "Hyperelastic skin diagnosis (yes/no) - Have you been formally diagnosed with hyperelastic skin by a healthcare provider? - No",Although there is "No" in "Non-melanoma skin cancer", but it is meaningful, so exclude this. 


Output true if the input refers to any clinical abnormality, including:
1. Clinical presentation:Symptoms or signs, Physical or psychological complaints, Clinical findings

2. Diagnostic information: Diagnostic test results that may indicate a phenotype

3. Disease or condition: Diseases or syndromes, Structural malformations, Observable deviations from normal anatomy, physiology, or function


4. Functional and behavioral indicators:
Questions asking whether an individual has certain behaviors or abilities


5. Developmental concerns: Growth abnormalities

6. If the question is asking whether the individual has taken any auxiliary measures.

8. If the question is asking Has your child/ward had a history of any problems with their body system.

9. Although there is "No" in "Non-melanoma skin cancer", but it is meaningful, so output should be true. 



Defaults:
If uncertain, default to false.
If the input text is less than or equal to three words, default to true.
Input: "{{ text }}"
Output: Return only true or false as valid JSON.
Example output: true