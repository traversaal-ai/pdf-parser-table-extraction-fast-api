from fastapi import APIRouter, Form, status, HTTPException
from typing import Dict
from pathlib import Path
from app.services.docling_service import extract_tables_from_file as docling_extract_tables_from_file, DOCLING_AVAILABLE
from app.services.llamaparse_service import extract_tables_llamaparse
from app.services.unstructured_service import extract_tables_from_file_unstructured, client as unstructured_client
from app.schemas.extraction import ExtractionResponse, TableInfo, ExtractionResult
import shutil
import uuid
import logging
import os

router = APIRouter(prefix="", tags=["Extraction"])
_log = logging.getLogger(__name__)

SUMMARY_FIELDS = [
    "job_id",
    "status",
    "document_name",
    "processing_time",
    "total_tables",
    "output_directory",
    "message"
]

def filter_summary_fields(result):
    if isinstance(result, dict):
        return {k: v for k, v in result.items() if k in SUMMARY_FIELDS}
    # If it's a Pydantic model, convert to dict first
    if hasattr(result, 'dict'):
        return {k: v for k, v in result.dict().items() if k in SUMMARY_FIELDS}
    return result

@router.post("/extract", status_code=status.HTTP_200_OK)
async def extract(
    input_file_path: str = Form(..., description="Absolute path to the input document on the server"),
    output_dir: str = Form(..., description="Absolute path to the output directory (will be created/freshened)"),
    docling: bool = Form(..., description="Use Docling backend"),
    llamaparse: bool = Form(..., description="Use LlamaParse backend"),
    unstructured: bool = Form(..., description="Use Unstructured backend")
):
    """
    Unified endpoint to extract tables using selected extractors. User provides input file path and output directory.
    Returns extraction results for each selected backend and the job_id.
    """
    job_id = str(uuid.uuid4())
    jobs_db: Dict[str, dict] = {job_id: {}}
    input_path = Path(input_file_path)
    if not input_path.exists() or not input_path.is_file():
        _log.error(f"Input file does not exist: {input_file_path}")
        raise HTTPException(status_code=400, detail="Input file does not exist or is not a file.")

    user_output_dir = Path(output_dir)
    table_outputs_dir = user_output_dir / "table_outputs"
    table_outputs_dir.mkdir(parents=True, exist_ok=True)
    job_output_dir = table_outputs_dir / f"job_{job_id}"
    job_output_dir.mkdir(exist_ok=True)
    for subfolder in ["docling", "llamaparse", "unstructured"]:
        subfolder_path = job_output_dir / subfolder
        if subfolder_path.exists() and subfolder_path.is_dir():
            shutil.rmtree(subfolder_path)

    results = {}
    _log.info(f"Starting extraction job {job_id} for file: {input_file_path}")
    if docling:
        try:
            docling_result = docling_extract_tables_from_file(
                input_file_path, job_output_dir, job_id, jobs_db, TableInfo, ExtractionResult, _log
            )
            results["docling"] = filter_summary_fields(docling_result)
        except Exception as e:
            _log.error(f"Docling extraction failed: {e}")
            results["docling"] = f"Docling extraction failed: {str(e)}"
    if llamaparse:
        try:
            llamaparse_result = extract_tables_llamaparse(
                input_file_path, job_output_dir, job_id, jobs_db, TableInfo, ExtractionResult, _log
            )
            results["llamaparse"] = filter_summary_fields(llamaparse_result)
        except Exception as e:
            _log.error(f"LlamaParse extraction failed: {e}")
            results["llamaparse"] = f"LlamaParse extraction failed: {str(e)}"
    if unstructured:
        try:
            unstructured_result = extract_tables_from_file_unstructured(
                input_file_path, job_output_dir, job_id, jobs_db, TableInfo, ExtractionResult, _log, unstructured_client
            )
            results["unstructured"] = filter_summary_fields(unstructured_result)
        except Exception as e:
            _log.error(f"Unstructured extraction failed: {e}")
            results["unstructured"] = f"Unstructured extraction failed: {str(e)}"
    _log.info(f"Extraction job {job_id} completed.")
    return {"job_id": job_id, "results": results} 