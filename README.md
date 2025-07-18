# Document Table Extractor API (FastAPI)

This project provides a FastAPI-based API for extracting tables from documents (PDF) using multiple backends (Docling, Llamaparse, Unstructured). It supports saving extracted tables as CSV and HTML files in organized output directories.

## Features
- Extract tables from documents using Docling, Llamaparse, and Unstructured backends
- Save results as CSV and HTML in organized output folders
- Simple `/extract` API endpoint
- Configuration via `.env` file
- **GPU acceleration recommended for Docling for best performance**

## Requirements
- Python 3.11+
- pip
- (Optional) NVIDIA GPU for faster Docling extraction

## Output Organization
A folder named `table_outputs` will be created inside your specified output directory. For each extraction job, a unique subfolder (named with a job ID) is created inside `table_outputs`. All results for that job are stored in this subfolder.

## Installation
1. **Clone the repository:**
   ```sh
   git clone https://github.com/traversaal-ai/pdf-parser-table-extraction-fast-api.git
   cd get-tables-fastapi
   ```
2. **Create and activate a virtual environment:**
   ```sh
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On Unix/Mac:
   source venv/bin/activate
   ```
3. **Install dependencies:**
   ```sh
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

## Configuration
Create a `.env` file in the project root with your API keys and endpoints:

```
llamaparse_api_key=your_llamaparse_key_here
unstructured_api_key=your_unstructured_key_here
openai_api_key=your_openai_api_key_here
```

## Running the API
Start the FastAPI server with Uvicorn:

```sh
uvicorn main:app --reload
```

The API will be available at [http://localhost:8000/docs](http://localhost:8000/docs)

## API Usage
### `/extract` Endpoint
Extract tables from a document using one or more backends.

**POST** `/extract`

#### Form Data Parameters
- `input_file_path` (str): Absolute path to the input document on the server
- `output_dir` (str): Absolute path to the output directory (will be created/freshened)
- `docling` (bool): Use Docling backend (`true`/`false`)
- `llamaparse` (bool): Use Llamaparse backend (`true`/`false`)
- `unstructured` (bool): Use Unstructured backend (`true`/`false`)

#### Example `curl` Request
```sh
curl -X POST http://localhost:8000/extract \
  -F "input_file_path=/absolute/path/to/input.pdf" \
  -F "output_dir=/absolute/path/to/output" \
  -F "docling=true" \
  -F "llamaparse=false" \
  -F "unstructured=true"
```

#### Response
Returns a JSON object with the extraction results for each backend.

```
{
  "results": {
    "docling": { ... },
    "llamaparse": { ... },
    "unstructured": { ... }
  }
}
```

## Output Structure
- All output files are saved in subdirectories of the provided `output_dir` (e.g., `output_dir/docling/`, `output_dir/unstructured/`).
- Each backend saves its own results in its respective folder.

## Notes
- The input file must exist on the server at the specified path.
- LlamaParse backend is currently a placeholder.
- **For best performance with Docling, use a machine with an NVIDIA GPU.**

## License
MIT


## 📊 Evaluation: Table Extraction Quality
We evaluated all three extraction tools across three fundamental criteria:

### Criteria	
Completeness: Are all data values captured from the table?

Accuracy: Are the extracted values correct?

Structure: Is the layout (rows/columns) preserved correctly?

### 📈 Performance Snapshot
| Tool         | Completeness | Accuracy | Structure | Average Score |
|--------------|--------------|----------|-----------|----------------|
| **Docling**      | 90.5%        | 94.9%    | 63.1%     | **82.8**        |
| **Unstructured** | 53.1%        | 51.5%    | 64.2%     | **56.3**        |
| **LlamaParse**   | 96.9%        | 62.0%    | 80.4%     | **79.8**        |


Docling offers the best balance, while LlamaParse captures nearly all tables but with some accuracy trade-offs.

### Visual Comparison
<img width="500" height="500" alt="Extraction Quality Graph" src="https://github.com/user-attachments/assets/1e4e800d-1ec5-48a1-adc4-9d9280092650" />


🎥 Video Demo


https://github.com/user-attachments/assets/59390b4e-2567-40ef-83f6-f0106d5c978e



A visual walkthrough showing how different tools perform table extraction on sample documents.






