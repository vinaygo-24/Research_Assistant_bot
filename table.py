import camelot
import tempfile
import os

def extract_tables_to_text(pdf_bytes):
    if not pdf_bytes: return []
    
    table_data_list = []
    
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(pdf_bytes)
        temp_path = tmp.name

    try:
        # 'lattice' is better for bordered tables, 'stream' for whitespace
        tables = camelot.read_pdf(temp_path, pages="all", flavor='lattice')
        print(f"[table] Found {len(tables)} tables.")

        for i, tbl in enumerate(tables):
            df = tbl.df
            # Convert to CSV string for embedding
            csv_text = f"Table {i+1} Data (CSV Format):\n" + df.to_csv(index=False, sep=',')
            
            table_data_list.append({
                "text": csv_text,
                "type": "table",
                "image_path": "", # Tables don't have separate image files in this method
                "page": tbl.page
            })
    except Exception as e:
        print(f"[table] Error: {e}")
    finally:
        if os.path.exists(temp_path): os.remove(temp_path)
        
    return table_data_list