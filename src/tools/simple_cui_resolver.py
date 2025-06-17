import re

def simple_cui_resolver(candidate_cuis, matched_term):
    def flatten(names):
        flat = []
        for name in names:
            if isinstance(name, list):
                flat.extend(name)
            else:
                flat.append(name)
        return flat

    def score_entry(names):
        score = 0
        # 完全 flatten names:
        names = flatten(names)

        for name in names:
            name_lower = name.lower()
            term_lower = matched_term.lower()

            if name_lower == term_lower:
                score += 100
            elif term_lower in name_lower:
                score += 50

            modifiers = ["nos", "unspecified", "disorder", "finding", "ischemic", "ischaemic", "nonspecific", "[d]"]
            for mod in modifiers:
                if mod in name_lower:
                    score -= 20

            if len(name.split()) <= 3:
                score += 10

        return score

    scored_candidates = []
    for candidate in candidate_cuis:
        cui = candidate["cui"]
        names = candidate["names"]
        score = score_entry(names)
        scored_candidates.append((score, cui))

    scored_candidates.sort(reverse=True)
    best_cui = scored_candidates[0][1]

    return best_cui