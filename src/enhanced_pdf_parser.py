import fitz
import pandas as pd
import re
from typing import Dict, List, Tuple, Any
from dataclasses import dataclass
import json
import os
from pathlib import Path

class FinancialDocumentParser(PDFLayoutParser):
    """Enhanced parser specifically for financial documents like 10-K forms"""
    
    def __init__(self):
        super().__init__()
        self.financial_patterns = {
            'financial_statements': [
                'consolidated statements', 'balance sheet', 'income statement', 
                'cash flows', 'shareholders equity', 'comprehensive income'
            ],
            'exhibits': ['exhibit'],
            'notes': ['notes to consolidated financial statements', 'note \\d+'],
            'sections': ['item \\d+', 'part [IVX]+'],
            'financial_data': [
                r'\$\s*[\d,]+(?:\.\d+)?(?:\s*million)?(?:\s*billion)?',
                r'[\d,]+\.\d+%',
                r'[\d,]+(?:\s*shares?)?(?:\s*outstanding)?'
            ]
        }
    
    def parse_financial_document(self, pdf_path: str) -> Dict:
        """Parse financial document with enhanced structure detection"""
        results = self.parse_pdf(pdf_path)
        
        # Enhanced processing for financial documents
        enhanced_results = self._enhance_financial_content(results)
        
        return enhanced_results
    
    def _enhance_financial_content(self, results: Dict) -> Dict:
        """Enhance results with financial document specific processing"""
        enhanced = results.copy()
        
        # Classify content by financial document sections
        enhanced['financial_sections'] = self._classify_financial_sections(results['text'])
        
        # Extract financial statements separately
        enhanced['financial_statements'] = self._extract_financial_statements(results['tables'])
        
        # Process exhibits
        enhanced['exhibits'] = self._process_exhibits(results)
        
        # Extract key financial metrics
        enhanced['financial_metrics'] = self._extract_financial_metrics(results['text'])
        
        # Create document outline
        enhanced['document_outline'] = self._create_document_outline(results)
        
        return enhanced
    
    def _classify_financial_sections(self, text_blocks: List[Dict]) -> Dict:
        """Classify text blocks into financial document sections"""
        sections = {
            'business_description': [],
            'risk_factors': [],
            'financial_statements': [],
            'notes_to_statements': [],
            'exhibits': [],
            'other': []
        }
        
        for block in text_blocks:
            content = block['content'].lower()
            
            if any(pattern in content for pattern in ['item 1.', 'business']):
                sections['business_description'].append(block)
            elif any(pattern in content for pattern in ['risk factor', 'item 1a']):
                sections['risk_factors'].append(block)
            elif any(pattern in content for pattern in self.financial_patterns['financial_statements']):
                sections['financial_statements'].append(block)
            elif any(re.search(pattern, content) for pattern in self.financial_patterns['notes']):
                sections['notes_to_statements'].append(block)
            elif 'exhibit' in content:
                sections['exhibits'].append(block)
            else:
                sections['other'].append(block)
        
        return sections
    
    def _extract_financial_statements(self, tables: List[Dict]) -> Dict:
        """Extract and classify financial statements"""
        statements = {
            'balance_sheet': [],
            'income_statement': [],
            'cash_flow': [],
            'equity_statement': [],
            'other_financial': []
        }
        
        for table in tables:
            # Try to classify based on content or metadata
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
        
        return statements
    
    def _process_exhibits(self, results: Dict) -> List[Dict]:
        """Process and organize exhibits"""
        exhibits = []
        
        # Look for exhibit patterns in headers and text
        all_content = results['text'] + results['headers']
        
        for block in all_content:
            content = block['content']
            
            # Match exhibit patterns
            exhibit_match = re.search(r'exhibit\s+(\d+\.\d+|\d+[a-z]?)', content.lower())
            if exhibit_match:
                exhibits.append({
                    'exhibit_number': exhibit_match.group(1),
                    'content': content,
                    'page': block['page'],
                    'bbox': block['bbox']
                })
        
        return exhibits
    
    def _extract_financial_metrics(self, text_blocks: List[Dict]) -> Dict:
        """Extract key financial metrics from text"""
        metrics = {
            'revenue_figures': [],
            'percentages': [],
            'share_data': [],
            'currency_amounts': []
        }
        
        for block in text_blocks:
            content = block['content']
            
            # Extract various financial patterns
            for pattern_type, patterns in self.financial_patterns['financial_data']:
                if isinstance(patterns, list):
                    for pattern in patterns:
                        matches = re.findall(pattern, content)
                        if matches:
                            metrics[pattern_type].extend([{
                                'value': match,
                                'context': content[:100] + '...',
                                'page': block['page']
                            } for match in matches])
        
        return metrics
    
    def _create_document_outline(self, results: Dict) -> List[Dict]:
        """Create a document outline based on headers and sections"""
        outline = []
        
        # Process headers to build outline
        headers = sorted(results['headers'], key=lambda x: x['page'])
        
        for header in headers:
            content = header['content']
            
            # Check for section markers
            section_match = re.search(r'(item\s+\d+[a-z]?|part\s+[IVX]+|exhibit\s+\d+)', content.lower())
            if section_match:
                outline.append({
                    'section': section_match.group(1).upper(),
                    'title': content.strip(),
                    'page': header['page'],
                    'bbox': header['bbox']
                })
        
        return outline
    
    def save_enhanced_results(self, output_dir: str = "financial_parsed_output"):
        """Save enhanced financial document results"""
        # First save standard results
        super().save_results(output_dir)
        
        # Save enhanced financial content
        enhanced_data = {
            'financial_sections': self.results.get('financial_sections', {}),
            'financial_statements': self.results.get('financial_statements', {}),
            'exhibits': self.results.get('exhibits', []),
            'financial_metrics': self.results.get('financial_metrics', {}),
            'document_outline': self.results.get('document_outline', [])
        }
        
        with open(f"{output_dir}/financial_analysis.json", "w", encoding="utf-8") as f:
            json.dump(enhanced_data, f, indent=2, ensure_ascii=False)
        
        # Save document outline as separate file
        with open(f"{output_dir}/document_outline.json", "w", encoding="utf-8") as f:
            json.dump(self.results.get('document_outline', []), f, indent=2, ensure_ascii=False)
        
        # Save financial statements as separate CSV files
        if 'financial_statements' in self.results:
            statements_dir = f"{output_dir}/financial_statements"
            os.makedirs(statements_dir, exist_ok=True)
            
            for statement_type, tables in self.results['financial_statements'].items():
                for i, table in enumerate(tables):
                    if 'data' in table:
                        df = pd.DataFrame(table['data'])
                        df.to_csv(f"{statements_dir}/{statement_type}_{i+1}.csv", index=False)
        
        print(f"Enhanced financial results saved to {output_dir}/")

def parse_apple_10k():
    """Specific function to parse Apple 10-K document"""
    parser = FinancialDocumentParser()
    
    # Parse the Apple 10-K document
    pdf_path = "ten-k-2024.pdf"
    
    if not os.path.exists(pdf_path):
        print(f"PDF file not found: {pdf_path}")
        return None
    
    print("Parsing Apple 10-K document...")
    results = parser.parse_financial_document(pdf_path)
    
    # Print detailed summary
    print("\nApple 10-K Parsing Summary:")
    print("=" * 60)
    
    # Basic stats
    if 'summary' in results:
        for key, value in results['summary'].items():
            print(f"{key.replace('_', ' ').title()}: {value}")
    
    print("\nFinancial Document Specific Analysis:")
    print("-" * 40)
    
    # Financial sections
    if 'financial_sections' in results:
        for section, blocks in results['financial_sections'].items():
            print(f"{section.replace('_', ' ').title()}: {len(blocks)} blocks")
    
    # Financial statements
    if 'financial_statements' in results:
        for statement_type, tables in results['financial_statements'].items():
            print(f"{statement_type.replace('_', ' ').title()}: {len(tables)} tables")
    
    # Exhibits
    if 'exhibits' in results:
        print(f"Exhibits Found: {len(results['exhibits'])}")
        for exhibit in results['exhibits'][:5]:  # Show first 5
            print(f"  - Exhibit {exhibit['exhibit_number']}: Page {exhibit['page']}")
    
    # Document outline
    if 'document_outline' in results:
        print(f"\nDocument Outline ({len(results['document_outline'])} sections):")
        for section in results['document_outline'][:10]:  # Show first 10
            print(f"  {section['section']}: {section['title'][:60]}...")
    
    # Save results
    parser.save_enhanced_results("apple_10k_parsed")
    
    return results

# Advanced usage example
def advanced_content_analysis(results: Dict):
    """Perform advanced analysis on parsed content"""
    analysis = {}
    
    # Analyze text complexity
    text_stats = {
        'total_words': 0,
        'avg_words_per_block': 0,
        'pages_with_tables': set(),
        'pages_with_images': set()
    }
    
    if 'text' in results:
        total_blocks = len(results['text'])
        for block in results['text']:
            words = len(block['content'].split())
            text_stats['total_words'] += words
        
        if total_blocks > 0:
            text_stats['avg_words_per_block'] = text_stats['total_words'] / total_blocks
    
    # Identify pages with complex content
    if 'tables' in results:
        text_stats['pages_with_tables'] = set(table.get('page', 0) for table in results['tables'])
    
    if 'images' in results:
        text_stats['pages_with_images'] = set(img.get('page', 0) for img in results['images'])
    
    analysis['text_statistics'] = text_stats
    
    # Find the most content-heavy pages
    page_content_count = {}
    for content_type in ['text', 'tables', 'images', 'headers', 'footers']:
        if content_type in results:
            for item in results[content_type]:
                page = item.get('page', 0)
                page_content_count[page] = page_content_count.get(page, 0) + 1
    
    # Sort pages by content density
    analysis['content_dense_pages'] = sorted(
        page_content_count.items(), 
        key=lambda x: x[1], 
        reverse=True
    )[:10]
    
    return analysis

if __name__ == "__main__":
    # Parse the Apple 10-K
    results = parse_apple_10k()
    
    if results:
        # Perform advanced analysis
        analysis = advanced_content_analysis(results)
        
        print("\nAdvanced Analysis:")
        print("-" * 30)
        print(f"Total words extracted: {analysis['text_statistics']['total_words']:,}")
        print(f"Average words per block: {analysis['text_statistics']['avg_words_per_block']:.1f}")
        print(f"Pages with tables: {len(analysis['text_statistics']['pages_with_tables'])}")
        print(f"Pages with images: {len(analysis['text_statistics']['pages_with_images'])}")
        
        print("\nMost content-dense pages:")
        for page, count in analysis['content_dense_pages']:
            print(f"  Page {page}: {count} content blocks")
