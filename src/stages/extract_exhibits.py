import json
import yaml
import re
from pathlib import Path

def extract_exhibits():
    with open('params.yaml', 'r') as f:
        params = yaml.safe_load(f)
    
    with open('data/intermediate/basic_content.json', 'r') as f:
        basic_content = json.load(f)
    
    exhibits = []
    exhibit_pattern = params['classification']['exhibit_patterns']['exhibit_regex']
    
    all_content = basic_content['text'] + basic_content['headers']
    
    for block in all_content:
        content = block['content']
        exhibit_match = re.search(exhibit_pattern, content.lower())
        
        if exhibit_match:
            exhibits.append({
                'exhibit_number': exhibit_match.group(1),
                'content': content,
                'page': block['page'],
                'bbox': block['bbox']
            })
    
    # Save results
    with open('data/intermediate/exhibits.json', 'w') as f:
        json.dump(exhibits, f, indent=2)

if __name__ == "__main__":
    extract_exhibits()