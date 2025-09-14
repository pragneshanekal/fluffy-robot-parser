import json
import yaml
import re
from pathlib import Path

def extract_metrics():
    with open('params.yaml', 'r') as f:
        params = yaml.safe_load(f)
    
    with open('data/intermediate/basic_content.json', 'r') as f:
        basic_content = json.load(f)
    
    metrics = {
        'currency_amounts': [],
        'percentages': [],
        'share_data': []
    }
    
    patterns = params['extraction']['metric_patterns']
    
    for block in basic_content['text']:
        content = block['content']
        
        # Extract currency amounts
        currency_matches = re.findall(patterns['currency'], content)
        if currency_matches:
            metrics['currency_amounts'].extend([{
                'value': match,
                'context': content[:100] + '...',
                'page': block['page']
            } for match in currency_matches])
        
        # Extract percentages
        percentage_matches = re.findall(patterns['percentage'], content)
        if percentage_matches:
            metrics['percentages'].extend([{
                'value': match,
                'context': content[:100] + '...',
                'page': block['page']
            } for match in percentage_matches])
        
        # Extract share data
        share_matches = re.findall(patterns['shares'], content)
        if share_matches:
            metrics['share_data'].extend([{
                'value': match,
                'context': content[:100] + '...',
                'page': block['page']
            } for match in share_matches])
    
    # Save results
    with open('data/intermediate/financial_metrics.json', 'w') as f:
        json.dump(metrics, f, indent=2)

if __name__ == "__main__":
    extract_metrics()