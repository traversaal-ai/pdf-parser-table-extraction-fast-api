import os
import time
import pandas as pd
from pathlib import Path
from datetime import datetime
import logging
from openai import OpenAI
from llama_parse import LlamaParse
from app.core.config import settings

# Initialize OpenAI client
openai_client = OpenAI(api_key=settings.openai_api_key)

def extract_tables_with_openai(text: str) -> str:
    """
    Use OpenAI to extract tables from text and convert to HTML
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
        logging.error(f"OpenAI API error: {str(e)}")
        return "ERROR_PROCESSING"

def extract_tables_llamaparse(input_file_path: str, output_dir: Path, job_id: str, jobs_db, TableInfo, ExtractionResult, _log: logging.Logger) -> object:
    """
    Extract tables from document using LlamaParse + OpenAI and save as HTML
    """
    try:
        jobs_db[job_id]["status"] = "processing"
        jobs_db[job_id]["progress"] = 10
        jobs_db[job_id]["message"] = "Initializing LlamaParse..."
        _log.info(f"Starting extraction for job {job_id}")
        start_time = time.time()
        
        # Create output directory: output_dir/llamaparse
        llamaparse_dir = output_dir / "llamaparse"
        llamaparse_dir.mkdir(parents=True, exist_ok=True)
        _log.info(f"Created directory: {llamaparse_dir}")
        
        # Initialize LlamaParse
        llamaparse_api_key=settings.llamaparse_api_key 
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
        
        _log.info(f"LlamaParse extracted {len(documents)} document sections")
        
        jobs_db[job_id]["progress"] = 40
        jobs_db[job_id]["message"] = f"Found {len(documents)} document sections. Processing with OpenAI..."
        
        doc_filename = Path(input_file_path).stem
        all_tables = []
        table_counter = 0
        
        # Process each document section
        for doc_idx, doc in enumerate(documents):
            progress = 40 + int((doc_idx / len(documents)) * 50)
            jobs_db[job_id]["progress"] = progress
            jobs_db[job_id]["message"] = f"Processing section {doc_idx + 1}/{len(documents)} with OpenAI..."
            
            # Extract tables using OpenAI
            html_content = extract_tables_with_openai(doc.text)
            
            if html_content == "NO_TABLES_FOUND":
                _log.info(f"No tables found in document section {doc_idx + 1}")
                continue
            elif html_content == "ERROR_PROCESSING":
                _log.warning(f"Error processing document section {doc_idx + 1}")
                continue
            
            # Split multiple tables if they exist in the response
            # Simple heuristic: split by </table> and look for <table>
            tables_in_section = []
            if "<table" in html_content.lower():
                # Split the content to find individual tables
                parts = html_content.split("</table>")
                for part in parts:
                    if "<table" in part.lower():
                        # Find the start of the table
                        table_start = part.lower().find("<table")
                        if table_start != -1:
                            table_html = part[table_start:] + "</table>"
                            tables_in_section.append(table_html)
            
            if not tables_in_section and "<table" in html_content.lower():
                # If splitting didn't work, treat entire content as one table
                tables_in_section = [html_content]
            
            # Save each table as HTML file
            for table_html in tables_in_section:
                table_counter += 1
                
                # Create styled HTML
                styled_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Table {table_counter} - {doc_filename}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #333;
            border-bottom: 3px solid #667eea;
            padding-bottom: 10px;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
            margin-top: 20px;
        }}
        th {{
            background: #667eea;
            color: white;
            padding: 12px;
            text-align: left;
        }}
        td {{
            border: 1px solid #ddd;
            padding: 10px;
        }}
        tr:nth-child(even) {{
            background-color: #f9f9f9;
        }}
        tr:hover {{
            background-color: #f5f5f5;
        }}
        .stats {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 6px;
            margin-bottom: 20px;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 Table {table_counter}</h1>
        <div class="stats">
            <strong>Document:</strong> {doc_filename}<br>
            <strong>Section:</strong> {doc_idx + 1} | 
            <strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
        </div>
        {table_html}
    </div>
</body>
</html>"""
                
                # Save HTML file
                html_filename = f"{doc_filename}-table-{table_counter}.html"
                html_path = llamaparse_dir / html_filename
                
                with open(html_path, "w", encoding="utf-8") as f:
                    f.write(styled_html)
                
                _log.info(f"Saved HTML table: {html_path}")
                
                # Store table info
                table_info = {
                    "table_id": table_counter,
                    "section": doc_idx + 1,
                    "html_file": str(html_path),
                    "html_content": table_html
                }
                all_tables.append(table_info)
        
        # Save summary file with all tables
        if all_tables:
            summary_html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>All Tables - {doc_filename}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #333;
            border-bottom: 3px solid #667eea;
            padding-bottom: 10px;
        }}
        .table-section {{
            margin: 30px 0;
            padding: 20px;
            border: 1px solid #ddd;
            border-radius: 8px;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
            margin-top: 20px;
        }}
        th {{
            background: #667eea;
            color: white;
            padding: 12px;
            text-align: left;
        }}
        td {{
            border: 1px solid #ddd;
            padding: 10px;
        }}
        tr:nth-child(even) {{
            background-color: #f9f9f9;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>📊 All Tables from {doc_filename}</h1>
        <p><strong>Total Tables Found:</strong> {len(all_tables)}</p>
        <p><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
"""
            
            for table_info in all_tables:
                summary_html += f"""
        <div class="table-section">
            <h2>Table {table_info['table_id']} (Section {table_info['section']})</h2>
            {table_info['html_content']}
        </div>
"""
            
            summary_html += """
    </div>
</body>
</html>"""
            
            summary_path = llamaparse_dir / f"{doc_filename}-all-tables.html"
            with open(summary_path, "w", encoding="utf-8") as f:
                f.write(summary_html)
            
            _log.info(f"Saved summary file: {summary_path}")
        
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
        
        _log.info(f"Extraction completed for job {job_id}: {len(all_tables)} tables in {processing_time:.2f}s")
        return result
        
    except Exception as e:
        jobs_db[job_id]["status"] = "failed"
        jobs_db[job_id]["message"] = f"Processing failed: {str(e)}"
        jobs_db[job_id]["completed_at"] = datetime.now()
        _log.error(f"Extraction failed for job {job_id}: {str(e)}")
        raise

def process_document_background_llamaparse(file_path: str, output_dir: Path, job_id: str, jobs_db, TableInfo, ExtractionResult, _log: logging.Logger):
    """Background task for processing documents with LlamaParse + OpenAI"""
    try:
        result = extract_tables_llamaparse(file_path, output_dir, job_id, jobs_db, TableInfo, ExtractionResult, _log)
        jobs_db[job_id]["result"] = result
    except Exception as e:
        _log.error(f"Background processing failed for job {job_id}: {str(e)}")