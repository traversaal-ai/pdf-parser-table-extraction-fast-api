# import os
# import time
# import pandas as pd
# from pathlib import Path
# from datetime import datetime
# import logging
# from bs4 import BeautifulSoup
# from llama_parse import LlamaParse
# from openai import OpenAI
# from app.core.config import settings

# # Initialize OpenAI client
# openai_client = OpenAI(api_key=settings.openai_api_key)

# def extract_tables_from_file_llamaparse(input_file_path: str, output_dir: Path, job_id: str, jobs_db, TableInfo, ExtractionResult, _log: logging.Logger) -> object:
#     """
#     Extract tables from document using LlamaParse and OpenAI, then save as HTML/Excel
#     """
#     try:
#         jobs_db[job_id]["status"] = "processing"
#         jobs_db[job_id]["progress"] = 10
#         jobs_db[job_id]["message"] = "Initializing LlamaParse..."
#         _log.info(f"Starting extraction for job {job_id}")
#         start_time = time.time()
        
#         # Create single output directory: output_dir/llamaparse
#         llamaparse_dir = output_dir / "llamaparse"
#         llamaparse_dir.mkdir(parents=True, exist_ok=True)
#         _log.info(f"Created directory: {llamaparse_dir}")
        
#         jobs_db[job_id]["progress"] = 20
#         jobs_db[job_id]["message"] = "Processing document with LlamaParse..."
        
#         # Initialize LlamaParse
#         llamaparse_api_key = "llx-jPEgiT8HG6Ly2KUOpmSIBT5x6WF4k0cXQQVY4Yre7WzRKEYj"
#         parser = LlamaParse(
#             api_key=llamaparse_api_key,
#             result_type="markdown",
#             extract_charts=True,
#             auto_mode=True,
#             auto_mode_trigger_on_image_in_page=True,
#             auto_mode_trigger_on_table_in_page=True,
#         )
        
#         # Extract text using LlamaParse
#         file_name = os.path.basename(input_file_path)
#         extra_info = {"file_name": file_name}
        
#         with open(input_file_path, "rb") as f:
#             documents = parser.load_data(f, extra_info=extra_info)
        
#         # Combine all document text
#         full_text = ""
#         for doc in documents:
#             full_text += doc.text + "\n\n"
        
#         jobs_db[job_id]["progress"] = 40
#         jobs_db[job_id]["message"] = "Analyzing text with OpenAI to extract tables..."
        
#         # Use OpenAI to extract tables from the text
#         response = openai_client.chat.completions.create(
#             model="gpt-4o",
#             messages=[
#                 {
#                     "role": "system",
#                     "content": """You are a table extraction expert. Analyze the provided text and extract all tables you find. 
#                     For each table:
#                     1. Convert it to proper HTML table format with <table>, <thead>, <tbody>, <tr>, <th>, and <td> tags
#                     2. Ensure the HTML is well-formed and properly structured
#                     3. Include a brief description of what the table contains
#                     4. If you find multiple tables, separate them clearly
                    
#                     Return your response in the following JSON format:
#                     {
#                         "tables": [
#                             {
#                                 "description": "Brief description of the table",
#                                 "html": "Complete HTML table code",
#                                 "page_reference": "Page or section reference if available"
#                             }
#                         ]
#                     }
                    
#                     If no tables are found, return: {"tables": []}"""
#                 },
#                 {
#                     "role": "user",
#                     "content": f"Please extract all tables from the following text:\n\n{full_text}"
#                 }
#             ],
#             temperature=0.1
#         )
        
#         jobs_db[job_id]["progress"] = 60
#         jobs_db[job_id]["message"] = "Processing extracted tables..."
        
#         # Parse OpenAI response
#         import json
#         try:
#             ai_response = json.loads(response.choices[0].message.content)
#             extracted_tables = ai_response.get("tables", [])
#         except json.JSONDecodeError:
#             _log.error("Failed to parse OpenAI response as JSON")
#             extracted_tables = []
        
#         doc_filename = Path(input_file_path).stem
#         tables_info = []
#         total_tables = len(extracted_tables)
        
#         jobs_db[job_id]["progress"] = 70
#         jobs_db[job_id]["message"] = f"Found {total_tables} tables. Converting to files..."
        
#         excel_files = []
#         combined_excel_path = None
#         if total_tables > 0:
#             combined_excel_path = llamaparse_dir / f"{doc_filename}_combined_tables.xlsx"
        
#         for table_ix, table_data in enumerate(extracted_tables):
#             progress = 70 + int((table_ix / total_tables) * 25) if total_tables > 0 else 95
#             jobs_db[job_id]["progress"] = progress
#             jobs_db[job_id]["message"] = f"Processing table {table_ix + 1}/{total_tables}..."
            
#             table_html = table_data.get('html', '')
#             table_description = table_data.get('description', f'Table {table_ix + 1}')
#             page_reference = table_data.get('page_reference', 'Unknown')
            
#             if not table_html:
#                 _log.warning(f"Table {table_ix + 1} has no HTML content, skipping...")
#                 continue
            
#             # Save HTML file directly in llamaparse_dir
#             html_filename = f"{doc_filename}-table-{table_ix + 1}.html"
#             element_html_path = llamaparse_dir / html_filename
            
#             styled_html = f"""<!DOCTYPE html>
# <html lang="en">
# <head>
#     <meta charset="UTF-8">
#     <meta name="viewport" content="width=device-width, initial-scale=1.0">
#     <title>Table {table_ix + 1} - {doc_filename}</title>
#     <style>
#         body {{
#             font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
#             margin: 20px;
#             background-color: #f5f5f5;
#         }}
#         .container {{
#             max-width: 1200px;
#             margin: 0 auto;
#             background: white;
#             padding: 20px;
#             border-radius: 8px;
#             box-shadow: 0 2px 10px rgba(0,0,0,0.1);
#         }}
#         h1 {{
#             color: #333;
#             border-bottom: 3px solid #667eea;
#             padding-bottom: 10px;
#         }}
#         table {{
#             border-collapse: collapse;
#             width: 100%;
#             margin-top: 20px;
#         }}
#         th {{
#             background: #667eea;
#             color: white;
#             padding: 12px;
#             text-align: left;
#         }}
#         td {{
#             border: 1px solid #ddd;
#             padding: 10px;
#         }}
#         tr:nth-child(even) {{
#             background-color: #f9f9f9;
#         }}
#         tr:hover {{
#             background-color: #f5f5f5;
#         }}
#         .stats {{
#             background: #f8f9fa;
#             padding: 15px;
#             border-radius: 6px;
#             margin-bottom: 20px;
#         }}
#         .description {{
#             background: #e3f2fd;
#             padding: 15px;
#             border-radius: 6px;
#             margin-bottom: 20px;
#             border-left: 4px solid #2196f3;
#         }}
#     </style>
# </head>
# <body>
#     <div class="container">
#         <h1>📊 Table {table_ix + 1}</h1>
#         <div class="stats">
#             <strong>Document:</strong> {doc_filename}<br>
#             <strong>Page/Section:</strong> {page_reference} | 
#             <strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
#         </div>
#         <div class="description">
#             <strong>Description:</strong> {table_description}
#         </div>
#         {table_html}
#     </div>
# </body>
# </html>"""
            
#             with open(element_html_path, "w", encoding="utf-8") as fp:
#                 fp.write(styled_html)
#             _log.info(f"Saved HTML: {element_html_path}")
            
#             # Convert to DataFrame and Excel
#             try:
#                 df_list = pd.read_html(table_html)
#                 if df_list:
#                     table_df = df_list[0]
#                     if isinstance(table_df.columns, pd.MultiIndex):
#                         table_df.columns = [' '.join(map(str, col)).strip() for col in table_df.columns.values]
                    
#                     # Save Excel file directly in llamaparse_dir
#                     excel_filename = f"{doc_filename}-table-{table_ix + 1}.xlsx"
#                     element_excel_path = llamaparse_dir / excel_filename
#                     table_df.to_excel(element_excel_path, index=False)
#                     excel_files.append(element_excel_path)
#                     _log.info(f"Saved Excel: {element_excel_path}")
                    
#                     # Add to tables_info
#                     tables_info.append({
#                         "table_index": table_ix + 1,
#                         "description": table_description,
#                         "page_reference": page_reference,
#                         "html_file": str(element_html_path),
#                         "excel_file": str(element_excel_path),
#                         "rows": len(table_df),
#                         "columns": len(table_df.columns)
#                     })
                    
#             except Exception as e:
#                 _log.warning(f"Failed to convert HTML to Excel for table {table_ix + 1}: {str(e)}")
#                 continue
        
#         # Combine all tables into a single Excel file
#         if combined_excel_path and excel_files:
#             try:
#                 with pd.ExcelWriter(combined_excel_path) as writer:
#                     for idx, excel_file in enumerate(excel_files):
#                         df = pd.read_excel(excel_file)
#                         sheet_name = f"Table_{idx+1}"
#                         df.to_excel(writer, sheet_name=sheet_name, index=False)
#                 _log.info(f"Saved combined Excel: {combined_excel_path}")
#             except Exception as e:
#                 _log.warning(f"Failed to create combined Excel file: {str(e)}")
        
#         # Save the original markdown output
#         markdown_path = llamaparse_dir / f"{doc_filename}_original.md"
#         with open(markdown_path, "w", encoding="utf-8") as f:
#             f.write(full_text)
#         _log.info(f"Saved original markdown: {markdown_path}")
        
#         processing_time = time.time() - start_time
#         jobs_db[job_id]["status"] = "completed"
#         jobs_db[job_id]["progress"] = 100
#         jobs_db[job_id]["message"] = "Processing completed successfully!"
#         jobs_db[job_id]["completed_at"] = datetime.now()
        
#         result = ExtractionResult(
#             job_id=job_id,
#             status="completed",
#             document_name=doc_filename,
#             processing_time=processing_time,
#             total_tables=len(extracted_tables),
#             tables=tables_info,
#             output_directory=str(llamaparse_dir.absolute()),
#             message=f"Successfully extracted {len(extracted_tables)} tables in {processing_time:.2f} seconds"
#         )
        
#         _log.info(f"Extraction completed for job {job_id}: {len(extracted_tables)} tables in {processing_time:.2f}s")
#         return result
        
#     except Exception as e:
#         jobs_db[job_id]["status"] = "failed"
#         jobs_db[job_id]["message"] = f"Processing failed: {str(e)}"
#         jobs_db[job_id]["completed_at"] = datetime.now()
#         _log.error(f"Extraction failed for job {job_id}: {str(e)}")
#         raise

# def process_document_background_llamaparse(file_path: str, output_dir: Path, job_id: str, jobs_db, TableInfo, ExtractionResult, _log: logging.Logger):
#     """Background task for processing documents with LlamaParse and OpenAI"""
#     try:
#         result = extract_tables_from_file_llamaparse(file_path, output_dir, job_id, jobs_db, TableInfo, ExtractionResult, _log)
#         jobs_db[job_id]["result"] = result
#     except Exception as e:
#         _log.error(f"Background processing failed for job {job_id}: {str(e)}")



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