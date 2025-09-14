import json
import re
from pathlib import Path

def create_document_outline():
    with open('data/intermediate/basic_content.json', 'r') as f:
        basic_content = json.load(f)
    
    outline = []
    headers = sorted(basic_content['headers'], key=lambda x: x['page'])
    
    for header in headers:
        content = header['content']
        section_match = re.search(r'(item\s+\d+[a-z]?|part\s+[IVX]+|exhibit\s+\d+)', content.lower())
        
        if section_match:
            outline.append({
                'section': section_match.group(1).upper(),
                'title': content.strip(),
                'page': header['page'],
                'bbox': header['bbox']
            })
    
    # Save results
    with open('data/intermediate/document_outline.json', 'w') as f:
        json.dump(outline, f, indent=2)

if __name__ == "__main__":
    create_document_outline()