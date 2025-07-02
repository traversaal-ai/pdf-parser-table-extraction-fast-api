from pathlib import Path

def validate_file_path(path: str) -> bool:
    """
    Validate that the given path exists and is a file.
    """
    p = Path(path)
    return p.exists() and p.is_file()

def validate_output_dir(path: str) -> bool:
    """
    Validate that the given path is a directory (if it exists).
    """
    p = Path(path)
    return not p.exists() or p.is_dir() 