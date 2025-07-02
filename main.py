from fastapi import FastAPI, HTTPException, Form
import logging
from pathlib import Path
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel
from app.services.docling_service import extract_tables_from_file as docling_extract_tables_from_file, DOCLING_AVAILABLE
from app.services.llamaparse_service import extract_tables_llamaparse
from app.services.unstructured_service import extract_tables_from_file_unstructured, client as unstructured_client
import shutil

logging.basicConfig(level=logging.INFO)
_log = logging.getLogger(__name__)

app = FastAPI(
    title="Document Table Extractor API",
    description="Extract tables from documents and export to CSV/HTML formats",
    version="1.0.0"
)

class TableInfo(BaseModel):
    table_index: int
    csv_path: str
    html_path: str
    rows: int
    columns: int
    filename_csv: str
    filename_html: str

class ExtractionResult(BaseModel):
    job_id: str
    status: str
    document_name: str
    processing_time: Optional[float] = None
    total_tables: int
    tables: List[TableInfo] = []
    output_directory: str
    message: str

@app.post("/extract")
async def extract(
    input_file_path: str = Form(...),
    output_dir: str = Form(...),
    docling: bool = Form(...),
    llamaparse: bool = Form(...),
    unstructured: bool = Form(...)
):
    """
    Unified endpoint to extract tables using selected extractors. User provides input file path and output directory.
    """
    # Ensure output_dir is fresh
    output_path = Path(output_dir)
    if output_path.exists():
        shutil.rmtree(output_path)
    output_path.mkdir(parents=True, exist_ok=True)
    results = {}
    job_id = "job-id"
    jobs_db = {job_id: {}}

    if docling:
        try:
            results["docling"] = docling_extract_tables_from_file(
                input_file_path, output_path, job_id, jobs_db, TableInfo, ExtractionResult, _log
            )
        except Exception as e:
            results["docling"] = f"Docling extraction failed: {str(e)}"
    if llamaparse:
        try:
            results["llamaparse"] = extract_tables_llamaparse(
                input_file_path, output_path, job_id, jobs_db, TableInfo, ExtractionResult, _log
            )
        except Exception as e:
            results["llamaparse"] = f"Llamaparse extraction failed: {str(e)}"
    if unstructured:
        try:
            results["unstructured"] = extract_tables_from_file_unstructured(
                input_file_path, output_path, job_id, jobs_db, TableInfo, ExtractionResult, _log, unstructured_client
            )
        except Exception as e:
            results["unstructured"] = f"Unstructured extraction failed: {str(e)}"
    return {"results": results}
