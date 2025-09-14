import json
from pathlib import Path

def combine_results():
    # Load all intermediate results
    results = {}
    
    intermediate_files = [
        'basic_content.json',
        'tables.json',
        'images.json',
        'financial_sections.json',
        'financial_statements.json',
        'exhibits.json',
        'financial_metrics.json',
        'document_outline.json'
    ]
    
    for file_name in intermediate_files:
        key = file_name.replace('.json', '')
        with open(f'data/intermediate/{file_name}', 'r') as f:
            results[key] = json.load(f)
    
    # Create summary
    summary = {
        'total_pages': results['basic_content'].get('metadata', {}).get('total_pages', 0),
        'text_blocks': len(results['basic_content'].get('text', [])),
        'headers': len(results['basic_content'].get('headers', [])),
        'footers': len(results['basic_content'].get('footers', [])),
        'tables': len(results['tables']),
        'images': len(results['images']),
        'exhibits': len(results['exhibits']),
        'outline_sections': len(results['document_outline'])
    }
    
    # Save final results
    Path('data/processed').mkdir(parents=True, exist_ok=True)
    with open('data/processed/final_results.json', 'w') as f:
        json.dump(results, f, indent=2)
    
    with open('data/processed/summary.json', 'w') as f:
        json.dump(summary, f, indent=2)

if __name__ == "__main__":
    combine_results()