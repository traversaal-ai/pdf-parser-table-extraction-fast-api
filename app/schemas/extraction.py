from typing import List, Optional, Dict
from pydantic import BaseModel

class TableInfo(BaseModel):
    """Information about an extracted table."""
    table_index: int
    csv_path: str
    html_path: str
    rows: int
    columns: int
    filename_csv: str
    filename_html: str

class ExtractionResult(BaseModel):
    """Result of a table extraction job."""
    job_id: str
    status: str
    document_name: str
    processing_time: Optional[float] = None
    total_tables: int
    tables: List[TableInfo] = []
    output_directory: str
    message: str

class ExtractionResponse(BaseModel):
    """Response model for the /extract endpoint."""
    results: Dict[str, object] 