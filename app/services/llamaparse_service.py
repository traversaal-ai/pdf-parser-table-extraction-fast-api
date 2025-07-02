"""
LlamaParse extraction service for table extraction from documents using LlamaParse and OpenAI.
"""
import os
import time
import pandas as pd
from pathlib import Path
from datetime import datetime
import logging
from typing import Any, Dict, List
from openai import OpenAI
from llama_parse import LlamaParse
from app.core.config import settings

# Initialize OpenAI client
openai_client = OpenAI(api_key=settings.openai_api_key)

class LlamaParseServiceError(Exception):
    """Custom exception for LlamaParse extraction errors."""
    pass

def extract_tables_with_openai(text: str) -> str:
    """
    Use OpenAI to extract tables from text and convert to HTML.
    Args:
        text (str): The text to analyze for tables.
    Returns:
        str: HTML tables or 'NO_TABLES_FOUND' or 'ERROR_PROCESSING'.
    """
    prompt = f"""
    Please analyze the following text and extract any tables you find. Convert each table to proper HTML format with:
    1. Proper HTML table structure (<table>, <thead>, <tbody>, <tr>, <th>, <td>)
    2. Clean, readable formatting
    3. Preserve all data accurately
    4. If multiple tables exist, separate them clearly
    5. If no tables are found, return "NO_TABLES_FOUND"

    Text to analyze:
    {text}

    Please return only the HTML table(s) or "NO_TABLES_FOUND":
    """
    try:
        response = openai_client.chat.completions.create(
            model="gpt-4o-mini",  # You can change this to gpt-3.5-turbo for cost savings
            messages=[
                {"role": "system", "content": "You are an expert at extracting and formatting tables from text. Return only HTML tables or 'NO_TABLES_FOUND'."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=4000,
            temperature=0.1
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        logging.error(f"[LlamaParse] OpenAI API error: {str(e)}")
        return "ERROR_PROCESSING"

def extract_tables_llamaparse(
    input_file_path: str,
    output_dir: Path,
    job_id: str,
    jobs_db: Dict[str, Any],
    TableInfo,
    ExtractionResult,
    _log: logging.Logger
) -> object:
    """
    Extract tables from document using LlamaParse + OpenAI and save as HTML.
    Args:
        input_file_path (str): Path to the input document.
        output_dir (Path): Output directory for extracted tables.
        job_id (str): Unique job identifier.
        jobs_db (dict): Job status tracking.
        TableInfo: Pydantic model for table info.
        ExtractionResult: Pydantic model for extraction result.
        _log (logging.Logger): Logger instance.
    Returns:
        ExtractionResult: Extraction result object.
    Raises:
        LlamaParseServiceError: If extraction fails.
    """
    try:
        jobs_db[job_id]["status"] = "processing"
        jobs_db[job_id]["progress"] = 10
        jobs_db[job_id]["message"] = "Initializing LlamaParse..."
        _log.info(f"[LlamaParse] Starting extraction for job {job_id}")
        start_time = time.time()
        # Create output directory: output_dir/llamaparse
        llamaparse_dir = output_dir / "llamaparse"
        llamaparse_dir.mkdir(parents=True, exist_ok=True)
        _log.info(f"[LlamaParse] Created directory: {llamaparse_dir}")
        # Initialize LlamaParse
        llamaparse_api_key = settings.llamaparse_api_key
        parser = LlamaParse(
            api_key=llamaparse_api_key,
            result_type="markdown",
            extract_charts=True,
            auto_mode=True,
            auto_mode_trigger_on_image_in_page=True,
            auto_mode_trigger_on_table_in_page=True,
        )
        jobs_db[job_id]["progress"] = 20
        jobs_db[job_id]["message"] = "Processing document with LlamaParse..."
        # Parse the document
        file_name = os.path.basename(input_file_path)
        extra_info = {"file_name": file_name}
        with open(input_file_path, "rb") as f:
            documents = parser.load_data(f, extra_info=extra_info)
        _log.info(f"[LlamaParse] Extracted {len(documents)} document sections")
        jobs_db[job_id]["progress"] = 40
        jobs_db[job_id]["message"] = f"Found {len(documents)} document sections. Processing with OpenAI..."
        doc_filename = Path(input_file_path).stem
        all_tables: List[dict] = []
        table_counter = 0
        # Process each document section
        for doc_idx, doc in enumerate(documents):
            progress = 40 + int((doc_idx / len(documents)) * 50)
            jobs_db[job_id]["progress"] = progress
            jobs_db[job_id]["message"] = f"Processing section {doc_idx + 1}/{len(documents)} with OpenAI..."
            # Extract tables using OpenAI
            html_content = extract_tables_with_openai(doc.text)
            if html_content == "NO_TABLES_FOUND":
                _log.info(f"[LlamaParse] No tables found in document section {doc_idx + 1}")
                continue
            elif html_content == "ERROR_PROCESSING":
                _log.warning(f"[LlamaParse] Error processing document section {doc_idx + 1}")
                continue
            # Split multiple tables if they exist in the response
            tables_in_section = []
            if "<table" in html_content.lower():
                parts = html_content.split("</table>")
                for part in parts:
                    if "<table" in part.lower():
                        table_start = part.lower().find("<table")
                        if table_start != -1:
                            table_html = part[table_start:] + "</table>"
                            tables_in_section.append(table_html)
            if not tables_in_section and "<table" in html_content.lower():
                tables_in_section = [html_content]
            # Save each table as HTML file
            for table_html in tables_in_section:
                table_counter += 1
                styled_html = f"""<!DOCTYPE html>\n<html lang=\"en\">\n<head>\n    <meta charset=\"UTF-8\">\n    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">\n    <title>Table {table_counter} - {doc_filename}</title>\n    <style>\n        body {{\n            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;\n            margin: 20px;\n            background-color: #f5f5f5;\n        }}\n        .container {{\n            max-width: 1200px;\n            margin: 0 auto;\n            background: white;\n            padding: 20px;\n            border-radius: 8px;\n            box-shadow: 0 2px 10px rgba(0,0,0,0.1);\n        }}\n        h1 {{\n            color: #333;\n            border-bottom: 3px solid #667eea;\n            padding-bottom: 10px;\n        }}\n        table {{\n            border-collapse: collapse;\n            width: 100%;\n            margin-top: 20px;\n        }}\n        th {{\n            background: #667eea;\n            color: white;\n            padding: 12px;\n            text-align: left;\n        }}\n        td {{\n            border: 1px solid #ddd;\n            padding: 10px;\n        }}\n        tr:nth-child(even) {{\n            background-color: #f9f9f9;\n        }}\n        tr:hover {{\n            background-color: #f5f5f5;\n        }}\n        .stats {{\n            background: #f8f9fa;\n            padding: 15px;\n            border-radius: 6px;\n            margin-bottom: 20px;\n        }}\n    </style>\n</head>\n<body>\n    <div class=\"container\">\n        <h1>📊 Table {table_counter}</h1>\n        <div class=\"stats\">\n            <strong>Document:</strong> {doc_filename}<br>\n            <strong>Section:</strong> {doc_idx + 1} | \n            <strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n        </div>\n        {table_html}\n    </div>\n</body>\n</html>"""
                html_filename = f"{doc_filename}-table-{table_counter}.html"
                html_path = llamaparse_dir / html_filename
                with open(html_path, "w", encoding="utf-8") as f:
                    f.write(styled_html)
                _log.info(f"[LlamaParse] Saved HTML table: {html_path}")
                table_info = {
                    "table_id": table_counter,
                    "section": doc_idx + 1,
                    "html_file": str(html_path),
                    "html_content": table_html
                }
                all_tables.append(table_info)
        # Save summary file with all tables
        if all_tables:
            summary_html = f"""<!DOCTYPE html>\n<html lang=\"en\">\n<head>\n    <meta charset=\"UTF-8\">\n    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">\n    <title>All Tables - {doc_filename}</title>\n    <style>\n        body {{\n            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;\n            margin: 20px;\n            background-color: #f5f5f5;\n        }}\n        .container {{\n            max-width: 1200px;\n            margin: 0 auto;\n            background: white;\n            padding: 20px;\n            border-radius: 8px;\n            box-shadow: 0 2px 10px rgba(0,0,0,0.1);\n        }}\n        h1 {{\n            color: #333;\n            border-bottom: 3px solid #667eea;\n            padding-bottom: 10px;\n        }}\n        .table-section {{\n            margin: 30px 0;\n            padding: 20px;\n            border: 1px solid #ddd;\n            border-radius: 8px;\n        }}\n        table {{\n            border-collapse: collapse;\n            width: 100%;\n            margin-top: 20px;\n        }}\n        th {{\n            background: #667eea;\n            color: white;\n            padding: 12px;\n            text-align: left;\n        }}\n        td {{\n            border: 1px solid #ddd;\n            padding: 10px;\n        }}\n        tr:nth-child(even) {{\n            background-color: #f9f9f9;\n        }}\n        tr:hover {{\n            background-color: #f5f5f5;\n        }}\n        .stats {{\n            background: #f8f9fa;\n            padding: 15px;\n            border-radius: 6px;\n            margin-bottom: 20px;\n        }}\n    </style>\n</head>\n<body>\n    <div class=\"container\">\n        <h1>All Tables - {doc_filename}</h1>\n        {''.join([f'<div class=\"table-section\">' + t['html_content'] + '</div>' for t in all_tables])}\n    </div>\n</body>\n</html>"""
            summary_path = llamaparse_dir / f"{doc_filename}-all-tables.html"
            with open(summary_path, "w", encoding="utf-8") as f:
                f.write(summary_html)
            _log.info(f"[LlamaParse] Saved summary file: {summary_path}")
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
            total_tables=len(all_tables),
            tables=[],  # You can populate this with table info if needed
            output_directory=str(llamaparse_dir.absolute()),
            message=f"Successfully extracted {len(all_tables)} tables in {processing_time:.2f} seconds"
        )
        _log.info(f"[LlamaParse] Extraction completed for job {job_id}: {len(all_tables)} tables in {processing_time:.2f}s")
        return result
    except Exception as e:
        jobs_db[job_id]["status"] = "failed"
        jobs_db[job_id]["message"] = f"Processing failed: {str(e)}"
        jobs_db[job_id]["completed_at"] = datetime.now()
        _log.error(f"[LlamaParse] Extraction failed for job {job_id}: {str(e)}")
        raise LlamaParseServiceError(f"LlamaParse extraction failed: {str(e)}")

def process_document_background_llamaparse(
    file_path: str,
    output_dir: Path,
    job_id: str,
    jobs_db: Dict[str, Any],
    TableInfo,
    ExtractionResult,
    _log: logging.Logger
) -> None:
    """
    Background task for processing documents with LlamaParse + OpenAI.
    """
    try:
        result = extract_tables_llamaparse(file_path, output_dir, job_id, jobs_db, TableInfo, ExtractionResult, _log)
        jobs_db[job_id]["result"] = result
    except Exception as e:
        _log.error(f"[LlamaParse] Background processing failed for job {job_id}: {str(e)}")