"""
Unstructured extraction service for table extraction from documents using Unstructured API.
"""
import os
from unstructured_client import UnstructuredClient
from unstructured_client.models import shared, operations
import time
import pandas as pd
from pathlib import Path
from datetime import datetime
import logging
from typing import Any, Dict
from bs4 import BeautifulSoup
from app.core.config import settings

client = UnstructuredClient(api_key_auth=settings.unstructured_api_key)

class UnstructuredServiceError(Exception):
    """Custom exception for Unstructured extraction errors."""
    pass

def extract_tables_from_file_unstructured(
    input_file_path: str,
    output_dir: Path,
    job_id: str,
    jobs_db: Dict[str, Any],
    TableInfo,
    ExtractionResult,
    _log: logging.Logger,
    client: UnstructuredClient
) -> object:
    """
    Extract tables from document using Unstructured and save as CSV/HTML/Excel.
    Args:
        input_file_path (str): Path to the input document.
        output_dir (Path): Output directory for extracted tables.
        job_id (str): Unique job identifier.
        jobs_db (dict): Job status tracking.
        TableInfo: Pydantic model for table info.
        ExtractionResult: Pydantic model for extraction result.
        _log (logging.Logger): Logger instance.
        client (UnstructuredClient): Unstructured API client.
    Returns:
        ExtractionResult: Extraction result object.
    Raises:
        UnstructuredServiceError: If extraction fails.
    """
    try:
        jobs_db[job_id]["status"] = "processing"
        jobs_db[job_id]["progress"] = 10
        jobs_db[job_id]["message"] = "Initializing Unstructured client..."
        _log.info(f"[Unstructured] Starting extraction for job {job_id}")
        start_time = time.time()
        # Create single output directory: output_dir/unstructured
        unstructured_dir = output_dir / "unstructured"
        unstructured_dir.mkdir(parents=True, exist_ok=True)
        _log.info(f"[Unstructured] Created directory: {unstructured_dir}")
        jobs_db[job_id]["progress"] = 20
        jobs_db[job_id]["message"] = "Processing document with Unstructured..."
        with open(input_file_path, "rb") as f:
            files = shared.Files(
                content=f.read(),
                file_name=os.path.basename(input_file_path)
            )
        req = operations.PartitionRequest(
            partition_parameters=shared.PartitionParameters(
                files=files,
                strategy=shared.Strategy.HI_RES,
                split_pdf_page=True,
                split_pdf_allow_failed=True,
                split_pdf_concurrency_level=15,
                extract_image_block_types=["Image", "Table"],
                infer_table_structure=True,
                chunking_strategy="by_title",
                max_characters=4000,
                new_after_n_chars=3800,
                combine_text_under_n_chars=2000,
            )
        )
        resp = client.general.partition(request=req)
        tables = []
        for element in resp.elements:
            try:
                if (element.get("type") == "Table" or 
                    ("text_as_html" in element.get("metadata", {}) or 
                     "image_base64" in element.get("metadata", {}))):
                    page_num = element["metadata"].get("page_number", "UNKNOWN")
                    table_html = element["metadata"].get("text_as_html", "")
                    table_text = element.get("text", "")
                    table_content = table_html if table_html else table_text
                    table_data = {
                        "html": table_html,
                        "text": table_text,
                        "page_num": page_num
                    }
                    if "image_base64" in element.get("metadata", {}):
                        table_data["image_base64"] = element["metadata"]["image_base64"]
                    tables.append(table_data)
            except Exception as e:
                _log.warning(f"[Unstructured] Error processing element: {str(e)}")
                continue
        doc_filename = Path(input_file_path).stem
        tables_info = []
        total_tables = len(tables)
        jobs_db[job_id]["progress"] = 30
        jobs_db[job_id]["message"] = f"Found {total_tables} tables. Processing..."
        excel_files = []
        for table_ix, table_data in enumerate(tables):
            progress = 30 + int((table_ix / total_tables) * 60) if total_tables > 0 else 90
            jobs_db[job_id]["progress"] = progress
            jobs_db[job_id]["message"] = f"Processing table {table_ix + 1}/{total_tables}..."
            if not table_data['html']:
                _log.warning(f"[Unstructured] Table {table_ix + 1} has no HTML content, skipping...")
                continue
            # Save HTML file directly in unstructured_dir
            html_filename = f"{doc_filename}-table-{table_ix + 1}.html"
            element_html_path = unstructured_dir / html_filename
            styled_html = f"""<!DOCTYPE html>\n<html lang=\"en\">\n<head>\n    <meta charset=\"UTF-8\">\n    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">\n    <title>Table {table_ix + 1} - {doc_filename}</title>\n    <style>\n        body {{\n            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;\n            margin: 20px;\n            background-color: #f5f5f5;\n        }}\n        .container {{\n            max-width: 1200px;\n            margin: 0 auto;\n            background: white;\n            padding: 20px;\n            border-radius: 8px;\n            box-shadow: 0 2px 10px rgba(0,0,0,0.1);\n        }}\n        h1 {{\n            color: #333;\n            border-bottom: 3px solid #667eea;\n            padding-bottom: 10px;\n        }}\n        table {{\n            border-collapse: collapse;\n            width: 100%;\n            margin-top: 20px;\n        }}\n        th {{\n            background: #667eea;\n            color: white;\n            padding: 12px;\n            text-align: left;\n        }}\n        td {{\n            border: 1px solid #ddd;\n            padding: 10px;\n        }}\n        tr:nth-child(even) {{\n            background-color: #f9f9f9;\n        }}\n        tr:hover {{\n            background-color: #f5f5f5;\n        }}\n        .stats {{\n            background: #f8f9fa;\n            padding: 15px;\n            border-radius: 6px;\n            margin-bottom: 20px;\n        }}\n    </style>\n</head>\n<body>\n    <div class=\"container\">\n        <h1>📊 Table {table_ix + 1}</h1>\n        <div class=\"stats\">\n            <strong>Document:</strong> {doc_filename}<br>\n            <strong>Page:</strong> {table_data['page_num']} | \n            <strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n        </div>\n        {table_data['html']}\n    </div>\n</body>\n</html>"""
            with open(element_html_path, "w", encoding="utf-8") as fp:
                fp.write(styled_html)
            _log.info(f"[Unstructured] Saved HTML: {element_html_path}")
            # Convert to DataFrame and handle MultiIndex columns
            try:
                df_list = pd.read_html(table_data['html'])
                if df_list:
                    table_df = df_list[0]
                    if isinstance(table_df.columns, pd.MultiIndex):
                        table_df.columns = [' '.join(map(str, col)).strip() for col in table_df.columns.values]
                    # Save Excel file directly in unstructured_dir
                    excel_filename = f"{doc_filename}-table-{table_ix + 1}.xlsx"
                    element_excel_path = unstructured_dir / excel_filename
                    table_df.to_excel(element_excel_path, index=False)
                    excel_files.append(element_excel_path)
                    _log.info(f"[Unstructured] Saved Excel: {element_excel_path}")
            except Exception as e:
                _log.warning(f"[Unstructured] Failed to convert HTML to Excel for table {table_ix + 1}: {str(e)}")
                continue
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
            total_tables=len(tables),
            tables=tables_info,
            output_directory=str(unstructured_dir.absolute()),
            message=f"Successfully extracted {len(tables)} tables in {processing_time:.2f} seconds"
        )
        _log.info(f"[Unstructured] Extraction completed for job {job_id}: {len(tables)} tables in {processing_time:.2f}s")
        return result
    except Exception as e:
        jobs_db[job_id]["status"] = "failed"
        jobs_db[job_id]["message"] = f"Processing failed: {str(e)}"
        jobs_db[job_id]["completed_at"] = datetime.now()
        _log.error(f"[Unstructured] Extraction failed for job {job_id}: {str(e)}")
        raise UnstructuredServiceError(f"Unstructured extraction failed: {str(e)}")

def process_document_background_unstructured(
    file_path: str,
    output_dir: Path,
    job_id: str,
    jobs_db: Dict[str, Any],
    TableInfo,
    ExtractionResult,
    _log: logging.Logger,
    client: UnstructuredClient
) -> None:
    """
    Background task for processing documents with Unstructured.
    """
    try:
        result = extract_tables_from_file_unstructured(file_path, output_dir, job_id, jobs_db, TableInfo, ExtractionResult, _log, client)
        jobs_db[job_id]["result"] = result
    except Exception as e:
        _log.error(f"[Unstructured] Background processing failed for job {job_id}: {str(e)}")