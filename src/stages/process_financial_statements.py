import json
import pandas as pd
from pathlib import Path

def process_financial_statements():
    with open('data/intermediate/tables.json', 'r') as f:
        tables = json.load(f)
    
    statements = {
        'balance_sheet': [],
        'income_statement': [],
        'cash_flow': [],
        'equity_statement': [],
        'other_financial': []
    }
    
    for table in tables:
        table_text = str(table.get('data', [])).lower()
        
        if any(term in table_text for term in ['assets', 'liabilities', 'balance']):
            statements['balance_sheet'].append(table)
        elif any(term in table_text for term in ['revenue', 'income', 'earnings']):
            statements['income_statement'].append(table)
        elif any(term in table_text for term in ['cash flow', 'operating activities']):
            statements['cash_flow'].append(table)
        elif any(term in table_text for term in ['equity', 'shareholders']):
            statements['equity_statement'].append(table)
        else:
            statements['other_financial'].append(table)
    
    # Save JSON results
    with open('data/intermediate/financial_statements.json', 'w') as f:
        json.dump(statements, f, indent=2)
    
    # Save CSV files
    statements_dir = Path('data/processed/statements')
    statements_dir.mkdir(parents=True, exist_ok=True)
    
    for statement_type, tables_list in statements.items():
        for i, table in enumerate(tables_list):
            if 'data' in table and table['data']:
                df = pd.DataFrame(table['data'])
                df.to_csv(statements_dir / f"{statement_type}_{i+1}.csv", index=False)

if __name__ == "__main__":
    process_financial_statements()