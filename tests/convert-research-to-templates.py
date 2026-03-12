#!/usr/bin/env python3
"""
Convert research-findings.md into Python template dicts for generate-grammar-batches.py.
Parses the markdown structure and outputs a Python file with TEMPLATES list.
"""
import re
import sys
from pathlib import Path

def parse_findings(md_path):
    text = Path(md_path).read_text()

    templates = []
    current_category = None
    current_example = {}

    for line in text.split('\n'):
        # Category header: ## Category: email
        cat_match = re.match(r'^## Category:\s*(.+)', line)
        if cat_match:
            current_category = cat_match.group(1).strip()
            continue

        # Example header: ### Example N
        if re.match(r'^### Example \d+', line):
            # Save previous example
            if current_example.get('text'):
                templates.append(current_example)
            current_example = {'category': current_category}
            continue

        # Bad text
        bad_match = re.match(r'^\*\*Bad text:\*\*\s*"(.+)"$', line)
        if bad_match:
            current_example['text'] = bad_match.group(1)
            continue
        # Multi-line bad text (continues with ")
        if bad_match is None and 'text' not in current_example:
            bad_match = re.match(r'^\*\*Bad text:\*\*\s*"(.+)', line)
            if bad_match:
                current_example['text'] = bad_match.group(1)
                current_example['_collecting_text'] = True
                continue

        if current_example.get('_collecting_text'):
            if line.endswith('"'):
                current_example['text'] += '\n' + line[:-1]
                del current_example['_collecting_text']
            else:
                current_example['text'] += '\n' + line
            continue

        # Error types
        err_match = re.match(r'^\*\*Error types:\*\*\s*(.+)', line)
        if err_match:
            # Parse error types from the description
            errors_text = err_match.group(1)
            # Extract key error patterns
            error_types = []
            error_keywords = {
                'contraction': ['contraction', "don't", "can't", "won't", "isn't"],
                'informal_language': ['informal', 'FYI', 'ASAP', 'cliché', 'casual'],
                'missing_oxford_comma': ['Oxford comma', 'serial comma'],
                'legalese': ['legalese', 'pursuant to', 'herein', 'hereby', 'aforementioned', 'witnesseth'],
                'throat_clearing': ['throat-clearing', 'I am writing', 'please be advised'],
                'passive_voice': ['passive voice', 'was filed by', 'was granted by'],
                'nominalization': ['nominalization', 'made a determination', 'gave consideration'],
                'redundant_doublet': ['doublet', 'cease and desist', 'null and void', 'each and every'],
                'privilege_waiver': ['privilege', 'waiver', 'attorney-client'],
                'binding_language': ['binding', 'enforceable', 'UETA', 'E-SIGN'],
                'vague_timeline': ['vague', 'earliest convenience', 'ASAP', 'immediately'],
                'overconfident': ['clearly', 'obviously', 'overconfident'],
                'hedging': ['hedging', 'arguably', 'perhaps', 'it seems'],
                'subject_verb_agreement': ['subject-verb', 'agreement'],
                'dangling_modifier': ['dangling modifier', 'misplaced modifier', 'squinting'],
                'modal_verb_error': ['shall', 'may', 'must', 'modal'],
                'ambiguity': ['ambiguous', 'ambiguity', 'and/or'],
                'defined_term_issue': ['defined term', 'capitalization', 'undefined'],
                'citation_error': ['citation', 'Bluebook', 'supra', 'Id.'],
                'sentence_length': ['sentence length', 'long sentence', 'over 45 words'],
                'archaic_language': ['archaic', 'witnesseth', 'hereinafter', 'party of the first part'],
                'tone_adversarial': ['adversarial', 'personal attack', 'unprofessional'],
                'parallel_structure': ['parallel structure', 'parallel'],
                'spelling_error': ['spelling', 'misspelling'],
                'which_that': ['which/that', 'which', 'restrictive'],
                'govern_yourself': ['govern yourself'],
                'provided_however': ['provided, however'],
                'efforts_standard': ['efforts', 'best efforts', 'commercially reasonable'],
                'represents_warrants': ['represents and warrants'],
                'force_majeure': ['force majeure'],
                'double_negative': ['double negative', 'not uncommon'],
            }

            for err_type, keywords in error_keywords.items():
                if any(kw.lower() in errors_text.lower() for kw in keywords):
                    error_types.append(err_type)

            if not error_types:
                error_types = ['style_issue']

            current_example['error_types'] = error_types
            continue

        # Source
        src_match = re.match(r'^\*\*Source/inspiration:\*\*\s*(.+)', line)
        if src_match:
            current_example['source'] = src_match.group(1)
            continue

    # Don't forget last example
    if current_example.get('text'):
        templates.append(current_example)

    return templates


def main():
    md_path = Path(__file__).parent / 'research-findings.md'
    templates = parse_findings(md_path)

    # Output as Python
    out_path = Path(__file__).parent / 'research-templates.py'

    with open(out_path, 'w') as f:
        f.write("# Auto-generated from research-findings.md\n")
        f.write("# Do not edit — regenerate with convert-research-to-templates.py\n\n")
        f.write("RESEARCH_TEMPLATES = [\n")

        for t in templates:
            text = t.get('text', '').replace('\\n', '\n').replace('\\', '\\\\').replace('"""', '\\"\\"\\"')
            errors = t.get('error_types', ['style_issue'])
            category = t.get('category', 'general')

            f.write("    {\n")
            f.write(f'        "category": "{category}",\n')
            f.write(f'        "doc_subtype": "research_{category}",\n')
            f.write(f'        "text": """{text}""",\n')
            f.write(f'        "error_types": {errors},\n')
            f.write("    },\n")

        f.write("]\n")

    # Stats
    categories = {}
    for t in templates:
        cat = t.get('category', 'unknown')
        categories[cat] = categories.get(cat, 0) + 1

    print(f"Converted {len(templates)} examples:")
    for cat, count in sorted(categories.items()):
        print(f"  {cat}: {count}")
    print(f"\nOutput: {out_path}")


if __name__ == '__main__':
    main()
