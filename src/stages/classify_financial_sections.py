import json
import yaml
import re
from pathlib import Path

def classify_financial_sections():
    with open('params.yaml', 'r') as f:
        params = yaml.safe_load(f)
    
    with open('data/intermediate/basic_content.json', 'r') as f:
        basic_content = json.load(f)
    
    sections = {
        'business_description': [],
        'risk_factors': [],
        'financial_statements': [],
        'notes_to_statements': [],
        'exhibits': [],
        'other': []
    }
    
    patterns = params['classification']['section_patterns']
    
    for block in basic_content['text']:
        content = block['content'].lower()
        classified = False
        
        for section_type, section_patterns in patterns.items():
            if any(pattern in content for pattern in section_patterns):
                sections[section_type].append(block)
                classified = True
                break
        
        if not classified:
            sections['other'].append(block)
    
    # Save results
    with open('data/intermediate/financial_sections.json', 'w') as f:
        json.dump(sections, f, indent=2)

if __name__ == "__main__":
    classify_financial_sections()