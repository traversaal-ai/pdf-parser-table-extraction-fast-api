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

router = APIRouter(prefix="", tags=["Extraction"])
_log = logging.getLogger(__name__)

@router.post("/extract", response_model=ExtractionResponse, status_code=status.HTTP_200_OK)
async def extract(
    input_file_path: str = Form(..., description="Absolute path to the input document on the server"),
    output_dir: str = Form(..., description="Absolute path to the output directory (will be created/freshened)"),
    docling: bool = Form(..., description="Use Docling backend"),
    llamaparse: bool = Form(..., description="Use LlamaParse backend"),
    unstructured: bool = Form(..., description="Use Unstructured backend")
):
    """
    Unified endpoint to extract tables using selected extractors. User provides input file path and output directory.
    Returns extraction results for each selected backend.
    """
    job_id = str(uuid.uuid4())
    jobs_db: Dict[str, dict] = {job_id: {}}
    input_path = Path(input_file_path)
    if not input_path.exists() or not input_path.is_file():
        _log.error(f"Input file does not exist: {input_file_path}")
        raise HTTPException(status_code=400, detail="Input file does not exist or is not a file.")
    output_path = Path(output_dir)
    if output_path.exists() and not output_path.is_dir():
        _log.error(f"Output path exists and is not a directory: {output_dir}")
        raise HTTPException(status_code=400, detail="Output path exists and is not a directory.")
    if output_path.exists():
        shutil.rmtree(output_path)
    output_path.mkdir(parents=True, exist_ok=True)
    results = {}
    _log.info(f"Starting extraction job {job_id} for file: {input_file_path}")
    if docling:
        try:
            results["docling"] = docling_extract_tables_from_file(
                input_file_path, output_path, job_id, jobs_db, TableInfo, ExtractionResult, _log
            )
        except Exception as e:
            _log.error(f"Docling extraction failed: {e}")
            results["docling"] = f"Docling extraction failed: {str(e)}"
    if llamaparse:
        try:
            results["llamaparse"] = extract_tables_llamaparse(
                input_file_path, output_path, job_id, jobs_db, TableInfo, ExtractionResult, _log
            )
        except Exception as e:
            _log.error(f"LlamaParse extraction failed: {e}")
            results["llamaparse"] = f"LlamaParse extraction failed: {str(e)}"
    if unstructured:
        try:
            results["unstructured"] = extract_tables_from_file_unstructured(
                input_file_path, output_path, job_id, jobs_db, TableInfo, ExtractionResult, _log, unstructured_client
            )
        except Exception as e:
            _log.error(f"Unstructured extraction failed: {e}")
            results["unstructured"] = f"Unstructured extraction failed: {str(e)}"
    _log.info(f"Extraction job {job_id} completed.")
    return {"results": results} 