import fitz
import json
import yaml
from pathlib import Path

def extract_tables_images():
    with open('params.yaml', 'r') as f:
        params = yaml.safe_load(f)
    
    doc = fitz.open('data/raw/ten-k-2024.pdf')
    
    tables = []
    images = []
    
    for page_num in range(len(doc)):
        page = doc[page_num]
        
        # Extract tables
        try:
            page_tables = page.find_tables()
            for table in page_tables:
                table_data = table.extract()
                if (len(table_data) >= params['extract']['table_settings']['min_rows'] and 
                    len(table_data[0]) >= params['extract']['table_settings']['min_cols']):
                    tables.append({
                        'page': page_num + 1,
                        'bbox': table.bbox,
                        'data': table_data
                    })
        except:
            pass
        
        # Extract images
        image_list = page.get_images()
        for img_index, img in enumerate(image_list):
            try:
                xref = img[0]
                pix = fitz.Pixmap(doc, xref)
                if pix.n - pix.alpha < 4:
                    images.append({
                        'page': page_num + 1,
                        'xref': xref,
                        'width': pix.width,
                        'height': pix.height
                    })
                pix = None
            except:
                pass
    
    doc.close()
    
    # Save results
    Path('data/intermediate').mkdir(parents=True, exist_ok=True)
    with open('data/intermediate/tables.json', 'w') as f:
        json.dump(tables, f, indent=2)
    
    with open('data/intermediate/images.json', 'w') as f:
        json.dump(images, f, indent=2)

if __name__ == "__main__":
    extract_tables_images()