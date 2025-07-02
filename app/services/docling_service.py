import time
import pandas as pd
from pathlib import Path
from datetime import datetime
import logging

try:
    from docling.document_converter import DocumentConverter
    DOCLING_AVAILABLE = True
except ImportError:
    DOCLING_AVAILABLE = False


def extract_tables_from_file(input_file_path: str, output_dir: Path, job_id: str, jobs_db, TableInfo, ExtractionResult, _log: logging.Logger) -> object:
    """
    Extract tables from document and save as CSV/HTML
    """
    if not DOCLING_AVAILABLE:
        raise Exception("DocumentConverter not available. Please install docling.")
    try:
        jobs_db[job_id]["status"] = "processing"
        jobs_db[job_id]["progress"] = 10
        jobs_db[job_id]["message"] = "Initializing DocumentConverter..."
        _log.info(f"Starting extraction for job {job_id}")
        doc_converter = DocumentConverter()
        start_time = time.time()
        jobs_db[job_id]["progress"] = 20
        jobs_db[job_id]["message"] = "Converting document..."
        conv_res = doc_converter.convert(input_file_path)
        docling_dir = output_dir / "docling"
        docling_dir.mkdir(parents=True, exist_ok=True)
        doc_filename = Path(input_file_path).stem
        tables_info = []
        total_tables = len(conv_res.document.tables)
        jobs_db[job_id]["progress"] = 30
        jobs_db[job_id]["message"] = f"Found {total_tables} tables. Processing..."
        for table_ix, table in enumerate(conv_res.document.tables):
            progress = 30 + int((table_ix / total_tables) * 60)
            jobs_db[job_id]["progress"] = progress
            jobs_db[job_id]["message"] = f"Processing table {table_ix + 1}/{total_tables}..."
            table_df: pd.DataFrame = table.export_to_dataframe()
            if table_df.empty:
                _log.warning(f"Table {table_ix} is empty, skipping...")
                continue
            _log.info(f"Processing Table {table_ix + 1}: {len(table_df)} rows, {len(table_df.columns)} columns")
            csv_filename = f"{doc_filename}-table-{table_ix + 1}.csv"
            element_csv_path = docling_dir / csv_filename
            table_df.to_csv(element_csv_path, index=False)
            _log.info(f"Saved CSV: {element_csv_path}")
            html_filename = f"{doc_filename}-table-{table_ix + 1}.html"
            element_html_path = docling_dir / html_filename
            try:
                html_content = table.export_to_html(doc=conv_res.document)
                styled_html = f"""<!DOCTYPE html>\n<html lang=\"en\">\n<head>\n    <meta charset=\"UTF-8\">\n    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">\n    <title>Table {table_ix + 1} - {doc_filename}</title>\n    <style>\n        body {{\n            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;\n            margin: 20px;\n            background-color: #f5f5f5;\n        }}\n        .container {{\n            max-width: 1200px;\n            margin: 0 auto;\n            background: white;\n            padding: 20px;\n            border-radius: 8px;\n            box-shadow: 0 2px 10px rgba(0,0,0,0.1);\n        }}\n        h1 {{\n            color: #333;\n            border-bottom: 3px solid #667eea;\n            padding-bottom: 10px;\n        }}\n        table {{\n            border-collapse: collapse;\n            width: 100%;\n            margin-top: 20px;\n        }}\n        th {{\n            background: #667eea;\n            color: white;\n            padding: 12px;\n            text-align: left;\n        }}\n        td {{\n            border: 1px solid #ddd;\n            padding: 10px;\n        }}\n        tr:nth-child(even) {{\n            background-color: #f9f9f9;\n        }}\n        tr:hover {{\n            background-color: #f5f5f5;\n        }}\n        .stats {{\n            background: #f8f9fa;\n            padding: 15px;\n            border-radius: 6px;\n            margin-bottom: 20px;\n        }}\n    </style>\n</head>\n<body>\n    <div class=\"container\">\n        <h1>📊 Table {table_ix + 1}</h1>\n        <div class=\"stats\">\n            <strong>Document:</strong> {doc_filename}<br>\n            <strong>Rows:</strong> {len(table_df)} | \n            <strong>Columns:</strong> {len(table_df.columns)} | \n            <strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n        </div>\n        {html_content}\n    </div>\n</body>\n</html>"""
                with open(element_html_path, "w", encoding="utf-8") as fp:
                    fp.write(styled_html)
            except Exception as e:
                _log.warning(f"DocumentConverter HTML export failed: {e}. Using pandas fallback.")
                fallback_html = f"""<!DOCTYPE html>\n<html><head><title>Table {table_ix + 1}</title></head>\n<body><h1>Table {table_ix + 1} - {doc_filename}</h1>\n{table_df.to_html(index=False)}</body></html>"""
                with open(element_html_path, "w", encoding="utf-8") as fp:
                    fp.write(fallback_html)
            _log.info(f"Saved HTML: {element_html_path}")
            tables_info.append(TableInfo(
                table_index=table_ix,
                csv_path=str(element_csv_path.absolute()),
                html_path=str(element_html_path.absolute()),
                rows=len(table_df),
                columns=len(table_df.columns),
                filename_csv=csv_filename,
                filename_html=html_filename
            ))
        processing_time = time.time() - start_time
        jobs_db[job_id]["status"] = "completed"
        jobs_db[job_id]["progress"] = 100
        jobs_db[job_id]["message"] = "Processing completed successfully!"
        jobs_db[job_id]["completed_at"] = datetime.now()
        
        result = ExtractionResult(
            job_id=job_id,
            status="completed",
            document_name=doc_filename,
            processing_time=processing_time,
            total_tables=len(tables_info),
            tables=tables_info,
            output_directory=str(docling_dir.absolute()),
            message=f"Successfully extracted {len(tables_info)} tables in {processing_time:.2f} seconds"
        )
        _log.info(f"Extraction completed for job {job_id}: {len(tables_info)} tables in {processing_time:.2f}s")
        return result
    except Exception as e:
        jobs_db[job_id]["status"] = "failed"
        jobs_db[job_id]["message"] = f"Processing failed: {str(e)}"
        jobs_db[job_id]["completed_at"] = datetime.now()
        _log.error(f"Extraction failed for job {job_id}: {str(e)}")
        raise

def process_document_background(file_path: str, output_dir: Path, job_id: str, jobs_db, TableInfo, ExtractionResult, _log: logging.Logger):
    """Background task for processing documents"""
    try:
        result = extract_tables_from_file(file_path, output_dir, job_id, jobs_db, TableInfo, ExtractionResult, _log)
        jobs_db[job_id]["result"] = result
    except Exception as e:
        _log.error(f"Background processing failed for job {job_id}: {str(e)}")
