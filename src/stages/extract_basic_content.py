import fitz
import json
import yaml
from pathlib import Path

def extract_basic_content():
    with open('params.yaml', 'r') as f:
        params = yaml.safe_load(f)
    
    doc = fitz.open('data/raw/ten-k-2024.pdf')
    
    results = {
        'text': [],
        'headers': [],
        'footers': [],
        'metadata': {'total_pages': len(doc)}
    }
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        blocks = page.get_text("dict")
        
        for block in blocks["blocks"]:
            if "lines" in block:
                for line in block["lines"]:
                    for span in line["spans"]:
                        content = span["text"].strip()
                        if not content:
                            continue
                        
                        font_size = span.get("size", 0)
                        bbox = span["bbox"]
                        
                        item = {
                            'content': content,
                            'page': page_num + 1,
                            'bbox': bbox,
                            'font_size': font_size
                        }
                        
                        # Classify as header, footer, or text
                        if any(kw.lower() in content.lower() for kw in params['extract']['basic_patterns']['header_keywords']):
                            results['headers'].append(item)
                        elif any(kw.lower() in content.lower() for kw in params['extract']['basic_patterns']['footer_keywords']):
                            results['footers'].append(item)
                        else:
                            results['text'].append(item)
    
    doc.close()
    
    # Save results
    Path('data/intermediate').mkdir(parents=True, exist_ok=True)
    with open('data/intermediate/basic_content.json', 'w') as f:
        json.dump(results, f, indent=2)

if __name__ == "__main__":
    extract_basic_content()